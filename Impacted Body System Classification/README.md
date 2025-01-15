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

## Output Screens
![image](https://github.com/user-attachments/assets/ee8f0ec5-5d37-482e-bb0f-654c97e853d5) ![image](https://github.com/user-attachments/assets/60179651-37ca-46e4-8396-1990c1d07425)
![image](https://github.com/user-attachments/assets/58c1db01-d68b-4394-8a97-254eb30d1880) ![image](https://github.com/user-attachments/assets/5d91d40e-889b-4402-b7eb-d1d600522f1e)




