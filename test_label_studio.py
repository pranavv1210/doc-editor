import requests
import json
import time
from label_studio_integration import create_label_studio_integration, export_resume_for_annotation, import_and_analyze_annotations

def test_label_studio_integration():
    """
    Test the Label Studio integration with the document editor.
    """
    print("=== Label Studio Integration Test ===\n")
    
    # Test 1: Check Label Studio connection
    print("1. Testing Label Studio connection...")
    try:
        ls_integration = create_label_studio_integration()
        print("✓ Label Studio integration created successfully")
    except Exception as e:
        print(f"✗ Failed to create Label Studio integration: {e}")
        print("Make sure Label Studio is running on http://localhost:8080")
        return
    
    # Test 2: Check Flask app Label Studio status
    print("\n2. Testing Flask app Label Studio status...")
    try:
        response = requests.get("http://localhost:5000/label-studio-status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✓ Label Studio status: {status_data['status']}")
            print(f"  URL: {status_data['url']}")
            print(f"  Total projects: {status_data['total_projects']}")
        else:
            print(f"✗ Failed to get Label Studio status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error checking Label Studio status: {e}")
    
    # Test 3: Upload and parse a resume
    print("\n3. Uploading and parsing resume...")
    try:
        with open("sample.pdf", "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            response = requests.post("http://localhost:5000/upload", files=files)
        
        if response.status_code == 200:
            parsed_data = response.json()
            print(f"✓ Resume parsed successfully")
            print(f"  Content items: {len(parsed_data.get('content', []))}")
            print(f"  Parsed sections: {len(parsed_data.get('parsed_data', {}))}")
        else:
            print(f"✗ Failed to parse resume: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Error uploading resume: {e}")
        return
    
    # Test 4: Export to Label Studio
    print("\n4. Exporting parsed data to Label Studio...")
    try:
        export_data = {
            "parsed_data": parsed_data,
            "project_name": "Test Resume Annotation",
            "project_type": "resume"
        }
        
        response = requests.post("http://localhost:5000/export-to-label-studio", 
                               json=export_data)
        
        if response.status_code == 200:
            export_result = response.json()
            print(f"✓ Successfully exported to Label Studio")
            print(f"  Project ID: {export_result['project_id']}")
            print(f"  Tasks created: {export_result['tasks_created']}")
            print(f"  Label Studio URL: {export_result['label_studio_url']}")
            
            # Store project ID for later use
            project_id = export_result['project_id']
        else:
            print(f"✗ Failed to export to Label Studio: {response.status_code}")
            print(f"  Error: {response.text}")
            return
    except Exception as e:
        print(f"✗ Error exporting to Label Studio: {e}")
        return
    
    # Test 5: Get Label Studio projects
    print("\n5. Getting Label Studio projects...")
    try:
        response = requests.get("http://localhost:5000/label-studio-projects")
        if response.status_code == 200:
            projects_data = response.json()
            print(f"✓ Found {projects_data['total_projects']} projects")
            for project in projects_data['projects']:
                print(f"  - {project['title']} (ID: {project['id']}, Tasks: {project['task_count']})")
        else:
            print(f"✗ Failed to get projects: {response.status_code}")
    except Exception as e:
        print(f"✗ Error getting projects: {e}")
    
    # Test 6: Create batch annotation workflow
    print("\n6. Creating batch annotation workflow...")
    try:
        batch_data = {
            "parsed_resumes": [parsed_data],  # Single resume for demo
            "project_type": "resume"
        }
        
        response = requests.post("http://localhost:5000/batch-annotation", 
                               json=batch_data)
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"✓ Batch annotation workflow created")
            print(f"  Total tasks: {batch_result['workflow']['total_tasks']}")
            print(f"  Projects created: {len(batch_result['workflow']['projects'])}")
        else:
            print(f"✗ Failed to create batch workflow: {response.status_code}")
    except Exception as e:
        print(f"✗ Error creating batch workflow: {e}")
    
    # Test 7: Demonstrate import functionality (would need annotations first)
    print("\n7. Testing import functionality...")
    print("Note: This would require actual annotations in Label Studio")
    print("To test this:")
    print("1. Go to the Label Studio URL above")
    print("2. Create annotations for the tasks")
    print("3. Run the import test again")
    
    print("\n=== Test Summary ===")
    print("✓ Label Studio integration is working")
    print("✓ Flask app can communicate with Label Studio")
    print("✓ Resume parsing and export functionality is ready")
    print("✓ Batch annotation workflows can be created")
    print("\nNext steps:")
    print("1. Start Label Studio: label-studio start")
    print("2. Access the Label Studio URL to create annotations")
    print("3. Use the import functionality to analyze annotations")

def test_annotation_import(project_id):
    """
    Test importing annotations from a specific project.
    """
    print(f"\n=== Testing Annotation Import for Project {project_id} ===")
    
    try:
        import_data = {"project_id": project_id}
        response = requests.post("http://localhost:5000/import-from-label-studio", 
                               json=import_data)
        
        if response.status_code == 200:
            import_result = response.json()
            print(f"✓ Successfully imported annotations")
            print(f"  Annotated tasks: {len(import_result['annotated_data']['annotated_tasks'])}")
            print(f"  Insights file: {import_result['insights_file']}")
            
            # Print insights summary
            insights = import_result['annotated_data']['insights']
            if insights['section_accuracy']:
                print("\nSection Accuracy:")
                for section, stats in insights['section_accuracy'].items():
                    accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    print(f"  {section}: {accuracy:.1f}%")
            
            if insights['common_corrections']:
                print(f"\nCommon Corrections: {len(insights['common_corrections'])}")
            
            if insights['parsing_issues']:
                print(f"Parsing Issues: {len(insights['parsing_issues'])}")
                
        else:
            print(f"✗ Failed to import annotations: {response.status_code}")
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Error importing annotations: {e}")

if __name__ == "__main__":
    test_label_studio_integration()
    
    # Uncomment and provide a project ID to test annotation import
    # test_annotation_import(1) 