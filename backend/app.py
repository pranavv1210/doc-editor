from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import fitz
import os
import io
from datetime import datetime
import re
import json
import google.generativeai as genai
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- External Modules (quill_converter.py, label_studio_integration.py) ---
# NOTE: These are assumed to be present in your backend directory.
# Basic implementations are provided at the end of this app.py for completeness.

# quill_converter.py content (simplified for this example)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch
import base64 # Import base64 for PDF export to base64 string

def quill_to_pdf_base64(content_delta):
    """
    Converts QuillJS content (delta format) to a PDF and returns it as a base64 string.
    This is a simplified conversion, it won't perfectly replicate complex Quill formatting
    or original document layout.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add a default paragraph style
        default_style = ParagraphStyle(
            name='Default',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
        styles.add(default_style)

        current_text = ""
        current_attributes = {}

        for item in content_delta:
            text = item.get('insert', '')
            attributes = item.get('attributes', {})

            if text:
                # Handle new lines
                parts = text.split('\n')
                for i, part in enumerate(parts):
                    if part:
                        # Apply basic formatting (bold, italic)
                        style_name = 'Default'
                        if attributes.get('bold') and attributes.get('italic'):
                            style_name = 'BoldItalic'
                            if 'BoldItalic' not in styles:
                                styles.add(ParagraphStyle(
                                    name='BoldItalic',
                                    parent=styles['Default'],
                                    fontName='Helvetica-BoldOblique'
                                ))
                        elif attributes.get('bold'):
                            style_name = 'Bold'
                            if 'Bold' not in styles:
                                styles.add(ParagraphStyle(
                                    name='Bold',
                                    parent=styles['Default'],
                                    fontName='Helvetica-Bold'
                                ))
                        elif attributes.get('italic'):
                            style_name = 'Italic'
                            if 'Italic' not in styles:
                                styles.add(ParagraphStyle(
                                    name='Italic',
                                    parent=styles['Default'],
                                    fontName='Helvetica-Oblique'
                                ))
                        
                        # Use extracted font size if available, otherwise default
                        font_size = attributes.get('size')
                        if font_size and isinstance(font_size, (int, float)):
                            style = ParagraphStyle(
                                name=f'CustomSize_{font_size}',
                                parent=styles[style_name],
                                fontSize=font_size
                            )
                            if f'CustomSize_{font_size}' not in styles:
                                styles.add(style)
                            story.append(Paragraph(part, style))
                        else:
                            story.append(Paragraph(part, styles[style_name]))
                    
                    if i < len(parts) - 1: # Add a line break for newlines
                        story.append(Spacer(1, 0.2 * inch)) # Adjust spacing for newlines

        doc.build(story)
        buffer.seek(0)
        pdf_data = buffer.read()
        return base64.b64encode(pdf_data).decode('utf-8')
    except Exception as e:
        print(f"Error in quill_to_pdf_base64: {e}")
        return None

def save_quill_to_pdf(content_delta, output_path):
    """
    Saves QuillJS content (delta format) to a PDF file.
    This uses the same logic as quill_to_pdf_base64 but saves to a file.
    """
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add a default paragraph style
        default_style = ParagraphStyle(
            name='Default',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
        styles.add(default_style)

        current_text = ""
        current_attributes = {}

        for item in content_delta:
            text = item.get('insert', '')
            attributes = item.get('attributes', {})

            if text:
                parts = text.split('\n')
                for i, part in enumerate(parts):
                    if part:
                        style_name = 'Default'
                        if attributes.get('bold') and attributes.get('italic'):
                            style_name = 'BoldItalic'
                            if 'BoldItalic' not in styles:
                                styles.add(ParagraphStyle(
                                    name='BoldItalic',
                                    parent=styles['Default'],
                                    fontName='Helvetica-BoldOblique'
                                ))
                        elif attributes.get('bold'):
                            style_name = 'Bold'
                            if 'Bold' not in styles:
                                styles.add(ParagraphStyle(
                                    name='Bold',
                                    parent=styles['Default'],
                                    fontName='Helvetica-Bold'
                                ))
                        elif attributes.get('italic'):
                            style_name = 'Italic'
                            if 'Italic' not in styles:
                                styles.add(ParagraphStyle(
                                    name='Italic',
                                    parent=styles['Default'],
                                    fontName='Helvetica-Oblique'
                                ))
                        
                        font_size = attributes.get('size')
                        if font_size and isinstance(font_size, (int, float)):
                            style = ParagraphStyle(
                                name=f'CustomSize_{font_size}',
                                parent=styles[style_name],
                                fontSize=font_size
                            )
                            if f'CustomSize_{font_size}' not in styles:
                                styles.add(style)
                            story.append(Paragraph(part, style))
                        else:
                            story.append(Paragraph(part, styles[style_name]))
                    
                    if i < len(parts) - 1:
                        story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        print(f"PDF saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error in save_quill_to_pdf: {e}")
        return False

# label_studio_integration.py content (simplified mocks for demonstration)
import requests
import os
import json
from label_studio_sdk.client import LabelStudio

# --- DIRECTLY USE PROVIDED LABEL STUDIO CREDENTIALS ---
_LABEL_STUDIO_URL = 'http://localhost:8080'
_LABEL_STUDIO_API_KEY = 'd6f8a2622d39e9d89ff0dfef1a80ad877f4ee9e3'
# ---------------------------------------------------

class LabelStudioIntegration:
    def __init__(self, url=_LABEL_STUDIO_URL, api_key=_LABEL_STUDIO_API_KEY):
        self.url = url
        self.api_key = api_key
        self.client = None
        if self.api_key:
            try:
                self.client = LabelStudio(base_url=self.url, api_key=self.api_key)
                self.client.check_connection() # This will raise an error if connection fails
                print("Label Studio client initialized and connected.")
            except Exception as e:
                print(f"Failed to connect to Label Studio: {e}")
                self.client = None
        else:
            print("Label Studio API key not found. Label Studio integration disabled.")

    def test_connection(self):
        if not self.client:
            return False
        try:
            self.client.check_connection()
            return True
        except Exception as e:
            print(f"Label Studio connection failed: {e}")
            return False

    def get_projects(self):
        if not self.client:
            return []
        try:
            return self.client.get_projects()
        except Exception as e:
            print(f"Error getting Label Studio projects: {e}")
            return []

    def create_project(self, project_name, labeling_config):
        if not self.client:
            raise Exception("Label Studio client not initialized.")
        try:
            project = self.client.create_project(title=project_name, labeling_config=labeling_config)
            print(f"Created Label Studio project: {project.title} with ID: {project.id}")
            return project.id
        except Exception as e:
            print(f"Error creating Label Studio project: {e}")
            raise

    def create_resume_annotation_project(self, project_name):
        labeling_config = """
        <View>
            <Header value="Resume Annotation"/>
            <Text name="resume_text" value="$resume_text"/>
            <Labels name="label" toName="resume_text">
                <Label value="Name" background="red"/>
                <Label value="Contact" background="darkorange"/>
                <Label value="Email" background="orange"/>
                <Label value="Phone" background="peru"/>
                <Label value="Address" background="olivedrab"/>
                <Label value="Objective" background="forestgreen"/>
                <Label value="Education" background="green"/>
                <Label value="Experience" background="teal"/>
                <Label value="Skills" background="blue"/>
                <Label value="Projects" background="purple"/>
                <Label value="Achievements" background="violet"/>
                <Label value="Languages" background="magenta"/>
                <Label value="Co-Curricular" background="gray"/>
                <Label value="Personal Details" background="black"/>
            </Labels>
        </View>
        """
        return self.create_project(project_name, labeling_config)

    def create_skill_extraction_project(self, project_name):
        labeling_config = """
        <View>
            <Header value="Skill Extraction"/>
            <Text name="text" value="$text"/>
            <Labels name="label" toName="text">
                <Label value="Skill" background="green"/>
            </Labels>
        </View>
        """
        return self.create_project(project_name, labeling_config)

    def create_education_validation_project(self, project_name):
        labeling_config = """
        <View>
            <Header value="Education Validation"/>
            <Text name="text" value="$text"/>
            <Labels name="label" toName="text">
                <Label value="Degree" background="blue"/>
                <Label value="University" background="purple"/>
                <Label value="GraduationDate" background="orange"/>
            </Labels>
        </View>
        """
        return self.create_project(project_name, labeling_config)

    def export_parsed_data_to_label_studio(self, tasks_to_import, project_id):
        if not self.client:
            raise Exception("Label Studio client not initialized.")
        try:
            project = self.client.get_project(project_id)
            imported_tasks = project.import_tasks(tasks_to_import) 
            print(f"Imported {len(imported_tasks)} tasks to project {project_id}")
            return imported_tasks
        except Exception as e:
            print(f"Error exporting data to Label Studio: {e}")
            raise

    def import_annotated_data(self, project_id):
        if not self.client:
            raise Exception("Label Studio client not initialized.")
        try:
            project = self.client.get_project(project_id)
            tasks = project.get_tasks()
            annotated_tasks = []
            for task in tasks:
                if task.annotations:
                    # In a real scenario, you'd parse Label Studio's annotation results
                    # based on your labeling config. This is a placeholder.
                    for annotation in task.annotations:
                        annotated_tasks.append({
                            "task_id": task.id,
                            "data": task.data,
                            "annotation": annotation.as_dict() # Get annotation details
                        })
            print(f"Imported {len(annotated_tasks)} annotated tasks from project {project_id}")
            return {"annotated_tasks": annotated_tasks}
        except Exception as e:
            print(f"Error importing annotated data from Label Studio: {e}")
            raise

    def export_insights_report(self, annotated_data, output_file):
        # This is a mock function. In a real app, you'd analyze `annotated_data`
        # to generate meaningful insights (e.g., inter-annotator agreement,
        # distribution of labels, common extraction errors).
        print(f"Generating mock insights report to {output_file}")
        with open(output_file, 'w') as f:
            json.dump({"report_status": "mock_report_generated", "data_summary": annotated_data}, f, indent=2)

    def create_batch_annotation_workflow(self, ls_tasks, project_type):
        if not self.client:
            raise Exception("Label Studio client not initialized.")
        
        project_name = f"Batch Annotation - {project_type} - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project_id = None
        if project_type == 'resume':
            project_id = self.create_resume_annotation_project(project_name)
        elif project_type == 'skills':
            project_id = self.create_skill_extraction_project(project_name)
        elif project_type == 'education':
            project_id = self.create_education_validation_project(project_name)
        else: # Generic project for any document
            # Create a generic labeling config based on the expected fields
            # This is simplified; in a real app, you'd generate this dynamically or use a predefined one
            generic_labeling_config = """
            <View>
                <Header value="Generic Document Annotation"/>
                <Text name="document_text" value="$document_text"/>
                <Labels name="label" toName="document_text">
                    <Label value="Field" background="blue"/>
                </Labels>
            </View>
            """
            project_id = self.create_project(project_name, generic_labeling_config)

        tasks_created = 0
        if project_id:
            project = self.client.get_project(project_id)
            project.import_tasks(ls_tasks)
            tasks_created = len(ls_tasks) # Number of tasks sent
            print(f"Created {tasks_created} tasks for batch annotation in project {project_id}")

        return {
            "project_id": project_id,
            "project_name": project_name,
            "total_tasks": tasks_created,
            "label_studio_url": f"{self.url}/projects/{project_id}/data"
        }

def create_label_studio_integration():
    # Pass the defined URL and API Key directly to the constructor
    return LabelStudioIntegration(url=_LABEL_STUDIO_URL, api_key=_LABEL_STUDIO_API_KEY)

# --- End External Modules ---


app = Flask(__name__)
CORS(app)

# Initialize Label Studio integration
try:
    label_studio = create_label_studio_integration()
    label_studio_available = label_studio.test_connection()
except Exception as e:
    print(f"Label Studio integration not available: {e}")
    label_studio_available = False

# Configure Gemini API
# This API key is used for the Gemini AI calls
API_KEY = "AIzaSyBF7M96A9L4J9_XSzRTUgrWH1RVaisTRKY" 
genai.configure(api_key=API_KEY)
# Using gemini-2.5-flash-preview-05-20 for text generation and structured output
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20" 

def _gemini_generate_content_with_backoff(model, payload, retries=5, delay=1):
    for i in range(retries):
        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            if result.get('candidates') and result['candidates'][0].get('content') and \
               result['candidates'][0]['content'].get('parts') and \
               result['candidates'][0]['content']['parts'][0].get('text'):
                return result['candidates'][0]['content']['parts'][0].get('text', '') # Ensure text is retrieved
            else:
                print(f"Unexpected API response structure: {result}")
                raise ValueError("Unexpected API response structure.")
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429 and i < retries - 1: # Too Many Requests
                print(f"Rate limit hit. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
            else:
                print(f"HTTP error occurred: {http_err}")
                raise
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    raise Exception(f"Failed to get response from Gemini API after {retries} retries.")


def extract_document_details(raw_text):
    """
    Extracts generic key-value details from raw document text using Gemini API.
    """
    prompt = f"""
    Given the following document text, extract key information and present it as a JSON object.
    Identify common document fields such as:
    - Name (for resumes/personal documents)
    - Contact Information (email, phone, address, links)
    - Dates (e.g., Date of Birth, employment dates, project dates, expiry dates)
    - Headings/Sections (e.g., Education, Experience, Skills, Objective, Product Name, Ingredients, Instructions, Description, Price, SKU, Manufacturer, etc.)
    - Key data points relevant to the document type (e.g., for a product label: net weight, nutrition facts, barcode; for a resume: degree, university, job title, company, skills listed).
    - If a section contains a list (e.g., skills, ingredients), represent it as a JSON array of strings.
    - If a section contains structured items (e.g., multiple experiences, each with job title, company, dates), represent it as a JSON array of objects.
    - For general text sections, provide the full text.

    Be as comprehensive as possible in identifying relevant fields.
    Do NOT include any introductory or concluding remarks, only the JSON object.

    Document Text:
    ---
    {raw_text}
    ---
    """

    chat_history = []
    chat_history.append({ "role": "user", "parts": [{ "text": prompt }] })

    # Define a flexible response schema to capture various types of extracted data
    # The actual structure of the extracted data will depend on the LLM's interpretation
    # This schema allows the LLM to return a list of named fields, each with a value.
    # The value can be a string, array, or object.
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "field_name": {"type": "STRING", "description": "Descriptive name of the extracted field (e.g., Name, Email, Education, Skills, Product Name)."},
                        "field_value": {"type": ["STRING", "ARRAY", "OBJECT"], "description": "The extracted content for the field. Can be a string, array of strings, or array of objects."},
                        "type": {"type": "STRING", "description": "The type of data (e.g., contact, personal, section, product_info, list, structured_list, date, other).", "enum": ["personal", "contact", "section", "product_info", "date", "list", "structured_list", "other"]},
                        "confidence": {"type": "STRING", "description": "Confidence level of extraction (e.g., High, Medium, Low)."}
                    },
                    "required": ["field_name", "field_value", "type"]
                }
            }
        }
    }

    try:
        json_string = _gemini_generate_content_with_backoff(GEMINI_MODEL, payload)
        # The LLM returns a string that represents a JSON array
        parsed_array = json.loads(json_string)
        
        # Transform the array into a dictionary for easier frontend processing
        # and keep track of the original order
        parsed_data_dict = {}
        parsed_data_order = []
        for item in parsed_array:
            field_name = item.get('field_name')
            field_value = item.get('field_value')
            if field_name:
                parsed_data_dict[field_name] = field_value
                parsed_data_order.append(field_name)

        return parsed_data_dict, parsed_data_order
    except Exception as e:
        print(f"Error during AI extraction: {e}")
        return {}, [] # Return empty dict and list on error


# Removed the @app.route('/') home function as the frontend (React) serves the main UI.


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        print("No file provided in request")
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}, Content-Type: {file.content_type}")

    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    filename = file.filename.lower()
    content_type = file.content_type or ''

    is_pdf = filename.endswith('.pdf') or content_type == 'application/pdf'
    is_docx = filename.endswith('.docx') or content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    is_doc = filename.endswith('.doc') or content_type == 'application/msword' # Note: python-docx handles .docx well, .doc less so.
    is_txt = filename.endswith('.txt') or content_type == 'text/plain'

    raw_text = ""
    quill_content_delta = [] # Quill delta format to preserve basic formatting

    try:
        file_content_bytes = file.read()

        if is_pdf:
            doc = fitz.open(stream=file_content_bytes, filetype='pdf')
            for page in doc:
                blocks = page.get_text('dict')['blocks']
                for block in blocks:
                    if 'lines' in block:
                        for line in block['lines']:
                            for span in line['spans']:
                                text = span['text']
                                raw_text += text + '\n' # Accumulate raw text
                                
                                # Convert PyMuPDF span info to Quill attributes
                                attributes = {}
                                if span['flags'] & 1: # BOLD
                                    attributes['bold'] = True
                                if span['flags'] & 2: # ITALIC
                                    attributes['italic'] = True
                                
                                # Convert font size (PyMuPDF's size is often points)
                                # Quill's 'size' attribute typically maps to specific sizes (small, large, huge)
                                # For direct mapping, we'll keep the numeric size but it might not render perfectly in Quill
                                attributes['size'] = round(span['size']) # Round to nearest int for simplicity
                                
                                # Use font family, Quill needs 'font' attribute
                                # PyMuPDF provides font name, Quill expects specific font classes or values
                                # We'll just pass the font name as a string, Quill might ignore unknown ones
                                attributes['font'] = span['font'] 
                                
                                quill_content_delta.append({
                                    'insert': text + '\n',
                                    'attributes': attributes
                                })
            doc.close()

        elif is_docx or is_doc:
            # For DOC/DOCX, python-docx is better for .docx, .doc support needs another library or conversion
            # Here, we'll assume .docx for python-docx. For .doc, it might fail or need a conversion tool.
            # python-docx doesn't easily extract per-span formatting like PyMuPDF
            import docx
            doc = docx.Document(io.BytesIO(file_content_bytes))
            for para in doc.paragraphs:
                raw_text += para.text + '\n'
                quill_content_delta.append({'insert': para.text + '\n'}) # No rich attributes from docx easily

        elif is_txt:
            raw_text = file_content_bytes.decode('utf-8')
            quill_content_delta.append({'insert': raw_text})

        else:
            return jsonify({'error': f'Unsupported file type. Expected PDF, DOCX, or TXT. Got: filename="{file.filename}", content_type="{file.content_type}"'}), 400

        # AI-powered generic extraction
        parsed_data_dict, parsed_data_order = extract_document_details(raw_text)
        
        # Convert list/object values in parsed_data_dict to string for display in textareas
        # Frontend will handle parsing back if needed for specific field types
        for key, value in parsed_data_dict.items():
            if isinstance(value, (list, dict)):
                parsed_data_dict[key] = json.dumps(value, indent=2)

        print(f"Extracted initial Quill Delta (first 2 items): {quill_content_delta[:2]}")
        print(f"AI-Parsed data: {parsed_data_dict}")
        print(f"AI-Parsed data order: {parsed_data_order}")

        return jsonify({
            'quill_content_delta': quill_content_delta, # For Column 1 Quill view
            'parsed_data': parsed_data_dict,             # For Column 2/3 structured view
            'parsed_data_order': parsed_data_order,      # To maintain order in Column 2/3
            'raw_text_content': raw_text                 # For potential re-parsing or context
        })

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 400

@app.route('/save', methods=['POST'])
def save_document():
    try:
        data = request.get_json()
        edited_data = data.get('edited_data', {}) # This is the structured editable data
        quill_delta_content = data.get('quill_content_delta', []) # This is the full Quill delta from Column 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure 'downloads' directory exists
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # Option 1: Save the structured data as JSON
        output_json_filename = f"saved_document_structured_{timestamp}.json"
        with open(os.path.join("downloads", output_json_filename), 'w') as f:
            json.dump(edited_data, f, indent=2)
        print(f"Saved structured data to {output_json_filename}")

        # Option 2: Save the Quill delta content as a raw JSON delta file
        output_delta_filename = f"saved_document_quill_delta_{timestamp}.json"
        with open(os.path.join("downloads", output_delta_filename), 'w') as f:
            json.dump(quill_delta_content, f, indent=2)
        print(f"Saved Quill delta to {output_delta_filename}")

        return jsonify({'message': f'Document saved successfully. Saved as {output_json_filename} and {output_delta_filename}'})
    except Exception as e:
        print(f"Error saving document: {str(e)}")
        return jsonify({'error': f'Failed to save document: {str(e)}'}), 400

@app.route('/export', methods=['POST'])
def export_to_pdf():
    try:
        data = request.get_json()
        quill_delta = data.get('quill_content_delta', [])

        if not quill_delta:
            return jsonify({'error': 'No content to export'}), 400

        print(f"Exporting document with {len(quill_delta)} content items to PDF.")

        # Ensure a 'downloads' directory exists
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exported_document_{timestamp}.pdf"
        output_path = os.path.join("downloads", filename)

        success = save_quill_to_pdf(quill_delta, output_path)

        if success:
            # Instead of sending file directly, inform frontend it's saved and can be downloaded
            return jsonify({
                'message': 'PDF exported successfully to server',
                'filename': filename, # Provide filename for client to initiate download
                'pdf_download_url': f'/download/{filename}'
            })
        else:
            return jsonify({'error': 'Failed to generate PDF on server'}), 500

    except Exception as e:
        print(f"Error exporting PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to export PDF: {str(e)}'}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_pdf(filename):
    """
    Allows the frontend to download a file saved on the server.
    """
    try:
        # Ensure filename is safe to prevent directory traversal
        safe_filename = os.path.basename(filename)
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        file_path = os.path.join(downloads_dir, safe_filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        print(f"Sending file: {file_path}")
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    except Exception as e:
        print(f"Error downloading PDF: {str(e)}")
        return jsonify({'error': f'Failed to download PDF: {str(e)}'}), 400

@app.route('/export-to-label-studio', methods=['POST'])
def export_to_label_studio():
    """
    Export parsed resume data to Label Studio for annotation.
    """
    if not label_studio_available:
        return jsonify({
            'error': 'Label Studio is not available. Please set up Label Studio and API key.',
            'setup_instructions': [
                '1. Start Label Studio: label-studio start',
                '2. Go to http://localhost:8080 and create an account',
                '3. Get your API key from the account settings',
                '4. Set environment variable: LABEL_STUDIO_API_KEY=your_key'
            ]
        }), 503
    
    try:
        data = request.get_json()
        parsed_data = data.get('parsed_data', {}) # This is the dict of extracted fields
        raw_document_text = data.get('raw_document_text', "") # Send the original raw text to LS
        project_name_prefix = data.get('project_name', 'Document Annotation')
        project_type = data.get('project_type', 'generic') # 'generic', 'resume', 'skills', 'education'

        if not parsed_data:
            return jsonify({'error': 'No parsed data provided for Label Studio export'}), 400
        
        project_name = f"{project_name_prefix} - {datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create Label Studio project based on type or a generic config
        if project_type == 'resume':
            project_id = label_studio.create_resume_annotation_project(project_name)
        elif project_type == 'skills':
            project_id = label_studio.create_skill_extraction_project(project_name)
        elif project_type == 'education':
            project_id = label_studio.create_education_validation_project(project_name)
        else: # Generic project for any document
            # Create a generic labeling config based on the extracted fields
            labeling_config_labels = ""
            # Dynamically add labels for each field that was extracted by AI
            for field_name in parsed_data.keys():
                # Sanitize field_name for XML (replace spaces/special chars)
                sanitized_field_name = re.sub(r'[^a-zA-Z0-9_]', '', field_name)
                labeling_config_labels += f'<Label value="{field_name}" background="blue"/>\n'
            
            # Fallback if no fields are parsed, ensure a basic generic config
            if not labeling_config_labels:
                labeling_config_labels = '<Label value="General_Text" background="blue"/>'

            generic_labeling_config = f"""
            <View>
                <Header value="Generic Document Annotation"/>
                <Text name="document_text" value="$document_text"/>
                <Labels name="label" toName="document_text">
                    {labeling_config_labels}
                </Labels>
            </View>
            """
            project_id = label_studio.create_project(project_name, generic_labeling_config)
        
        # Prepare task data for Label Studio
        # Send the full raw text for annotation
        tasks_to_import = [{
            "data": {
                "document_text": raw_document_text,
                "parsed_data_preview": json.dumps(parsed_data, indent=2) # Preview in LS
            }
        }]
        
        # Export data to Label Studio
        tasks_created_response = label_studio.export_parsed_data_to_label_studio(tasks_to_import, project_id) # Adjusted to take list of tasks
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'project_name': project_name,
            'tasks_created': len(tasks_created_response),
            'label_studio_url': f"{label_studio.url}/projects/{project_id}/data",
            'message': f'Successfully exported {len(tasks_created_response)} tasks to Label Studio project: {project_name}'
        })
        
    except Exception as e:
        print(f"Error exporting to Label Studio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to export to Label Studio: {str(e)}'}), 500

@app.route('/import-from-label-studio', methods=['POST'])
def import_from_label_studio():
    """
    Import annotated data from Label Studio.
    """
    if not label_studio_available:
        return jsonify({
            'error': 'Label Studio is not available. Please set up Label Studio and API key.',
            'setup_instructions': [
                '1. Start Label Studio: label-studio start',
                '2. Go to http://localhost:8080 and create an account',
                '3. Get your API key from the account settings',
                '4. Set environment variable: LABEL_STUDIO_API_KEY=your_key'
            ]
        }), 503

    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        # Import annotated data
        annotated_data = label_studio.import_annotated_data(project_id)
        
        # Export insights report (optional, can be downloaded by client if needed)
        output_file = f"annotation_insights_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # Ensure a 'downloads' directory exists
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        report_path = os.path.join("downloads", output_file)

        label_studio.export_insights_report(annotated_data, report_path)
        
        return jsonify({
            'success': True,
            'annotated_data': annotated_data,
            'insights_file': output_file,
            'insights_download_url': f'/download/{output_file}',
            'message': f'Successfully imported {len(annotated_data["annotated_tasks"])} annotated tasks'
        })
        
    except Exception as e:
        print(f"Error importing from Label Studio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to import from Label Studio: {str(e)}'}), 500

@app.route('/batch-annotation', methods=['POST'])
def batch_annotation():
    """
    Create batch annotation workflow for multiple documents.
    Expects a list of dictionaries, where each dict is a parsed document
    (e.g., {'document_text': '...', 'parsed_data_preview': {...}})
    """
    if not label_studio_available:
        return jsonify({
            'error': 'Label Studio is not available. Please set up Label Studio and API key.',
            'setup_instructions': [
                '1. Start Label Studio: label-studio start',
                '2. Go to http://localhost:8080 and create an account',
                '3. Get your API key from the account settings',
                '4. Set environment variable: LABEL_STUDIO_API_KEY=your_key'
            ]
        }), 503

    try:
        data = request.get_json()
        documents_to_annotate = data.get('documents_to_annotate', []) # This should be a list of {'raw_text': ..., 'parsed_data': ...}
        project_type = data.get('project_type', 'generic')
        
        if not documents_to_annotate:
            return jsonify({'error': 'No documents provided for batch annotation'}), 400
        
        # Transform input for create_batch_annotation_workflow
        # It expects a list of tasks, where each task dict has a 'document_text' key.
        ls_tasks = []
        for doc_item in documents_to_annotate:
            ls_tasks.append({
                "data": {
                    "document_text": doc_item.get('raw_text', ''),
                    "parsed_data_preview": json.dumps(doc_item.get('parsed_data', {}), indent=2) # Send parsed data as preview
                }
            })

        # Create batch annotation workflow
        workflow = label_studio.create_batch_annotation_workflow(ls_tasks, project_type)
        
        return jsonify({
            'success': True,
            'workflow': workflow,
            'message': f'Created batch annotation workflow with {workflow["total_tasks"]} total tasks'
        })
        
    except Exception as e:
        print(f"Failed to create batch annotation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create batch annotation: {str(e)}'}), 500

@app.route('/label-studio-projects', methods=['GET'])
def get_label_studio_projects():
    """
    Get list of available Label Studio projects.
    """
    if not label_studio_available:
        return jsonify({
            'error': 'Label Studio is not available. Please set up Label Studio and API key.',
            'setup_instructions': [
                '1. Start Label Studio: label-studio start',
                '2. Go to http://localhost:8080 and create an account',
                '3. Get your API key from the account settings',
                '4. Set environment variable: LABEL_STUDIO_API_KEY=your_key'
            ]
        }), 503
    try:
        # Get all projects
        projects = label_studio.get_projects() # Use the wrapper method
        
        project_list = []
        for project in projects:
            tasks = project.get_tasks()
            project_info = {
                'id': project.id,
                'title': project.title,
                'created_at': project.created_at,
                'task_count': len(tasks),
                'annotation_count': sum(len(task.annotations) for task in tasks if hasattr(task, 'annotations'))
            }
            project_list.append(project_info)
        
        return jsonify({
            'success': True,
            'projects': project_list,
            'total_projects': len(project_list)
        })
        
    except Exception as e:
        print(f"Error getting projects from Label Studio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get projects: {str(e)}'}), 500

@app.route('/label-studio-status', methods=['GET'])
def label_studio_status():
    """
    Check Label Studio connection status.
    """
    if not label_studio_available:
        return jsonify({
            'success': False,
            'status': 'not_configured',
            'url': _LABEL_STUDIO_URL, # Use the directly defined URL
            'message': 'Label Studio is not configured. Please set up API key.',
            'setup_instructions': [
                '1. Start Label Studio: label-studio start',
                '2. Go to http://localhost:8080 and create an account',
                '3. Get your API key from the account settings',
                '4. Set environment variable: LABEL_STUDIO_API_KEY=your_key'
            ]
        }), 503
    
    try:
        # Test connection by getting projects
        projects = label_studio.get_projects() # Will raise exception if connection fails
        
        return jsonify({
            'success': True,
            'status': 'connected',
            'url': label_studio.url,
            'total_projects': len(projects),
            'message': 'Label Studio connection successful'
        })
        
    except Exception as e:
        print(f"Label Studio connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': 'disconnected',
            'url': label_studio.url,
            'error': str(e),
            'message': 'Label Studio connection failed. Make sure Label Studio is running and API key is correct.'
        }), 500

if __name__ == '__main__':
    # Create 'downloads' directory if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    app.run(debug=True, port=5000) # Running on port 5000 for backend
