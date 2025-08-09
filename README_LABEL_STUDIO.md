# Label Studio Integration for Document Editor

This document explains how to use Label Studio integration with your Document Editor to create annotation workflows for improving document parsing accuracy.

## Overview

The Label Studio integration provides the following capabilities:

1. **Export parsed resume data** to Label Studio for human annotation
2. **Create specialized annotation projects** for different types of analysis
3. **Import annotated data** back to analyze parsing accuracy
4. **Generate insights reports** to improve parsing algorithms
5. **Batch annotation workflows** for processing multiple documents

## Prerequisites

1. **Label Studio installed** (already done via `pip install label-studio`)
2. **Flask app running** on `http://localhost:5000`
3. **Label Studio server** running on `http://localhost:8080`

## Setup Instructions

### 1. Start Label Studio Server

```bash
# Start Label Studio server
label-studio start

# Or with specific port
label-studio start --port 8080
```

### 2. Start Flask Application

```bash
# Start the document editor Flask app
python app.py
```

### 3. Test the Integration

```bash
# Run the integration test
python test_label_studio.py
```

## API Endpoints

### 1. Export to Label Studio

**Endpoint:** `POST /export-to-label-studio`

**Purpose:** Export parsed resume data to Label Studio for annotation

**Request Body:**
```json
{
  "parsed_data": {
    "parsed_data": {
      "name": "John Doe",
      "email": "john@example.com",
      "education": "...",
      "experience": "..."
    },
    "content": [...]
  },
  "project_name": "Resume Annotation Project",
  "project_type": "resume"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": 1,
  "project_name": "Resume Annotation Project",
  "tasks_created": 5,
  "label_studio_url": "http://localhost:8080/projects/1/data",
  "message": "Successfully exported 5 tasks to Label Studio"
}
```

### 2. Import from Label Studio

**Endpoint:** `POST /import-from-label-studio`

**Purpose:** Import annotated data from Label Studio

**Request Body:**
```json
{
  "project_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "annotated_data": {
    "project_id": 1,
    "project_title": "Resume Annotation Project",
    "total_tasks": 5,
    "annotated_tasks": [...],
    "insights": {
      "section_accuracy": {...},
      "common_corrections": [...],
      "parsing_issues": [...]
    }
  },
  "insights_file": "annotation_insights_1_20241204_143022.json",
  "message": "Successfully imported 3 annotated tasks"
}
```

### 3. Batch Annotation

**Endpoint:** `POST /batch-annotation`

**Purpose:** Create batch annotation workflows for multiple resumes

**Request Body:**
```json
{
  "parsed_resumes": [
    {
      "parsed_data": {...},
      "content": [...]
    }
  ],
  "project_type": "resume"
}
```

### 4. Get Label Studio Projects

**Endpoint:** `GET /label-studio-projects`

**Purpose:** List all available Label Studio projects

**Response:**
```json
{
  "success": true,
  "projects": [
    {
      "id": 1,
      "title": "Resume Annotation Project",
      "created_at": "2024-12-04T14:30:22Z",
      "task_count": 5,
      "annotation_count": 3
    }
  ],
  "total_projects": 1
}
```

### 5. Label Studio Status

**Endpoint:** `GET /label-studio-status`

**Purpose:** Check Label Studio connection status

**Response:**
```json
{
  "success": true,
  "status": "connected",
  "url": "http://localhost:8080",
  "total_projects": 1,
  "message": "Label Studio connection successful"
}
```

## Project Types

### 1. Resume Annotation (`resume`)

General resume data annotation with:
- Section type classification
- Corrections and improvements
- Parsing accuracy rating

### 2. Skill Extraction (`skills`)

Specialized skill analysis with:
- Skill type labeling (Programming Language, Framework, Database, etc.)
- Skill level assessment (Beginner, Intermediate, Advanced, Expert)
- Additional notes

### 3. Education Validation (`education`)

