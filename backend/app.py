from flask import Flask, request, jsonify, send_file
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
import requests

load_dotenv()

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
import base64

def quill_to_pdf_base64(content_delta):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        default_style = ParagraphStyle(
            name='Default',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
        styles.add(default_style)

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
        buffer.seek(0)
        pdf_data = buffer.read()
        return base64.b64encode(pdf_data).decode('utf-8')
    except Exception as e:
        print(f"Error in quill_to_pdf_base64: {e}")
        return None

def save_quill_to_pdf(content_delta, output_path):
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        default_style = ParagraphStyle(
            name='Default',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
        styles.add(default_style)

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
        return None

app = Flask(__name__)
CORS(app)

API_KEY = "AIzaSyBF7M96A9L4J9_XSzRTUgrWH1RVaisTRKY" 
genai.configure(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20" 

def _gemini_generate_content_with_backoff(model, payload, retries=5, delay=1):
    for i in range(retries):
        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            if result.get('candidates') and result['candidates'][0].get('content') and \
               result['candidates'][0]['content'].get('parts') and \
               result['candidates'][0]['content']['parts'][0].get('text'):
                raw_gemini_text_response = result['candidates'][0]['content']['parts'][0].get('text', '')
                
                cleaned_response = raw_gemini_text_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[len('```json'):].strip()
                elif cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[len('```'):].strip()
                
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-len('```')].strip()
                
                print(f"DEBUG: Processed Gemini API response text: {cleaned_response[:500]}...")
                return cleaned_response
            else:
                print(f"Unexpected API response structure: {result}")
                raise ValueError("Unexpected API response structure.")
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429 and i < retries - 1:
                print(f"Rate limit hit. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
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
    prompt = f"""
    Given the following document text, extract key information and present it as a single JSON object.
    The keys of the JSON object should be descriptive field names (e.g., "Name", "Contact Information", "Education", "Skills", "Product Name", "Ingredients").
    The values should be the extracted content for that field.
    - If a section contains a list (e.g., skills, ingredients), the value should be a JSON array of strings.
    - If a section contains structured items (e.g., multiple experiences, each with job title, company, dates), the value should be a JSON array of objects.
    - For general text sections or single values, the value should be a string.

    Return ONLY the JSON object, with no other text or formatting.

    Document Text:
    ---
    {raw_text}
    ---
    """

    chat_history = []
    chat_history.append({ "role": "user", "parts": [{ "text": prompt }] })

    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "text/plain",
        }
    }

    try:
        json_string = _gemini_generate_content_with_backoff(GEMINI_MODEL, payload)
        
        # FIX: Expect a single JSON object (dictionary) at the top level
        parsed_object = json.loads(json_string) 
        
        if not isinstance(parsed_object, dict):
            print(f"Warning: Gemini API returned non-dict JSON: {parsed_object}. Expected a dictionary.")
            raise ValueError("Gemini API did not return expected JSON object structure.")

        parsed_data_dict = {}
        parsed_data_order = []
        # FIX: Iterate directly over the key-value pairs of the parsed object
        for field_name, field_value in parsed_object.items():
            parsed_data_dict[field_name] = field_value
            parsed_data_order.append(field_name)

        return parsed_data_dict, parsed_data_order
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API response: {e}. Raw response: {json_string[:500]}...")
        return {}, []
    except Exception as e:
        print(f"Error during AI extraction: {e}")
        return {}, []


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
    is_doc = filename.endswith('.doc') or content_type == 'application/msword'
    is_txt = filename.endswith('.txt') or content_type == 'text/plain'

    raw_text = ""
    quill_content_delta = []

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
                                raw_text += text + '\n'
                                
                                attributes = {}
                                if span['flags'] & 1:
                                    attributes['bold'] = True
                                if span['flags'] & 2:
                                    attributes['italic'] = True
                                
                                attributes['size'] = round(span['size'])
                                attributes['font'] = span['font'] 
                                
                                quill_content_delta.append({
                                    'insert': text + '\n',
                                    'attributes': attributes
                                })
            doc.close()

        elif is_docx or is_doc:
            import docx
            doc = docx.Document(io.BytesIO(file_content_bytes))
            for para in doc.paragraphs:
                raw_text += para.text + '\n'
                quill_content_delta.append({'insert': para.text + '\n'})

        elif is_txt:
            raw_text = file_content_bytes.decode('utf-8')
            quill_content_delta.append({'insert': raw_text})

        else:
            return jsonify({'error': f'Unsupported file type. Expected PDF, DOCX, or TXT. Got: filename="{file.filename}", content_type="{file.content_type}"'}), 400

        parsed_data_dict, parsed_data_order = extract_document_details(raw_text)
        
        for key, value in parsed_data_dict.items():
            if isinstance(value, (list, dict)):
                parsed_data_dict[key] = json.dumps(value, indent=2)

        print(f"Extracted initial Quill Delta (first 2 items): {quill_content_delta[:2]}")
        print(f"AI-Parsed data: {parsed_data_dict}")
        print(f"AI-Parsed data order: {parsed_data_order}")

        return jsonify({
            'quill_content_delta': quill_content_delta,
            'parsed_data': parsed_data_dict,
            'parsed_data_order': parsed_data_order,
            'raw_text_content': raw_text
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
        edited_data = data.get('edited_data', {})
        # FIX: Corrected variable name from quill_content_delta to quill_delta_content
        quill_delta_content = data.get('quill_content_delta', []) 

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        output_json_filename = f"saved_document_structured_{timestamp}.json"
        with open(os.path.join("downloads", output_json_filename), 'w') as f:
            json.dump(edited_data, f, indent=2)
        print(f"Saved structured data to {output_json_filename}")

        output_delta_filename = f"saved_document_quill_delta_{timestamp}.json"
        with open(os.path.join("downloads", output_delta_filename), 'w') as f:
            # FIX: Use the correctly defined variable here
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

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exported_document_{timestamp}.pdf"
        output_path = os.path.join("downloads", filename)

        success = save_quill_to_pdf(quill_delta, output_path)

        if success:
            return jsonify({
                'message': 'PDF exported successfully to server',
                'filename': filename,
                'pdf_download_url': f'/download/{filename}'
            })
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500

    except Exception as e:
        print(f"Error exporting PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to export PDF: {str(e)}'}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_pdf(filename):
    try:
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

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    app.run(debug=True, port=5000)
    