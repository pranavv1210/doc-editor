from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import fitz  # PyMuPDF
import os
from quill_converter import quill_to_pdf_base64, save_quill_to_pdf
import io
from datetime import datetime
import re
import json
from label_studio_integration import LabelStudioIntegration, create_label_studio_integration

app = Flask(__name__)
CORS(app)

# Initialize Label Studio integration
try:
    label_studio = create_label_studio_integration()
    label_studio_available = label_studio.test_connection()
except Exception as e:
    print(f"Label Studio integration not available: {e}")
    label_studio_available = False

def parse_resume_text(raw_text):
    """
    Parse raw resume text into a structured JSON object.
    
    Args:
        raw_text (str): Raw text extracted from PDF
        
    Returns:
        dict: Structured JSON object with parsed resume sections
    """
    
    # Define known section headers with variations
    section_headers = {
        'name': ['NAME', 'FULL NAME', 'CANDIDATE NAME'],
        'contact': ['CONTACT', 'CONTACT INFORMATION', 'CONTACT DETAILS', 'PHONE', 'MOBILE', 'EMAIL'],
        'address': ['ADDRESS', 'LOCATION', 'CURRENT ADDRESS', 'PERMANENT ADDRESS'],
        'objective': ['OBJECTIVE', 'CAREER OBJECTIVE', 'PROFESSIONAL OBJECTIVE', 'SUMMARY', 'PROFILE'],
        'education': ['EDUCATION', 'ACADEMIC BACKGROUND', 'QUALIFICATIONS', 'ACADEMIC QUALIFICATIONS'],
        'experience': ['EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT HISTORY', 'PROFESSIONAL EXPERIENCE'],
        'skills': ['SKILLS', 'TECHNICAL SKILLS', 'COMPETENCIES', 'EXPERTISE', 'TECHNOLOGIES'],
        'projects': ['PROJECTS', 'PROJECT WORK', 'ACADEMIC PROJECTS', 'PERSONAL PROJECTS'],
        'achievements': ['ACHIEVEMENTS', 'AWARDS', 'CERTIFICATIONS', 'HONORS', 'RECOGNITIONS'],
        'languages': ['LANGUAGES', 'LANGUAGE SKILLS', 'LINGUISTIC COMPETENCIES'],
        'co_curricular': ['CO CURRICULAR', 'CO-CURRICULAR', 'COCURRICULAR', 'EXTRA CURRICULAR', 'EXTRA-CURRICULAR', 'EXTRACURRICULAR', 'ACTIVITIES', 'HOBBIES', 'INTERESTS', 'PERSONAL INTERESTS'],
        'personal': ['PERSONAL DETAILS', 'PERSONAL INFORMATION', 'BIOGRAPHICAL DATA']
    }
    
    # Initialize result dictionary
    result = {}
    
    # Clean the text
    text = raw_text.strip()
    
    # Extract name (usually the first line or prominent text)
    name_match = re.search(r'^([A-Z][A-Z\s]+)(?:\n|$)', text, re.MULTILINE)
    if name_match:
        result['name'] = name_match.group(1).strip()
    
    # Extract contact information
    phone_patterns = [
        r'(\+91[-\s]?\d{10})',  # Indian format
        r'(\+1[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})',  # US format
        r'(\d{10})',  # 10-digit number
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            result['phone'] = phone_match.group(1)
            break
    
    # Extract email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        result['email'] = email_match.group(1)
    
    # Extract date of birth
    dob_patterns = [
        r'(?:DOB|Date of Birth|Birth Date)[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
    ]
    
    for pattern in dob_patterns:
        dob_match = re.search(pattern, text, re.IGNORECASE)
        if dob_match:
            result['date_of_birth'] = dob_match.group(1)
            break
    
    # Function to find section boundaries
    def find_section_boundaries(text, section_keywords):
        boundaries = []
        text_lines = text.split('\n')
        
        for i, line in enumerate(text_lines):
            line_upper = line.strip().upper()
            for keyword in section_keywords:
                if keyword in line_upper:
                    boundaries.append((i, line.strip()))
                    break
        
        return boundaries, text_lines
    
    # Extract sections
    for section_name, keywords in section_headers.items():
        if section_name in ['name', 'contact', 'phone', 'email', 'date_of_birth']:
            continue  # Already handled above
            
        boundaries, lines = find_section_boundaries(text, keywords)
        
        if boundaries:
            # Find the first occurrence of this section
            start_line = boundaries[0][0]
            
            # Find the next section or end of text
            next_section_start = len(lines)
            for i in range(start_line + 1, len(lines)):
                line_upper = lines[i].strip().upper()
                # Check if this line is a header for any other section
                for other_section, other_keywords in section_headers.items():
                    if other_section != section_name:
                        for keyword in other_keywords:
                            if keyword in line_upper:
                                next_section_start = i
                                break
                        if next_section_start != len(lines):
                            break
                if next_section_start != len(lines):
                    break
            
            # Extract content between boundaries
            content_lines = lines[start_line + 1:next_section_start]
            content = '\n'.join(content_lines).strip()
            
            if content:
                # Clean and structure the content
                if section_name == 'skills':
                    # Split skills by common delimiters
                    skills = re.split(r'[,;•\n]+', content)
                    skills = [skill.strip() for skill in skills if skill.strip()]
                    result[section_name] = skills
                elif section_name == 'languages':
                    # Split languages by common delimiters
                    languages = re.split(r'[,;•\n]+', content)
                    languages = [lang.strip() for lang in languages if lang.strip()]
                    result[section_name] = languages
                elif section_name == 'co_curricular':
                    # Split co-curricular activities by common delimiters
                    activities = re.split(r'[,;•\n]+', content)
                    activities = [activity.strip() for activity in activities if activity.strip()]
                    result[section_name] = activities
                else:
                    result[section_name] = content
    
    # Extract address (look for lines with street numbers)
    address_pattern = r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)[,\s]+[A-Za-z\s]+(?:City|Town|Village)[,\s]+[A-Za-z\s]+)'
    address_match = re.search(address_pattern, text, re.IGNORECASE)
    if address_match:
        result['address'] = address_match.group(1).strip()
    
    # If no structured sections found, try to extract basic information
    if len(result) <= 3:  # Only name, phone, email found
        lines = text.split('\n')
        if len(lines) > 0 and 'name' not in result:
            result['name'] = lines[0].strip()
        if len(lines) > 1 and 'address' not in result:
            result['address'] = lines[1].strip()
        if len(lines) > 2 and 'contact' not in result:
            result['contact'] = lines[2].strip()
    
    # Return both the result and the order of sections as they appear in the document
    return result, list(result.keys())

