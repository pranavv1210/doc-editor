import os
import json
import requests
from label_studio_sdk import Client
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LabelStudioIntegration:
    """
    Integration class for Label Studio to handle document annotation workflows.
    """
    
    def __init__(self, url: str = "http://localhost:8080", api_key: str = None):
        """
        Initialize Label Studio integration.
        
        Args:
            url: Label Studio server URL
            api_key: API key for authentication (optional)
        """
        self.url = url
        
        # Use provided API key or get from environment
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('LABEL_STUDIO_API_KEY')
        
        if not self.api_key:
            logger.warning("No API key provided. Label Studio integration will be limited.")
            logger.info("To get an API key:")
            logger.info("1. Start Label Studio: label-studio start")
            logger.info("2. Go to http://localhost:8080")
            logger.info("3. Create an account and get your API key")
            logger.info("4. Set environment variable: LABEL_STUDIO_API_KEY=your_key")
            self.client = None
        else:
            try:
                self.client = Client(url=url, api_key=self.api_key)
                logger.info("Label Studio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Label Studio client: {e}")
                self.client = None
        
    def _check_client(self):
        """Check if client is available."""
        if not self.client:
            raise Exception("Label Studio client not available. Please set up API key.")
        
    def create_resume_annotation_project(self, project_name: str = "Resume Data Annotation") -> int:
        """
        Create a new Label Studio project for resume data annotation.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project ID
        """
        self._check_client()
        
        try:
            # Create project
            project = self.client.create_project(
                title=project_name,
                label_config="""
                <View>
                    <Text name="resume_text" value="$resume_text"/>
                    <Choices name="section_type" toName="resume_text" showInLine="true">
                        <Choice value="name"/>
                        <Choice value="contact"/>
                        <Choice value="address"/>
                        <Choice value="objective"/>
                        <Choice value="education"/>
                        <Choice value="experience"/>
                        <Choice value="skills"/>
                        <Choice value="projects"/>
                        <Choice value="achievements"/>
                        <Choice value="languages"/>
                        <Choice value="co_curricular"/>
                        <Choice value="personal"/>
                    </Choices>
                    <TextArea name="corrections" toName="resume_text" 
                             placeholder="Enter any corrections or additional information"/>
                    <Rating name="parsing_accuracy" toName="resume_text" 
                           hotkey="r" maxRating="5" />
                </View>
                """
            )
            logger.info(f"Created Label Studio project: {project.title} (ID: {project.id})")
            return project.id
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    def export_parsed_data_to_label_studio(self, parsed_data: Dict[str, Any], 
                                          project_id: int) -> List[Dict]:
        """
        Export parsed resume data to Label Studio for annotation.
        
        Args:
            parsed_data: Parsed resume data from the document processor
            project_id: Label Studio project ID
            
        Returns:
            List of task IDs
        """
        self._check_client()
        
        try:
            # Format data for Label Studio
            tasks = []
            
            # Create task for each section
            for section_name, section_data in parsed_data.get('parsed_data', {}).items():
                if section_data:  # Only create tasks for non-empty sections
                    task_data = {
                        "data": {
                            "resume_text": str(section_data),
                            "section_name": section_name,
                            "original_parsing": parsed_data.get('parsed_data', {}),
                            "content_items": parsed_data.get('content', [])[:10],  # First 10 items for context
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    # Add task to project
                    task = self.client.create_task(project_id, task_data)
                    tasks.append({
                        "task_id": task.id,
                        "section_name": section_name,
                        "data": section_data
                    })
                    logger.info(f"Created task for section '{section_name}' (Task ID: {task.id})")
            
            return tasks
        except Exception as e:
            logger.error(f"Error exporting data to Label Studio: {e}")
            raise
    
    def create_skill_extraction_project(self, project_name: str = "Skill Extraction") -> int:
        """
        Create a specialized project for skill extraction and validation.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project ID
        """
        self._check_client()
        
        try:
            project = self.client.create_project(
                title=project_name,
                label_config="""
                <View>
                    <Text name="resume_text" value="$resume_text"/>
                    <Labels name="skill_labels" toName="resume_text">
                        <Label value="Programming Language" background="red"/>
                        <Label value="Framework" background="blue"/>
                        <Label value="Database" background="green"/>
                        <Label value="Tool" background="orange"/>
                        <Label value="Platform" background="purple"/>
                        <Label value="Methodology" background="yellow"/>
                    </Labels>
                    <Choices name="skill_level" toName="resume_text" showInLine="true">
                        <Choice value="Beginner"/>
                        <Choice value="Intermediate"/>
                        <Choice value="Advanced"/>
                        <Choice value="Expert"/>
                    </Choices>
                    <TextArea name="skill_notes" toName="resume_text" 
                             placeholder="Additional notes about the skill"/>
                </View>
                """
            )
            logger.info(f"Created skill extraction project: {project.title} (ID: {project.id})")
            return project.id
        except Exception as e:
            logger.error(f"Error creating skill extraction project: {e}")
            raise
    
    def create_education_validation_project(self, project_name: str = "Education Validation") -> int:
        """
        Create a project for validating education information.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project ID
        """
        self._check_client()
        
        try:
            project = self.client.create_project(
                title=project_name,
                label_config="""
                <View>
                    <Text name="education_text" value="$education_text"/>
                    <Choices name="degree_type" toName="education_text" showInLine="true">
                        <Choice value="Bachelor"/>
                        <Choice value="Master"/>
                        <Choice value="PhD"/>
                        <Choice value="Diploma"/>
                        <Choice value="Certificate"/>
                        <Choice value="Other"/>
                    </Choices>
                    <TextArea name="institution" toName="education_text" 
                             placeholder="Institution name"/>
                    <TextArea name="field_of_study" toName="education_text" 
                             placeholder="Field of study"/>
                    <TextArea name="graduation_year" toName="education_text" 
                             placeholder="Graduation year"/>
                    <Rating name="data_quality" toName="education_text" 
                           hotkey="r" maxRating="5" />
                </View>
                """
            )
            logger.info(f"Created education validation project: {project.title} (ID: {project.id})")
            return project.id
        except Exception as e:
            logger.error(f"Error creating education validation project: {e}")
            raise
    
    def import_annotated_data(self, project_id: int) -> Dict[str, Any]:
        """
        Import annotated data from Label Studio project.
        
        Args:
            project_id: Label Studio project ID
            
        Returns:
            Dictionary containing annotated data and insights
        """
        self._check_client()
        
        try:
            # Get project
            project = self.client.get_project(project_id)
            
            # Get all tasks with annotations
            tasks = project.get_tasks()
            
            annotated_data = {
                "project_id": project_id,
                "project_title": project.title,
                "total_tasks": len(tasks),
                "annotated_tasks": [],
                "insights": {
                    "section_accuracy": {},
                    "common_corrections": [],
                    "parsing_issues": []
                }
            }
            
            for task in tasks:
                if task.annotations:
                    task_data = {
                        "task_id": task.id,
                        "section_name": task.data.get("section_name"),
                        "original_text": task.data.get("resume_text"),
                        "annotations": []
                    }
                    
                    for annotation in task.annotations:
                        annotation_data = {
                            "annotator": annotation.completed_by.username if annotation.completed_by else "Unknown",
                            "created_at": annotation.created_at,
                            "result": annotation.result
                        }
                        task_data["annotations"].append(annotation_data)
                    
                    annotated_data["annotated_tasks"].append(task_data)
            
            # Analyze insights
            self._analyze_annotations(annotated_data)
            
            logger.info(f"Imported {len(annotated_data['annotated_tasks'])} annotated tasks from project {project_id}")
            return annotated_data
            
        except Exception as e:
            logger.error(f"Error importing annotated data: {e}")
            raise
    
    def _analyze_annotations(self, annotated_data: Dict[str, Any]):
        """
        Analyze annotations to extract insights for improving parsing.
        
        Args:
            annotated_data: Dictionary containing annotated data
        """
        try:
            section_accuracy = {}
            common_corrections = []
            parsing_issues = []
            
            for task in annotated_data["annotated_tasks"]:
                section_name = task["section_name"]
                
                for annotation in task["annotations"]:
                    result = annotation["result"]
                    
                    # Analyze section type annotations
                    for item in result:
                        if item.get("from_name") == "section_type":
                            predicted_section = item.get("value", {}).get("choices", [])
                            if predicted_section:
                                if section_name not in section_accuracy:
                                    section_accuracy[section_name] = {"correct": 0, "total": 0}
                                
                                section_accuracy[section_name]["total"] += 1
                                if section_name in predicted_section:
                                    section_accuracy[section_name]["correct"] += 1
                        
                        # Analyze corrections
                        if item.get("from_name") == "corrections":
                            correction = item.get("value", {}).get("text", "")
                            if correction.strip():
                                common_corrections.append({
                                    "section": section_name,
                                    "correction": correction,
                                    "original_text": task["original_text"]
                                })
                        
                        # Analyze accuracy ratings
                        if item.get("from_name") == "parsing_accuracy":
                            rating = item.get("value", {}).get("rating", 0)
                            if rating < 3:  # Low accuracy
                                parsing_issues.append({
                                    "section": section_name,
                                    "rating": rating,
                                    "text": task["original_text"]
                                })
            
            annotated_data["insights"]["section_accuracy"] = section_accuracy
            annotated_data["insights"]["common_corrections"] = common_corrections
            annotated_data["insights"]["parsing_issues"] = parsing_issues
            
        except Exception as e:
            logger.error(f"Error analyzing annotations: {e}")
    
    def export_insights_report(self, annotated_data: Dict[str, Any], 
                             output_file: str = "annotation_insights.json"):
        """
        Export insights from annotated data to a JSON file.
        
        Args:
            annotated_data: Dictionary containing annotated data and insights
            output_file: Output file path
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(annotated_data, f, indent=2, default=str)
            
            logger.info(f"Exported insights report to {output_file}")
            
            # Print summary
            print(f"\n=== Annotation Insights Report ===")
            print(f"Project: {annotated_data['project_title']}")
            print(f"Total Tasks: {annotated_data['total_tasks']}")
            print(f"Annotated Tasks: {len(annotated_data['annotated_tasks'])}")
            
            if annotated_data['insights']['section_accuracy']:
                print(f"\nSection Accuracy:")
                for section, stats in annotated_data['insights']['section_accuracy'].items():
                    accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    print(f"  {section}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
            
            if annotated_data['insights']['common_corrections']:
                print(f"\nCommon Corrections: {len(annotated_data['insights']['common_corrections'])}")
            
            if annotated_data['insights']['parsing_issues']:
                print(f"\nParsing Issues: {len(annotated_data['insights']['parsing_issues'])}")
                
        except Exception as e:
            logger.error(f"Error exporting insights report: {e}")
            raise
    
    def create_batch_annotation_workflow(self, parsed_resumes: List[Dict[str, Any]], 
                                       project_type: str = "resume") -> Dict[str, Any]:
        """
        Create a batch annotation workflow for multiple resumes.
        
        Args:
            parsed_resumes: List of parsed resume data
            project_type: Type of project to create ("resume", "skills", "education")
            
        Returns:
            Dictionary containing project information and task IDs
        """
        self._check_client()
        
        try:
            workflow = {
                "projects": {},
                "total_tasks": 0,
                "created_at": datetime.now().isoformat()
            }
            
            for i, resume_data in enumerate(parsed_resumes):
                # Create project for this resume
                project_name = f"{project_type.capitalize()} Annotation - Resume {i+1}"
                
                if project_type == "resume":
                    project_id = self.create_resume_annotation_project(project_name)
                elif project_type == "skills":
                    project_id = self.create_skill_extraction_project(project_name)
                elif project_type == "education":
                    project_id = self.create_education_validation_project(project_name)
                else:
                    raise ValueError(f"Unknown project type: {project_type}")
                
                # Export data to project
                tasks = self.export_parsed_data_to_label_studio(resume_data, project_id)
                
                workflow["projects"][f"resume_{i+1}"] = {
                    "project_id": project_id,
                    "project_name": project_name,
                    "tasks": tasks,
                    "task_count": len(tasks)
                }
                
                workflow["total_tasks"] += len(tasks)
            
            logger.info(f"Created batch annotation workflow with {workflow['total_tasks']} total tasks")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating batch annotation workflow: {e}")
            raise

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of all projects.
        
        Returns:
            List of project information
        """
        self._check_client()
        
        try:
            projects = self.client.get_projects()
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
            
            return project_list
            
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test connection to Label Studio.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.client:
                return False
            
            # Try to get projects as a connection test
            self.client.get_projects()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Utility functions for easy integration
def create_label_studio_integration(url: str = "http://localhost:8080", 
                                  api_key: str = None) -> LabelStudioIntegration:
    """
    Create a Label Studio integration instance.
    
    Args:
        url: Label Studio server URL
        api_key: API key for authentication
        
    Returns:
        LabelStudioIntegration instance
    """
    return LabelStudioIntegration(url=url, api_key=api_key)

def export_resume_for_annotation(parsed_data: Dict[str, Any], 
                               ls_integration: LabelStudioIntegration,
                               project_name: str = "Resume Annotation") -> int:
    """
    Export a single resume for annotation.
    
    Args:
        parsed_data: Parsed resume data
        ls_integration: Label Studio integration instance
        project_name: Name of the project
        
    Returns:
        Project ID
    """
    project_id = ls_integration.create_resume_annotation_project(project_name)
    ls_integration.export_parsed_data_to_label_studio(parsed_data, project_id)
    return project_id

def import_and_analyze_annotations(project_id: int, 
                                 ls_integration: LabelStudioIntegration,
                                 output_file: str = None) -> Dict[str, Any]:
    """
    Import and analyze annotations from a Label Studio project.
    
    Args:
        project_id: Label Studio project ID
        ls_integration: Label Studio integration instance
        output_file: Optional output file for insights report
        
    Returns:
        Dictionary containing annotated data and insights
    """
    annotated_data = ls_integration.import_annotated_data(project_id)
    
    if output_file:
        ls_integration.export_insights_report(annotated_data, output_file)
    
    return annotated_data 