# Medical Report Analyzer-Impacted Body System Classification

A Streamlit-based application that analyzes medical reports (PDF, images) using LLM to identify abnormal values and their clinical significance.

## Features

- Upload and analyze medical reports in PDF or image format
- Extract test values using OCR and text extraction
- LLM-based analysis of test results
- Identification of impacted body systems
- Recommendations for further tests
- Detailed clinical significance analysis

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Install Tesseract OCR:
- Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract installation directory to system PATH

## Running the App

```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `analyzer.py`: Core analysis logic and LLM integration
- `text_extractor.py`: PDF and image text extraction utilities
- `prompts/`: LLM prompt templates
- `utils/`: Helper functions and utilities

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `TESSERACT_PATH`: Path to Tesseract OCR installation (optional)

## Output Screen
![image](https://github.com/user-attachments/assets/624be38e-c4f0-4e00-adf1-871fc75887e5)
![image](https://github.com/user-attachments/assets/63ac17f4-020f-4459-90aa-88daa7078a3c)

