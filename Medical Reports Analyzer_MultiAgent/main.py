from typing import List, Dict
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Read prompts from files
def read_prompt(filename: str) -> str:
    with open(os.path.join("prompts", filename), "r") as f:
        return f.read()

EXTRACTION_PROMPT = read_prompt("extraction_prompt.txt")
CLASSIFICATION_PROMPT = read_prompt("classification_prompt.txt")
ANALYSIS_PROMPT = read_prompt("analysis_prompt.txt")

# Define agents
# Extraction Agent
extraction_agent = Agent(
    role="Medical Data Extractor",
    goal="Extract key medical data from the provided health report following the specified JSON structure.",
    backstory=(
        f"You are an expert in extracting structured information from unstructured medical reports. "
        f"You strictly adhere to the following guidelines for JSON structure:\n{EXTRACTION_PROMPT}"
    ),
    verbose=True,
    allow_delegation=False,
    tools=[]
)

# Classification Agent
classification_agent = Agent(
    role="Medical Systems Classifier",
    goal="Classify extracted findings into body systems and assign severity levels.",
    backstory=(
        f"You are skilled at classifying medical data into body systems and determining severity levels. "
        f"Your output must strictly follow this classification structure:\n{CLASSIFICATION_PROMPT}"
    ),
    verbose=True,
    allow_delegation=False,
    tools=[]
)

# Analysis Agent
analysis_agent = Agent(
    role="Medical Report Analyzer",
    goal="Analyze classified findings and provide actionable recommendations.",
    backstory=(
        f"You are responsible for interpreting classified medical data and creating a comprehensive analysis report. "
        f"Your output must follow the guidelines in this prompt:\n{ANALYSIS_PROMPT}"
    ),
    verbose=True,
    allow_delegation=False,
    tools=[]
)



def analyze_report(content: str) -> Dict:
    """Function to analyze a health report using the multi-agent system."""
    try:
        print(f"Received content to analyze: {content[:200]}...")  # Debug print

        # Check if the content is valid
        if not content or len(content.strip()) == 0:
            return {"error": "Please provide a medical test report to analyze."}

        # Task 1: Extraction
        extraction_task = Task(
            description=(
                f"{EXTRACTION_PROMPT}\n\n"
                "REPORT CONTENT:\n"
                f"{content}\n\n"
                "Your task:\n"
                "1. Extract any available test names, values, reference ranges, abnormal findings, and recommendations.\n"
                "2. Adhere strictly to the JSON structure defined in the extraction guidelines.\n"
                "3. Use empty strings, null, or 0 for missing data.\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "1. The output MUST be a valid JSON object.\n"
                "2. Do NOT include any text outside the JSON object."
            ),
            agent=extraction_agent,
            output_json=True  # Ensure JSON output
        )

        # Task 2: Classification
        classification_task = Task(
            description=(
                f"{CLASSIFICATION_PROMPT}\n\n"
                "Your task:\n"
                "1. Use the extracted data to identify affected body systems.\n"
                "2. Determine severity levels and cross-system impacts.\n"
                "3. Follow the classification structure exactly.\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "1. The output MUST be a valid JSON object.\n"
                "2. Do NOT include any text outside the JSON object."
            ),
            agent=classification_agent,
            output_json=True  # Ensure JSON output
        )

        # Task 3: Analysis
        analysis_task = Task(
            description=(
                f"{ANALYSIS_PROMPT}\n\n"
                "CLASSIFIED DATA:\n"
                "{classification_task.output}\n\n"
                "Your task:\n"
                "1. Use the classified data JSON to generate a comprehensive report.\n"
                "2. Pay special attention to test results affecting multiple systems.\n"
                "3. Follow the exact format specified in the prompt.\n"
                "4. Ensure all recommendations are based on actual findings.\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "1. Only include cross-system impacts for tests affecting multiple systems.\n"
                "2. Sort systems by severity (high → medium → low).\n"
                "3. Use markdown formatting for better readability.\n"
                "4. All recommendations must be tied to specific test results."
            ),
            agent=analysis_agent
        )

        # Create crew
        crew = Crew(
            agents=[extraction_agent, classification_agent, analysis_agent],
            tasks=[extraction_task, classification_task, analysis_task],
            verbose=True,
            process=Process.sequential  # Ensure sequential processing
        )

        # Execute the analysis
        result = crew.kickoff()
        
        # Debug print
        print("Raw crew result:", result)
        
        # Handle different result formats
        if isinstance(result, str):
            try:
                # Try to parse if it's a JSON string
                import json
                result = json.loads(result)
            except json.JSONDecodeError:
                # If it's not JSON, wrap it in a dict
                result = {"analysis": result}
        elif not isinstance(result, dict):
            # If result is neither string nor dict, wrap it
            result = {"analysis": str(result)}
            
        # Ensure we have a valid dictionary
        if not isinstance(result, dict):
            return {"error": "Unexpected result format", "raw_result": str(result)}
            
        # Add status field
        result["status"] = "success"
        
        print("Processed result:", result)  # Debug print
        return result

    except Exception as e:
        print(f"Error in analyze_report: {str(e)}")  # Debug print
        return {"error": str(e), "status": "error"}
