import pdfplumber
import pytesseract
import cv2
import numpy as np
from PIL import Image
import os
from typing import Optional
from docx import Document
from striprtf.striprtf import rtf_to_text
import platform
import subprocess
import pdf2image
import fitz

class TextExtractor:
    def __init__(self):
        """Initialize TextExtractor with Tesseract configuration"""
        # Set default Tesseract path for Windows
        if platform.system() == "Windows":
            default_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in default_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"Found Tesseract at: {path}")
                    break

    def test_tesseract(self) -> bool:
        """Test if Tesseract is working properly"""
        try:
            # Create a simple test image with text
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np

            # Create a white image
            img = Image.new('RGB', (200, 50), color='white')
            d = ImageDraw.Draw(img)
            
            # Add text to image
            d.text((10,10), "Test 123", fill='black')
            
            # Try to extract text
            text = pytesseract.image_to_string(img)
            print(f"Tesseract test result: {text.strip()}")
            
            return "Test" in text or "123" in text
        except Exception as e:
            print(f"Tesseract test failed: {str(e)}")
            return False

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is installed and accessible"""
        try:
            if platform.system() == "Windows":
                # Check if tesseract is in PATH or common install locations
                result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                
                # Check common installation paths
                default_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
                return any(os.path.exists(path) for path in default_paths)
            else:
                # For non-Windows systems
                result = subprocess.run(['which', 'tesseract'], capture_output=True)
                return result.returncode == 0
        except Exception:
            return False

    def _get_install_instructions(self) -> str:
        """Get platform-specific installation instructions"""
        if platform.system() == "Windows":
            return """
To install Tesseract OCR on Windows:
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (select "Add to PATH" during installation)
3. Restart your application

Alternatively, you can install it via winget:
> winget install UB-Mannheim.TesseractOCR
"""
        else:
            return """