Education information validation with:
- Degree type classification
- Institution name extraction
- Field of study identification
- Graduation year validation
- Data quality rating

## Usage Examples

### Example 1: Export Single Resume

```python
import requests

# Upload and parse resume
with open("resume.pdf", "rb") as f:
    files = {"file": ("resume.pdf", f, "application/pdf")}
    response = requests.post("http://localhost:5000/upload", files=files)
    parsed_data = response.json()

# Export to Label Studio
export_data = {
    "parsed_data": parsed_data,
    "project_name": "My Resume Project",
    "project_type": "resume"
}

response = requests.post("http://localhost:5000/export-to-label-studio", 
                       json=export_data)
result = response.json()
print(f"Project created: {result['label_studio_url']}")
```

### Example 2: Import Annotations

```python
# Import annotated data
import_data = {"project_id": 1}
response = requests.post("http://localhost:5000/import-from-label-studio", 
                       json=import_data)
result = response.json()

# Analyze insights
insights = result['annotated_data']['insights']
for section, accuracy in insights['section_accuracy'].items():
    print(f"{section}: {accuracy['correct']}/{accuracy['total']}")
```

### Example 3: Batch Processing

```python
# Process multiple resumes
resumes = [parsed_data1, parsed_data2, parsed_data3]
batch_data = {
    "parsed_resumes": resumes,
    "project_type": "skills"
}

response = requests.post("http://localhost:5000/batch-annotation", 
                       json=batch_data)
result = response.json()
print(f"Created {result['workflow']['total_tasks']} tasks")
```

## Workflow for Improving Parsing

### Step 1: Export Data
1. Upload resumes through your document editor
2. Export parsed data to Label Studio
3. Create annotation tasks for each resume section

### Step 2: Annotate in Label Studio
1. Access the Label Studio URL provided
2. Review and correct the parsed data
3. Add missing information
4. Rate parsing accuracy
5. Provide feedback and corrections

### Step 3: Import and Analyze
1. Import annotated data back to your system
2. Generate insights reports
3. Analyze common corrections and parsing issues
4. Use insights to improve parsing algorithms

### Step 4: Continuous Improvement
1. Update parsing logic based on insights
2. Re-export improved data for validation
3. Repeat the cycle for continuous improvement

## Insights Analysis

The system provides three types of insights:

### 1. Section Accuracy
- Measures how accurately each section was parsed
- Provides accuracy percentages for each section type
- Helps identify which sections need improvement

### 2. Common Corrections
- Lists frequently made corrections
- Shows patterns in parsing errors
- Helps improve parsing rules

### 3. Parsing Issues
- Identifies sections with low accuracy ratings
- Highlights problematic parsing patterns
- Guides algorithm improvements

## Files Structure

```
DocumentEditor/
├── app.py                          # Flask app with Label Studio routes
├── label_studio_integration.py     # Label Studio integration module
├── test_label_studio.py           # Integration test script
├── README_LABEL_STUDIO.md         # This documentation
└── sample.pdf                     # Sample resume for testing
```

## Troubleshooting

### Label Studio Connection Issues
- Ensure Label Studio is running: `label-studio start`
- Check the URL in `label_studio_integration.py` (default: `http://localhost:8080`)
- Verify no firewall blocking the connection

### Flask App Issues
- Ensure Flask app is running: `python app.py`
- Check that all dependencies are installed
- Verify the Flask app is accessible at `http://localhost:5000`

### Import/Export Issues
- Check that the parsed data format matches expectations
- Verify project IDs exist in Label Studio
- Ensure annotations are completed before importing

## Next Steps

1. **Start Label Studio**: `label-studio start`
2. **Run the test**: `python test_label_studio.py`
3. **Create your first annotation project** using the API
4. **Annotate data** in the Label Studio interface
5. **Import and analyze** the annotated data
6. **Use insights** to improve your parsing algorithms

This integration provides a powerful foundation for creating high-quality training data and continuously improving your document processing capabilities. 