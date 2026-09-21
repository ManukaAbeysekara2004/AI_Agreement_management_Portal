# AI PDF Agreement Extractor

This is a simple tool that reads PDF agreements (like contracts) and uses AI to automatically find and extract important information like the title, dates, vendor names, and values.

## What you need to run this

Before you start, make sure you have these installed on your computer:
1. **Python** (version 3.8 or newer)
2. **Ollama**: This is the engine that runs the AI on your computer. Download it from [ollama.com](https://ollama.com/) and install it.
3. Once Ollama is installed, open your command prompt or terminal and run this command to download the AI model we need:
   ```bash
   ollama pull llama3.1:8b
   ```

## How to set up and run the project

Follow these simple steps to get the project running on your PC:

**Step 1: Download the code**
Clone this repository to your computer and go into the folder:
```bash
git clone <your-repository-url>
cd Prototype
```

**Step 2: Create a virtual environment**
This creates a clean, separate space for the project so it doesn't mess with other Python projects on your computer.
```bash
python -m venv venv
```

**Step 3: Activate the virtual environment**
You need to turn the virtual environment "on".
- **On Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **On Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```
*(You will know it worked if you see `(venv)` at the beginning of your command line.)*

**Step 4: Install the required tools**
Now, install the Python packages this project needs to work:
```bash
pip install -r requirements.txt
```

**Step 5: Start the server**
Finally, run the code to start the web server:
```bash
python main.py
```

## How to use it

Once the server is running, the AI is ready to accept PDF files!

1. Open your web browser and go to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
2. This will open a simple, interactive page (Swagger UI) where you can test the API.
3. Click on the green `POST /extract` box.
4. Click the "Try it out" button on the right.
5. Click "Choose File" and select a PDF agreement from your computer.
6. Click the big blue "Execute" button.
7. Scroll down to see the final extracted data (it will look like a structured list called JSON).