To install Tesseract OCR:
- Ubuntu/Debian: sudo apt-get install tesseract-ocr
- MacOS: brew install tesseract
- Other Linux: Check your package manager for tesseract-ocr
"""

    def preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gray = cv2.dilate(gray, kernel, iterations=1)

        # Apply median blur to remove noise
        gray = cv2.medianBlur(gray, 3)

        return gray

    def extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file with enhanced structure preservation"""
        try:
            all_text = []
            print(f"\nAttempting to extract text from PDF: {pdf_path}")
            
            # Method 1: Try pdfplumber with table extraction
            try:
                print("Attempting extraction with pdfplumber...")
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        print(f"Processing page {page_num}")
                        
                        # Try to extract tables first
                        tables = page.extract_tables()
                        if tables:
                            print(f"Found {len(tables)} tables on page {page_num}")
                            for table in tables:
                                # Convert table to formatted text
                                table_text = []
                                for row in table:
                                    # Clean and filter row data
                                    cleaned_row = [
                                        str(cell).strip() if cell is not None else ''
                                        for cell in row
                                    ]
                                    # Only add non-empty rows
                                    if any(cleaned_row):
                                        table_text.append('\t'.join(cleaned_row))
                                if table_text:
                                    all_text.append('\n'.join(table_text))
                                    all_text.append('\n')  # Add separator between tables
                        
                        # Extract regular text
                        text = page.extract_text(layout=True)  # Use layout mode
                        if text:
                            print(f"Extracted regular text from page {page_num}")
                            # Preserve line breaks and spacing
                            all_text.append(text)
                        else:
                            print(f"No regular text found on page {page_num}")
            except Exception as e:
                print(f"pdfplumber extraction failed: {str(e)}")

            # Method 2: Try PyMuPDF if pdfplumber didn't get anything
            if not all_text:
                try:
                    print("\nAttempting extraction with PyMuPDF...")
                    with fitz.open(pdf_path) as doc:
                        for page_num, page in enumerate(doc, 1):
                            # Extract text with more details
                            text = page.get_text("dict")  # Get detailed text information
                            if text.get("blocks"):
                                print(f"Found structured text blocks on page {page_num}")
                                page_text = []
                                for block in text["blocks"]:
                                    if "lines" in block:
                                        for line in block["lines"]:
                                            if "spans" in line:
                                                line_text = []
                                                for span in line["spans"]:
                                                    if "text" in span:
                                                        line_text.append(span["text"])
                                                if line_text:
                                                    page_text.append(" ".join(line_text))
                                if page_text:
                                    all_text.append("\n".join(page_text))
                            else:
                                print(f"No structured text found on page {page_num}")
                except Exception as e:
                    print(f"PyMuPDF extraction failed: {str(e)}")

            # Method 3: Use pdf2image + OCR as last resort
            if not all_text:
                try:
                    print("\nAttempting extraction with pdf2image + OCR...")
                    images = pdf2image.convert_from_path(pdf_path)
                    print(f"Successfully converted PDF to {len(images)} images")
                    
                    for i, image in enumerate(images, 1):
                        print(f"Processing page {i} with OCR...")
                        # Convert PIL image to OpenCV format
                        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                        
                        # Preprocess the image
                        processed_image = self.preprocess_image(cv_image)
                        
                        # Convert back to PIL Image
                        pil_image = Image.fromarray(processed_image)
                        
                        # Use Tesseract with specific configuration for structured data
                        text = pytesseract.image_to_string(
                            pil_image,
                            config='--psm 6 --oem 3 -c preserve_interword_spaces=1'
                        )
                        if text:
                            print(f"Successfully extracted text from page {i}")
                            all_text.append(text)
                        else:
                            print(f"No text found on page {i}")
                except Exception as e:
                    print(f"OCR extraction failed: {str(e)}")

            # Combine all extracted text while preserving structure
            final_text = '\n\n'.join(all_text)
            
            if not final_text.strip():
                print("\nNo text could be extracted using any method")
                raise Exception(
                    "No text could be extracted from the PDF. The file might be:"
                    "\n1. Password protected"
                    "\n2. Scanned with poor quality"
                    "\n3. Contains only images"
                    "\n4. Corrupted"
                )

            print(f"\nSuccessfully extracted {len(final_text)} characters of text")
            return final_text

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def extract_from_image(self, image_path: str) -> str:
        """Extract text from an image using OCR"""
        try:
            if not self._check_tesseract():
                raise Exception(
                    f"Tesseract is not installed or not in PATH.\n"
                    f"{self._get_install_instructions()}"
                )
            
            # Read image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Failed to load image")

            # Preprocess the image
            processed_image = self.preprocess_image(image)

            # Extract text using Tesseract
            text = pytesseract.image_to_string(
                Image.fromarray(processed_image),
                config='--psm 6'  # Assume uniform block of text
            )

            if not text.strip():
                raise Exception(
                    "No text was extracted from the image. This could be because:\n"
                    "1. The image doesn't contain text\n"
                    "2. The text is not clear enough\n"
                    "3. The image format is not supported\n"
                    "Please try uploading a clearer image or a different format."
                )

            return text

        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")

    def extract_text(self, file_path: str) -> str:
        """Extract text from various file types"""
        try:
            # Test Tesseract before proceeding
            if not self.test_tesseract():
                raise Exception(
                    "Tesseract is not working properly. Please ensure it's installed correctly:\n"
                    "1. Check if Tesseract is installed in C:\\Program Files\\Tesseract-OCR\\\n"
                    "2. If installed elsewhere, set the TESSERACT_PATH environment variable\n"
                    "3. Restart the application"
                )

            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # For image files
            if ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Read image using OpenCV
                image = cv2.imread(file_path)
                if image is None:
                    raise Exception("Failed to read image file")

                # Preprocess the image
                processed_image = self.preprocess_image(image)

                # Save preprocessed image temporarily
                temp_path = file_path + "_processed.png"
                cv2.imwrite(temp_path, processed_image)

                try:
                    # Extract text using Tesseract
                    text = pytesseract.image_to_string(
                        Image.open(temp_path),
                        config='--psm 6'  # Assume uniform block of text
                    )
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                if not text.strip():
                    raise Exception(
                        "No text was extracted from the image. This could be because:\n"
                        "1. The image doesn't contain text\n"
                        "2. The text is not clear enough\n"
                        "3. The image format is not supported\n"
                        "Please try uploading a clearer image or a different format."
                    )

                return text

            # For PDFs
            elif ext == '.pdf':
                # Convert PDF to images
                images = pdf2image.convert_from_path(file_path)
                text = []
                
                # Extract text from each page
                for image in images:
                    # Convert PIL image to OpenCV format
                    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    
                    # Preprocess the image
                    processed_image = self.preprocess_image(cv_image)
                    
                    # Extract text
                    page_text = pytesseract.image_to_string(
                        Image.fromarray(processed_image),
                        config='--psm 6'
                    )
                    text.append(page_text)
                
                return '\n'.join(text)

            # For text files
            elif ext in ['.txt', '.doc', '.docx', '.rtf']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()

            else:
                raise Exception(f"Unsupported file type: {ext}")

        except Exception as e:
            if "No text was extracted" in str(e):
                raise
            raise Exception(f"Error extracting text from file: {str(e)}")

    def extract_from_text_file(self, file_path: str) -> str:
        """Extract text from text-based files"""
        try:
            # Handle .txt files
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            
            # Handle .doc, .docx files
            elif file_path.lower().endswith(('.doc', '.docx')):
                doc = Document(file_path)
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
            # Handle .rtf files
            elif file_path.lower().endswith('.rtf'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    rtf = f.read()
                    return rtf_to_text(rtf).strip()
                    
        except Exception as e:
            raise Exception(f"Error extracting text from file: {str(e)}")