@app.route('/')
def home():
    return render_template('index.html')

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

    is_pdf_by_extension = filename.endswith('.pdf')
    is_doc_by_extension = filename.endswith('.doc') or filename.endswith('.docx')
    is_pdf_by_content_type = content_type == 'application/pdf'
    is_doc_by_content_type = content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

    if is_pdf_by_extension or is_pdf_by_content_type or is_doc_by_extension or is_doc_by_content_type:
        try:
            file_content = file.read()
            doc = fitz.open(stream=file_content, filetype='pdf')
            
            # Extract raw text for parsing
            raw_text = ""
            content = []
            
            for page in doc:
                blocks = page.get_text('dict')['blocks']
                for block in blocks:
                    if 'lines' in block:
                        for line in block['lines']:
                            for span in line['spans']:
                                text = span['text']
                                raw_text += text + '\n'
                                
                                content.append({
                                    'insert': text + '\n',
                                    'attributes': {
                                        'bold': bool(span['flags'] & 1),
                                        'italic': bool(span['flags'] & 2),
                                        'font': span['font'],
                                        'size': span['size']
                                    }
                                })
            
            doc.close()
            
            # Parse the raw text into structured data
            parsed_data, parsed_order = parse_resume_text(raw_text)
            
            print(f"Extracted content: {content[:2]}")
            print(f"Parsed data: {parsed_data}")
            print(f"Parsed order: {parsed_order}")
            
            return jsonify({
                'content': content,
                'parsed_data': parsed_data,
                'parsed_data_order': parsed_order,
                'original_structure': {
                    'fonts': [item['attributes']['font'] for item in content if 'font' in item['attributes']],
                    'sizes': [item['attributes']['size'] for item in content if 'size' in item['attributes']],
                    'formatting': [item['attributes'] for item in content]
                }
            })
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 400
    else:
        return jsonify({'error': f'Invalid file type. Expected PDF or DOC file. Got: filename="{file.filename}", content_type="{file.content_type}"'}), 400

@app.route('/save', methods=['POST'])
def save_document():
    try:
        data = request.get_json()
        content = data.get('content', [])
        print(f"Saving document with {len(content)} content items")
        return jsonify({'message': 'Document saved successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to save document: {str(e)}'}), 400

