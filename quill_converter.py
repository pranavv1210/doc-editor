from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black
import io
import base64

def quill_to_pdf(quill_content):
    """
    Convert Quill.js content to PDF format with exact formatting preservation
    """
    # Create a buffer to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Get default styles
    styles = getSampleStyleSheet()
    
    # Process each content item with exact formatting
    for item in quill_content:
        text = item.get('insert', '')
        attributes = item.get('attributes', {})
        
        # Skip empty text
        if not text or text.strip() == '':
            continue
        
        # Create custom style with exact formatting
        custom_style = ParagraphStyle(
            'Custom',
            parent=styles['Normal'],
            spaceAfter=0,
            spaceBefore=0,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0
        )
        
        # Apply exact formatting
        if attributes.get('bold') and attributes.get('italic'):
            custom_style.fontName = 'Helvetica-BoldOblique'
        elif attributes.get('bold'):
            custom_style.fontName = 'Helvetica-Bold'
        elif attributes.get('italic'):
            custom_style.fontName = 'Helvetica-Oblique'
        else:
            custom_style.fontName = 'Helvetica'
        
        # Handle exact font family
        if attributes.get('font'):
            font_name = attributes.get('font')
            # Map common fonts to ReportLab fonts
            if 'Times' in font_name:
                if attributes.get('bold') and attributes.get('italic'):
                    custom_style.fontName = 'Times-BoldItalic'
                elif attributes.get('bold'):
                    custom_style.fontName = 'Times-Bold'
                elif attributes.get('italic'):
                    custom_style.fontName = 'Times-Italic'
                else:
                    custom_style.fontName = 'Times-Roman'
            elif 'Arial' in font_name or 'Helvetica' in font_name:
                if attributes.get('bold') and attributes.get('italic'):
                    custom_style.fontName = 'Helvetica-BoldOblique'
                elif attributes.get('bold'):
                    custom_style.fontName = 'Helvetica-Bold'
                elif attributes.get('italic'):
                    custom_style.fontName = 'Helvetica-Oblique'
                else:
                    custom_style.fontName = 'Helvetica'
            elif 'Courier' in font_name:
                if attributes.get('bold') and attributes.get('italic'):
                    custom_style.fontName = 'Courier-BoldOblique'
                elif attributes.get('bold'):
                    custom_style.fontName = 'Courier-Bold'
                elif attributes.get('italic'):
                    custom_style.fontName = 'Courier-Oblique'
                else:
                    custom_style.fontName = 'Courier'
        
        # Handle exact font size
        if attributes.get('size'):
            size = attributes.get('size')
            # Remove 'px' if present and convert to float
            if isinstance(size, str) and size.endswith('px'):
                size = float(size[:-2])
            elif isinstance(size, str):
                size = float(size)
            else:
                size = float(size)
            
            # Convert to points (1 point = 1.333 pixels approximately)
            custom_style.fontSize = size * 0.75  # Convert pixels to points
        else:
            custom_style.fontSize = 11  # Default size
        
        # Create paragraph and add to story
        try:
            # Clean up text (remove special characters that might cause issues)
            clean_text = text.replace('\n', '<br/>')
            paragraph = Paragraph(clean_text, custom_style)
            story.append(paragraph)
        except Exception as e:
            print(f"Error processing text: {text[:50]}... Error: {e}")
            # Fallback to normal style
            fallback_paragraph = Paragraph(text.replace('\n', '<br/>'), styles['Normal'])
            story.append(fallback_paragraph)
    
    # Build the PDF
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error building PDF: {e}")
        return None

def quill_to_pdf_base64(quill_content):
    """
    Convert Quill.js content to PDF and return as base64 string
    """
    pdf_buffer = quill_to_pdf(quill_content)
    if pdf_buffer:
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()
        return base64.b64encode(pdf_data).decode('utf-8')
    return None

def save_quill_to_pdf(quill_content, filename):
    """
    Save Quill.js content to PDF file
    """
    pdf_buffer = quill_to_pdf(quill_content)
    if pdf_buffer:
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        pdf_buffer.close()
        return True
    return False