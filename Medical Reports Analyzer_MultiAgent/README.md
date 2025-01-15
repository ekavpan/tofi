# Medical Report Analyzer

A multi-agent AI system that analyzes medical test reports and provides comprehensive health insights.

## Features

- **Document Processing**: Supports multiple formats (PDF, TXT, DOCX)
- **Intelligent Analysis**: Uses multiple AI agents for:
  - Data Extraction
  - System Classification
  - Comprehensive Analysis
- **Detailed Reports**: Generates structured reports including:
  - Cross-system impacts
  - System-wise analysis
  - Action plans
  - Recommendations

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd medical-analyzer-multiagent
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Upload a medical report (supported formats: PDF, TXT, DOCX)

3. Click "Analyze Document" to process the report

4. View the analysis results:
   - Extracted Data
   - Classification Results
   - Analysis and Recommendations

## Project Structure

```
medical-analyzer-multiagent/
├── app.py              # Streamlit web interface
├── main.py            # Core analysis logic and agent definitions
├── prompts/           # AI agent prompts
│   ├── extraction_prompt.txt
│   ├── classification_prompt.txt
│   └── analysis_prompt.txt
├── requirements.txt   # Project dependencies
└── README.md         # Project documentation
```

## Dependencies

- Python 3.8+
- OpenAI API
- Streamlit
- CrewAI
- PDFPlumber
- python-docx
- Other dependencies listed in requirements.txt

## How It Works

1. **Document Processing**:
   - Uploads and extracts text from various document formats
   - Preprocesses text for analysis

2. **Multi-Agent Analysis**:
   - Extraction Agent: Converts raw text to structured data
   - Classification Agent: Categorizes findings by body system
   - Analysis Agent: Generates comprehensive report

3. **Report Generation**:
   - Creates structured analysis with multiple sections
   - Provides actionable recommendations
   - Includes follow-up timeline


## Output Screens
![image](https://github.com/user-attachments/assets/0c46fb32-3aa4-4fff-936f-a55a1c150b45)
![image](https://github.com/user-attachments/assets/c3aba139-9207-4787-b8ef-97d7c531dfa5)




