import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from text_extractor import TextExtractor
from analyzer import MedicalAnalyzer

def display_analysis_results(analysis):
    """Display analysis results in a structured format"""
    st.write("### Analysis Results")

    # Display cross-system impacts first
    if 'cross_system_impacts' in analysis.get('summary', {}):
        st.write("#### Cross-System Impacts")
        for impact in analysis['summary']['cross_system_impacts']:
            with st.expander(f"{impact['condition']}"):
                st.write("**Affected Systems:**")
                for system in impact['affected_systems']:
                    st.write(f"- {system}")
                st.write("\n**Description:**")
                st.write(impact['description'])

    # Display impacted systems
    st.write("#### Impacted Body Systems")
    
    # Sort systems by severity and primary/secondary status
    systems = analysis.get('impacted_systems', [])
    systems.sort(key=lambda x: (
        {'high': 0, 'medium': 1, 'low': 2}.get(x['severity'].lower(), 3),
        not x.get('is_primary', False)
    ))
    
    for system in systems:
        status = "Primary" if system.get('is_primary', False) else "Secondary"
        with st.expander(f"{system['system_name'].title()} (Severity: {system['severity']}, {status})"):
            # Display findings
            st.write("**Findings:**")
            for finding in system['findings']:
                st.write(f"- {finding['measurement']}: {finding['value']} {finding['unit']}")
                st.write(f"  *{finding['interpretation']}*")
                
                if finding.get('related_systems'):
                    st.write("  **Related Systems:**")
                    for related in finding['related_systems']:
                        st.write(f"  - {related}")
                
                if finding.get('confirmatory_tests'):
                    st.write("  **Confirmatory Tests Needed:**")
                    for test in finding['confirmatory_tests']:
                        st.write(f"  - {test}")

            # Display potential impacts
            st.write("\n**Potential Impacts:**")
            for impact in system['potential_impacts']:
                st.write(f"- {impact}")

            # Display recommendations
            st.write("\n**Recommendations:**")
            for rec in system['recommendations']:
                st.write(f"- [{rec['urgency'].upper()}] {rec['description']} ({rec['type']})")
                if rec.get('purpose'):
                    st.write(f"  *Purpose: {rec['purpose']}*")

    # Display summary
    if 'summary' in analysis:
        st.write("#### Summary")
        
        # Primary concerns
        st.write("**Primary Concerns:**")
        for concern in analysis['summary']['primary_concerns']:
            st.write(f"- {concern}")

        # Lifestyle recommendations
        st.write("\n**Lifestyle Recommendations:**")
        for rec in analysis['summary']['lifestyle_recommendations']:
            st.write(f"- {rec}")

        # Follow-up timeline
        st.write("\n**Follow-up Timeline:**")
        timeline = analysis['summary']['follow_up_timeline']
        
        with st.expander("Immediate Actions (24-48 hours)"):
            for action in timeline['immediate']:
                st.write(f"- {action}")
        
        with st.expander("Soon (1-2 weeks)"):
            for action in timeline['soon']:
                st.write(f"- {action}")
        
        with st.expander("Routine (1-3 months)"):
            for action in timeline['routine']:
                st.write(f"- {action}")

