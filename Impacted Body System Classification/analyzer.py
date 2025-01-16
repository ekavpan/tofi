import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

class MedicalAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with OpenAI API key"""
        # Try to get API key from environment if not provided
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Either pass it to the constructor or "
                "set the OPENAI_API_KEY environment variable."
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Load prompts
        try:
            prompt_dir = os.path.join(os.path.dirname(__file__), 'prompts')
            
            with open(os.path.join(prompt_dir, 'system_prompt.txt'), 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
            
            with open(os.path.join(prompt_dir, 'analysis_prompt.txt'), 'r', encoding='utf-8') as f:
                self.analysis_prompt = f.read()
        except Exception as e:
            raise Exception(f"Failed to load prompts: {str(e)}")

    def extract_data(self, text: str) -> Dict:
        """Extract structured data from text"""
        try:
            # Make API call with retry and better error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                extracted_data = json.loads(response.choices[0].message.content)
                return extracted_data
                
            except json.JSONDecodeError:
                raise Exception("Failed to parse OpenAI response as JSON")
            except Exception as e:
                if "api_key" in str(e).lower():
                    raise Exception(
                        "Invalid OpenAI API key. Please check your API key in the .env file."
                    )
                elif "connection" in str(e).lower():
                    raise Exception(
                        "Connection error. Please check your internet connection and try again."
                    )
                else:
                    raise Exception(f"OpenAI API error: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Data extraction failed: {str(e)}")

    def analyze_impacts(self, data: Dict) -> Dict:
        """Analyze health impacts from extracted data"""
        try:
            # Prepare data for analysis
            analysis_input = self._prepare_analysis_input(data)
            
            # Make API call with retry and better error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.analysis_prompt},
                        {"role": "user", "content": (
                            "Analyze these abnormal test results and show ALL impacted body systems. "
                            "For each abnormal result, show both direct impacts (primary system) and indirect impacts (related systems). "
                            "Example: High blood sugar affects: Endocrine (primary), Cardiovascular, Renal, Nervous (secondary). "
                            f"Abnormal Results: {json.dumps(analysis_input.get('abnormal_results', []))}\n\n"
                            f"Full Data: {json.dumps(analysis_input)}"
                        )}
                    ],
                    temperature=0.1
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                # Additional validation to ensure no systems are shown for normal results
                if "impacted_systems" in analysis:
                    abnormal_test_names = {
                        str(result.get("test_name", "")).lower() 
                        for result in analysis_input.get("abnormal_results", [])
                    }
                    
                    # Filter out any systems that don't correspond to abnormal results
                    filtered_systems = []
                    for system in analysis["impacted_systems"]:
                        findings = system.get("findings", [])
                        # Keep systems if they have findings from abnormal tests
                        if any(
                            test_name in str(finding).lower()
                            for test_name in abnormal_test_names
                            for finding in findings
                        ):
                            filtered_systems.append(system)
                    
                    analysis["impacted_systems"] = filtered_systems
                
                return analysis
                
            except json.JSONDecodeError:
                raise Exception("Failed to parse OpenAI response as JSON")
            except Exception as e:
                if "api_key" in str(e).lower():
                    raise Exception("Invalid OpenAI API key. Please check your API key in the .env file.")
                elif "connection" in str(e).lower():
                    raise Exception("Connection error. Please check your internet connection and try again.")
                else:
                    raise Exception(f"OpenAI API error: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Impact analysis failed: {str(e)}")

    def analyze_manual_input(self, health_data: Dict) -> Dict:
        """Analyze manually entered health data"""
        try:
            # Prepare the input data
            analysis_input = {
                "health_issues": health_data.get("health_issues", []),
                "symptoms": health_data.get("symptoms", []),
                "lifestyle_data": health_data.get("lifestyle_data", {}),
                "vitals": health_data.get("vitals", {})
            }
            
            # Make API call with retry and better error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.analysis_prompt},
                        {"role": "user", "content": json.dumps(analysis_input)}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                # Validate analysis format and body systems
                self._validate_analysis(analysis)
                
                return analysis
                
            except json.JSONDecodeError:
                raise Exception("Failed to parse OpenAI response as JSON")
            except Exception as e:
                if "api_key" in str(e).lower():
                    raise Exception(
                        "Invalid OpenAI API key. Please check your API key in the .env file."
                    )
                elif "connection" in str(e).lower():
                    raise Exception(
                        "Connection error. Please check your internet connection and try again."
                    )
                else:
                    raise Exception(f"OpenAI API error: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Manual input analysis failed: {str(e)}")

    def analyze_image(self, image_text: str, image_type: str) -> Dict:
        """Analyze medical image data"""
        try:
            # Prepare image analysis input
            analysis_input = {
                "image_findings": [],
                "image_type": image_type,
                "raw_text": image_text,  # Add raw text for analysis
                "measurements": [],
                "vitals": {},
                "abnormal_results": []
            }

            # First, try to extract structured data
            try:
                extracted_data = self.extract_data(image_text)
                if extracted_data:
                    # Add findings from structured data
                    if "report_summary" in extracted_data:
                        if "key_findings" in extracted_data["report_summary"]["document_specific_details"]["lab_report"]:
                            analysis_input["image_findings"].extend(extracted_data["report_summary"]["document_specific_details"]["lab_report"]["key_findings"])
                        if "abnormal_results" in extracted_data["report_summary"]["document_specific_details"]["lab_report"]:
                            analysis_input["abnormal_results"].extend(extracted_data["report_summary"]["document_specific_details"]["lab_report"]["abnormal_results"])
                        if "measurements" in extracted_data["report_summary"]["document_specific_details"]["lab_report"]:
                            analysis_input["measurements"].extend(extracted_data["report_summary"]["document_specific_details"]["lab_report"]["measurements"])
            except Exception as e:
                # Continue with raw text if structured extraction fails
                pass

            # If no structured findings, use the raw text
            if not analysis_input["image_findings"] and image_text:
                analysis_input["image_findings"] = [{"finding": image_text}]

            # Get LLM analysis
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.analysis_prompt},
                        {"role": "user", "content": (
                            f"Analyze this {image_type} image findings. "
                            "Map any abnormalities or findings to the appropriate body systems. "
                            f"Data: {json.dumps(analysis_input)}"
                        )}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                # Validate analysis format and body systems
                self._validate_analysis(analysis)
                
                return analysis
                
            except json.JSONDecodeError as e:
                raise Exception("Failed to parse OpenAI response as JSON")
            except Exception as e:
                if "api_key" in str(e).lower():
                    raise Exception(
                        "Invalid OpenAI API key. Please check your API key in the .env file."
                    )
                elif "connection" in str(e).lower():
                    raise Exception(
                        "Connection error. Please check your internet connection and try again."
                    )
                else:
                    raise Exception(f"OpenAI API error: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Image analysis failed: {str(e)}")

    def _prepare_analysis_input(self, data: Dict) -> Dict:
        """Prepare extracted data for impact analysis"""
        analysis_input = {
            "measurements": [],
            "vitals": {},
            "lifestyle_data": {},
            "abnormal_results": [],
            "image_findings": []
        }
        
        # Extract measurements and abnormal results from test results
        if "report_summary" in data and "test_results" in data["report_summary"]["document_specific_details"]["lab_report"]:
            for test in data["report_summary"]["document_specific_details"]["lab_report"]["test_results"]:
                # Add all measurements
                measurement = {
                    "name": test.get("test_name", ""),
                    "value": self._safe_float(test.get("value")),
                    "unit": test.get("unit", ""),
                    "reference_range": {
                        "min": self._safe_float(test.get("reference_range", {}).get("min")),
                        "max": self._safe_float(test.get("reference_range", {}).get("max")),
                        "unit": test.get("reference_range", {}).get("unit", "")
                    },
                    "status": test.get("status", "unknown"),
                    "clinical_significance": test.get("clinical_significance", ""),
                    "potential_causes": test.get("potential_causes", [])
                }
                analysis_input["measurements"].append(measurement)
                
                # Add abnormal results separately
                if test.get("status", "").lower() != "normal":
                    abnormal = {
                        "test_name": test.get("test_name", ""),
                        "value": self._safe_float(test.get("value")),
                        "unit": test.get("unit", ""),
                        "status": test.get("status", "unknown"),
                        "clinical_significance": test.get("clinical_significance", ""),
                        "potential_causes": test.get("potential_causes", [])
                    }
                    analysis_input["abnormal_results"].append(abnormal)
        
        # Extract abnormal findings
        if "report_summary" in data and "abnormal_results" in data["report_summary"]:
            analysis_input["abnormal_results"].extend(data["report_summary"]["abnormal_results"])
        
        # Extract key findings
        if "report_summary" in data and "key_findings" in data["report_summary"]:
            analysis_input["key_findings"] = data["report_summary"]["key_findings"]
        
        # Extract overview if available
        if "report_summary" in data and "overview" in data["report_summary"]:
            analysis_input["overview"] = data["report_summary"]["overview"]
        
        # Extract image findings if available
        if "image_findings" in data:
            analysis_input["image_findings"].extend(data["image_findings"])
        
        # Extract vitals if available
        if "vitals" in data:
            analysis_input["vitals"] = data["vitals"]
        
        # Extract lifestyle data if available
        if "lifestyle_data" in data:
            analysis_input["lifestyle_data"] = data["lifestyle_data"]
        
        return analysis_input

    def _validate_analysis(self, analysis: Dict):
        """Validate analysis format and body systems"""
        # Define valid body systems and their aliases
        VALID_BODY_SYSTEMS = {
            "cardiovascular": ["cardiovascular", "cardiac", "heart", "vascular", "circulatory", "blood pressure", "bp"],
            "respiratory": ["respiratory", "pulmonary", "lung", "airway", "breathing"],
            "renal": ["renal", "urinal", "kidney", "urinary", "bladder", "urine"],
            "digestive": ["digestive", "gastrointestinal", "gi", "hepatobiliary", "liver", "hepatic", "stomach", "intestinal", "bowel"],
            "endocrine": ["endocrine", "hormonal", "thyroid", "pancreatic", "adrenal", "pituitary", "diabetes"],
            "nervous system": ["nervous system", "neurological", "neural", "brain", "cns", "pns", "cognitive"],
            "immune system": ["immune system", "immunological", "lymphatic", "immune", "autoimmune"],
            "musculoskeletal": ["musculoskeletal", "skeletal", "muscular", "bone", "joint", "muscle", "orthopedic"],
            "reproductive": ["reproductive", "genital", "fertility", "sexual", "gynecological", "obstetric"],
            "haematologic": ["haematologic", "hematologic", "blood", "coagulation", "hemoglobin", "rbc", "wbc", "platelets"],
            "ent": ["ent", "ear", "nose", "throat", "otolaryngology", "sinus", "nasal"],
            "dental": ["dental", "oral", "teeth", "gum", "periodontal"],
            "skin": ["skin", "dermatological", "cutaneous", "dermal", "integumentary"],
            "metabolic": ["metabolic", "metabolism", "nutritional", "electrolyte", "acid-base"],
            "psychiatric": ["psychiatric", "mental", "psychological", "behavioral", "mood"],
            "ophthalmologic": ["ophthalmologic", "eye", "vision", "ocular", "retinal"]
        }
        
        # Validate analysis format
        if not isinstance(analysis, dict):
            raise ValueError("Analysis response is not a dictionary")
        
        required_fields = ['impacted_systems', 'summary']
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing '{field}' in analysis")
        
        # Validate and normalize body systems
        for system in analysis.get('impacted_systems', []):
            system_name = system.get('system_name', '').lower()
            normalized_system = None
            
            # Check if the system name matches any main system or alias
            for main_system, aliases in VALID_BODY_SYSTEMS.items():
                # Check exact matches first
                if system_name == main_system or system_name in aliases:
                    normalized_system = main_system
                    break
                
                # Check if system name contains any alias
                for alias in aliases:
                    if alias in system_name or system_name in alias:
                        normalized_system = main_system
                        break
                if normalized_system:
                    break
            
            # If no match found, try to map to closest system
            if normalized_system is None:
                # Keep the original name if no match found
                normalized_system = system_name
            
            # Update to normalized system name
            system['system_name'] = normalized_system.title()

    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
