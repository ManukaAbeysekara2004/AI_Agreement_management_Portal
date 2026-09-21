import time
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import ollama
from pypdf import PdfReader
import io
from typing import Optional, List, Dict, Any

# Create the FastAPI app (this acts as our main web server)
app = FastAPI(title="PDF Agreement Extraction API", version="1.0")

# This is the exact shape (schema) of the data we want the AI to give us back.
# It tells the AI exactly what fields to look for (like title, dates) and how to format them.
JSON_SCHEMA = """
{
  "schema_version": "1.0",
  "document_classification": { "is_agreement": true, "confidence": 0.98 },
  "fields": {
    "agreement_number": {
      "value": "string or null",
      "confidence": "number between 0 and 1",
      "source": "explicit or inferred",
      "evidence": { "page": "number", "text": "string of the excerpt" }
    },
    "title": {
      "value": "string or null",
      "confidence": "number",
      "source": "string",
      "evidence": { "page": "number", "text": "string" }
    },
    "vendor_customer": {
      "value": "string or null",
      "confidence": "number",
      "source": "string",
      "evidence": { "page": "number", "text": "string" }
    },
    "start_date": {
      "value": "YYYY-MM-DD or null",
      "confidence": "number",
      "source": "string",
      "evidence": { "page": "number", "text": "string" }
    },
    "expiry_date": {
      "value": "YYYY-MM-DD or null",
      "confidence": "number",
      "source": "string",
      "evidence": { "page": "number", "text": "string" }
    },
    "value": {
      "value": { "amount": "string number", "currency": "string" },
      "confidence": "number",
      "source": "string",
      "evidence": { "page": "number", "text": "string" }
    }
  },
  "warnings": [
    { "code": "string", "field": "string or null", "message": "string" }
  ],
  "document": { "page_count": "number", "ocr_applied": false, "language": "string" }
}
"""

# Helper function to read a PDF file and turn it into plain text
def extract_text_from_pdf(file_bytes: bytes):
    # Open the PDF file using the raw bytes uploaded by the user
    reader = PdfReader(io.BytesIO(file_bytes))
    text_content = []
    
    # Count how many pages are in the PDF
    page_count = len(reader.pages)
    
    # Go through the PDF page by page
    for page_num in range(page_count):
        page = reader.pages[page_num]
        
        # Extract the actual text from the current page
        text = page.extract_text()
        if text:
            # Add the text to our list, marking which page it came from.
            # We add 1 to the page number so humans (and the AI) see "Page 1" instead of "Page 0".
            text_content.append(f"--- PAGE {page_num + 1} ---\n{text}\n")
    
    # Combine all the individual pages into one giant string of text, separated by line breaks
    full_text = "\n".join(text_content)
    
    # Return both the giant text string and the total number of pages
    return full_text, page_count

# Create a web endpoint at "/extract" that accepts file uploads
@app.post("/extract")
async def extract_information(file: UploadFile = File(...)):
    # Check if the uploaded file is actually a PDF. If not, stop and return an error.
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Start a timer to see how long the extraction takes
    start_time = time.time()
    
    try:
        # Read the raw contents of the uploaded file
        content = await file.read()
        
        # Use our helper function above to get the text and page count
        extracted_text, page_count = extract_text_from_pdf(content)
        
        # If we couldn't find any text (for example, if it's an image-only scanned PDF), stop here.
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF. It might be scanned or empty.")
            
        # Build the exact instructions (prompt) to send to the AI.
        # This includes our instructions, the JSON schema we want, and the actual PDF text.
        prompt = f"""
        You are an expert contract analysis AI.
        Please analyze the following document text and extract the required fields.
        Return the result strictly as a JSON object matching the schema below.
        Do NOT wrap the JSON in markdown code blocks. Just output raw JSON.
        Note: OCR is not applied in this pipeline, so always set "ocr_applied" to false.

        Required JSON Schema:
        {JSON_SCHEMA}

        Document Text:
        {extracted_text}
        """

        # Send our instructions and text to the local AI model (Ollama)
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful API that strictly outputs valid JSON. Never include explanations.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            format='json',
            options={
                # Temperature 0.1 keeps the AI focused and factual, preventing it from making things up
                'temperature': 0.1
            }
        )

        # Get the AI's text answer from the response
        llm_output = response['message']['content']
        
        try:
            # Try to convert the AI's text answer into a proper Python dictionary (JSON data)
            parsed_json = json.loads(llm_output)
        except json.JSONDecodeError:
            # If the AI messed up and didn't give us valid JSON, print it to the console for debugging
            print("Failed to parse LLM output as JSON:")
            print(llm_output)
            # Send an error back to the user
            raise HTTPException(status_code=500, detail="LLM did not return valid JSON.")

        # Stop the timer and calculate how many milliseconds it took to process
        end_time = time.time()
        processing_ms = int((end_time - start_time) * 1000)
        
        # Add some extra helpful info to the final JSON result before returning it
        parsed_json['model'] = { "name": "llama3.1:8b", "version": "latest" }
        parsed_json['processing_ms'] = processing_ms
        
        # Make sure the 'document' section exists, then add the total page count to it
        if 'document' not in parsed_json:
            parsed_json['document'] = {}
        parsed_json['document']['page_count'] = page_count
        
        # Send the final extracted data back to whoever requested it
        return parsed_json
        
    except Exception as e:
        # If anything else goes wrong, catch the error and return a generic server error
        raise HTTPException(status_code=500, detail=str(e))

# This block actually starts the web server when you run 'python main.py' in the terminal
if __name__ == "__main__":
    import uvicorn
    # Starts the server on localhost port 8000. 'reload=True' means it will restart if you change the code.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