def main():
    st.title("Medical Report Analyzer")
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error(
            "OpenAI API key not found. Please create a .env file in the project root with:\n\n"
            "```\n"
            "OPENAI_API_KEY=your_api_key_here\n"
            "```"
        )
        return
    
    # Initialize analyzers
    try:
        text_extractor = TextExtractor()
        medical_analyzer = MedicalAnalyzer(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize analyzers: {str(e)}")
        return

    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Upload Report", "Upload Image", "Manual Input"])

    # Tab 1: File Upload
    with tab1:
        st.write("Upload medical reports or health data for analysis")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=['pdf', 'txt', 'doc', 'docx', 'rtf'],
            key="report_uploader"
        )

        if uploaded_file is not None:
            try:
                # Show file info
                file_details = {
                    "Filename": uploaded_file.name,
                    "File Type": uploaded_file.type,
                    "File Size": f"{uploaded_file.size / 1024:.2f} KB"
                }
                st.write("### File Details")
                for key, value in file_details.items():
                    st.write(f"**{key}:** {value}")

                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                # Extract text
                with st.spinner('Extracting text from document...'):
                    text = text_extractor.extract_text(tmp_path)
                    
                # Remove temp file
                os.unlink(tmp_path)

                # Show extracted text in expander
                with st.expander("View Extracted Text"):
                    st.text(text)

                # Extract structured data
                with st.spinner('Extracting data from text...'):
                    extracted_data = medical_analyzer.extract_data(text)

                # Show extracted data in expander
                with st.expander("View Extracted Data"):
                    st.json(extracted_data)

                # Analyze impacted systems
                with st.spinner('Analyzing health impacts...'):
                    analysis = medical_analyzer.analyze_impacts(extracted_data)

                # Display results
                display_analysis_results(analysis)

            except Exception as e:
                st.error(f"Error analyzing report: {str(e)}")

    # Tab 2: Image Upload
    with tab2:
        st.write("### Upload Medical Image")
        st.write("Upload medical images (X-ray, MRI, CT scan, etc.) for analysis")
        
        # Image upload
        uploaded_image = st.file_uploader(
            "Choose an image", 
            type=['png', 'jpg', 'jpeg'],
            key="image_uploader"
        )
        
        # Image type selection
        image_type = st.selectbox(
            "Select Image Type",
            ["X-ray", "MRI", "CT Scan", "Ultrasound", "PET Scan", "Other"],
            help="Select the type of medical image you are uploading"
        )

        if uploaded_image is not None:
            try:
                # Show image
                st.image(uploaded_image, caption="Uploaded Medical Image", use_column_width=True)

                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_image.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_image.getvalue())
                    tmp_path = tmp_file.name

                # Extract text from image
                with st.spinner('Extracting text from image...'):
                    text = text_extractor.extract_text(tmp_path)
                    
                # Remove temp file
                os.unlink(tmp_path)

                # Show extracted text in expander
                with st.expander("View Extracted Text"):
                    if text and text.strip():
                        st.text(text)
                    else:
                        st.warning("No text was extracted from the image. Analysis will be based on image type only.")

                # Analyze image
                with st.spinner('Analyzing image...'):
                    try:
                        analysis = medical_analyzer.analyze_image(text, image_type)
                        # Display results
                        display_analysis_results(analysis)
                    except Exception as analysis_error:
                        st.error(f"Error during image analysis: {str(analysis_error)}")
                        st.write("Debug Information:")
                        st.write(f"- Image Type: {image_type}")
                        st.write(f"- Extracted Text Length: {len(text) if text else 0}")
                        if text and text.strip():
                            with st.expander("Show Extracted Text"):
                                st.text(text)

            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

    # Tab 3: Manual Input
    with tab3:
        st.write("Enter your health information manually")
        
        # Health Issues
        st.write("### Health Issues")
        health_issues = st.text_area(
            "List any current health issues or medical conditions (one per line)",
            help="Enter each health issue on a new line"
        )

        # Symptoms
        st.write("### Symptoms")
        symptoms = st.text_area(
            "List your current symptoms (one per line)",
            help="Enter each symptom on a new line"
        )

        # Vitals
        st.write("### Vital Signs")
        col1, col2 = st.columns(2)
        with col1:
            blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)")
            heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, max_value=250)
        with col2:
            temperature = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, step=0.1)
            respiratory_rate = st.number_input("Respiratory Rate (breaths/min)", min_value=0, max_value=100)

        # Lifestyle Data
        st.write("### Lifestyle Information")
        col3, col4 = st.columns(2)
        with col3:
            exercise = st.selectbox(
                "Exercise Frequency",
                ["None", "1-2 times/week", "3-4 times/week", "5+ times/week"]
            )
            sleep = st.number_input("Average Sleep (hours/day)", min_value=0, max_value=24)
        with col4:
            diet = st.multiselect(
                "Diet Type",
                ["Regular", "Vegetarian", "Vegan", "Keto", "Low-carb", "Other"]
            )
            stress_level = st.select_slider(
                "Stress Level",
                options=["Low", "Medium", "High"]
            )

        # Submit button
        if st.button("Analyze Health Data"):
            try:
                # Prepare health data
                health_data = {
                    "health_issues": [issue.strip() for issue in health_issues.split('\n') if issue.strip()],
                    "symptoms": [symptom.strip() for symptom in symptoms.split('\n') if symptom.strip()],
                    "vitals": {
                        "blood_pressure": blood_pressure,
                        "heart_rate": heart_rate,
                        "temperature": temperature,
                        "respiratory_rate": respiratory_rate
                    },
                    "lifestyle_data": {
                        "exercise_frequency": exercise,
                        "sleep_hours": sleep,
                        "diet_type": diet,
                        "stress_level": stress_level
                    }
                }

                # Analyze the manual input
                with st.spinner('Analyzing health data...'):
                    analysis = medical_analyzer.analyze_manual_input(health_data)

                # Display results
                display_analysis_results(analysis)

            except Exception as e:
                st.error(f"Error analyzing health data: {str(e)}")

if __name__ == "__main__":
    main()