@app.route('/export', methods=['POST'])
def export_to_pdf():
    try:
        data = request.get_json()
        content = data.get('content', [])

        if not content:
            return jsonify({'error': 'No content to export'}), 400

        print(f"Exporting document with {len(content)} content items")

        pdf_base64 = quill_to_pdf_base64(content)

        if pdf_base64:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exported_document_{timestamp}.pdf"

            return jsonify({
                'message': 'PDF exported successfully',
                'pdf_data': pdf_base64,
                'filename': filename
            })
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500

    except Exception as e:
        print(f"Error exporting PDF: {str(e)}")
        return jsonify({'error': f'Failed to export PDF: {str(e)}'}), 400

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
        parsed_data = data.get('parsed_data', {})
        project_name = data.get('project_name', 'Resume Annotation')
        project_type = data.get('project_type', 'resume')
        
        if not parsed_data:
            return jsonify({'error': 'No parsed data provided'}), 400
        
        # Create Label Studio project
        if project_type == 'resume':
            project_id = label_studio.create_resume_annotation_project(project_name)
        elif project_type == 'skills':
            project_id = label_studio.create_skill_extraction_project(project_name)
        elif project_type == 'education':
            project_id = label_studio.create_education_validation_project(project_name)
        else:
            return jsonify({'error': f'Unknown project type: {project_type}'}), 400
        
        # Export data to Label Studio
        tasks = label_studio.export_parsed_data_to_label_studio(parsed_data, project_id)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'project_name': project_name,
            'tasks_created': len(tasks),
            'label_studio_url': f"{label_studio.url}/projects/{project_id}/data",
            'message': f'Successfully exported {len(tasks)} tasks to Label Studio'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to export to Label Studio: {str(e)}'}), 500

@app.route('/import-from-label-studio', methods=['POST'])
def import_from_label_studio():
    """
    Import annotated data from Label Studio.
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        # Import annotated data
        annotated_data = label_studio.import_annotated_data(project_id)
        
        # Export insights report
        output_file = f"annotation_insights_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        label_studio.export_insights_report(annotated_data, output_file)
        
        return jsonify({
            'success': True,
            'annotated_data': annotated_data,
            'insights_file': output_file,
            'message': f'Successfully imported {len(annotated_data["annotated_tasks"])} annotated tasks'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to import from Label Studio: {str(e)}'}), 500

@app.route('/batch-annotation', methods=['POST'])
def batch_annotation():
    """
    Create batch annotation workflow for multiple resumes.
    """
    try:
        data = request.get_json()
        parsed_resumes = data.get('parsed_resumes', [])
        project_type = data.get('project_type', 'resume')
        
        if not parsed_resumes:
            return jsonify({'error': 'No parsed resumes provided'}), 400
        
        # Create batch annotation workflow
        workflow = label_studio.create_batch_annotation_workflow(parsed_resumes, project_type)
        
        return jsonify({
            'success': True,
            'workflow': workflow,
            'message': f'Created batch annotation workflow with {workflow["total_tasks"]} total tasks'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create batch annotation: {str(e)}'}), 500

@app.route('/label-studio-projects', methods=['GET'])
def get_label_studio_projects():
    """
    Get list of available Label Studio projects.
    """
    try:
        # Get all projects
        projects = label_studio.client.get_projects()
        
        project_list = []
        for project in projects:
            project_info = {
                'id': project.id,
                'title': project.title,
                'created_at': project.created_at,
                'task_count': len(project.get_tasks()),
                'annotation_count': sum(len(task.annotations) for task in project.get_tasks())
            }
            project_list.append(project_info)
        
        return jsonify({
            'success': True,
            'projects': project_list,
            'total_projects': len(project_list)
        })
        
    except Exception as e:
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
            'url': 'http://localhost:8080',
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
        projects = label_studio.get_projects()
        
        return jsonify({
            'success': True,
            'status': 'connected',
            'url': label_studio.url,
            'total_projects': len(projects),
            'message': 'Label Studio connection successful'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'disconnected',
            'url': label_studio.url,
            'error': str(e),
            'message': 'Label Studio connection failed. Make sure Label Studio is running.'
        }), 500

@app.route('/download/<filename>', methods=['GET'])
def download_pdf(filename):
    try:
        return jsonify({'message': 'Download feature coming soon'})
    except Exception as e:
        return jsonify({'error': f'Failed to download PDF: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True)