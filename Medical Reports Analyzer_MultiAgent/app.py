import streamlit as st
import tempfile
import shutil
import os
from dotenv import load_dotenv
import openai
import pdfplumber
import requests
import docx
from io import BytesIO
from main import analyze_report

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def read_docx(file_bytes):
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def read_file_content(uploaded_file):
    """Read content from different file types"""
    try:
        # Get file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Copy the uploaded file to the temporary file
            shutil.copyfileobj(uploaded_file, temp_file)
            
            # Process based on file type
            if file_extension == '.pdf':
                with pdfplumber.open(temp_file.name) as pdf:
                    content = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                    if not content:
                        raise ValueError("Could not extract text from PDF. Please check if the PDF contains readable text.")
            elif file_extension == '.txt':
                # Reset file pointer
                uploaded_file.seek(0)
                # Read text content directly from the uploaded file
                content = uploaded_file.read().decode('utf-8')
                if not content.strip():
                    raise ValueError("Text file is empty")
            elif file_extension == '.docx':
                content = read_docx(uploaded_file.read())
                if not content.strip():
                    raise ValueError("Could not extract text from DOCX file")
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            return content
            
    except UnicodeDecodeError:
        try:
            # Try different encoding if UTF-8 fails
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('latin-1')
            if not content.strip():
                raise ValueError("File is empty")
            return content
        except Exception as e:
            raise ValueError(f"Error reading file with alternative encoding: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")
    finally:
        # Clean up temporary file
        if 'temp_file' in locals():
            os.unlink(temp_file.name)

def main():
    st.title("Health Report Analyzer")
    st.write("Upload your medical document for analysis")

    # File uploader
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])

    if uploaded_file is not None:
        try:
            # Read file content
            content = read_file_content(uploaded_file)
            
            # Debug: Print content type and length
            print(f"Content type: {type(content)}")
            print(f"Content length: {len(content) if content else 0}")
            
            # Show analysis button
            if st.button("Analyze Document"):
                with st.spinner("Analyzing document..."):
                    # Debug: Show content being analyzed
                    st.text("Document Content Preview:")
                    st.text_area("Content", content[:500] + "..." if len(content) > 500 else content, height=200)
                    
                    if not content or len(content.strip()) == 0:
                        st.error("No content found in the document. Please check if the file is readable.")
                        st.stop()
                    
                    # Analyze the document using multi-agent system
                    analysis = analyze_report(content)
                    
                    if analysis:
                        if "error" in analysis:
                            st.error(f"Analysis Error: {analysis['error']}")
                            if "raw_result" in analysis:
                                st.text("Raw Result for Debugging:")
                                st.code(analysis["raw_result"])
                        else:
                            # Display results in sections
                            st.subheader("Analysis Results")
                            
                            # Display each section of the analysis
                            if "extraction" in analysis:
                                st.subheader("Extracted Data")
                                st.json(analysis["extraction"])
                            
                            if "classification" in analysis:
                                st.subheader("Classification Results")
                                st.json(analysis["classification"])
                            
                            if "analysis" in analysis:
                                st.subheader("Analysis and Recommendations")
                                # Display analysis as markdown instead of JSON
                                st.markdown(analysis["analysis"])
                            
                            # Display any other sections
                            for key, value in analysis.items():
                                if key not in ["extraction", "classification", "analysis", "status"]:
                                    st.subheader(key.title())
                                    try:
                                        if isinstance(value, (dict, list)):
                                            st.json(value)
                                        else:
                                            st.markdown(str(value))
                                    except:
                                        st.text(str(value))
                            
                            # Add download button for raw output
                            st.download_button(
                                label="Download Full Analysis",
                                data=str(analysis),
                                file_name="analysis_report.txt",
                                mime="text/plain"
                            )
                    else:
                        st.error("No analysis results were generated. Please check if the document contains medical test results.")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            print(f"Detailed error: {str(e)}")  # Debug print
        finally:
            # Clean up any temporary files
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

if __name__ == "__main__":
    main()
