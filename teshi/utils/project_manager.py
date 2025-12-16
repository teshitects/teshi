import os
import json

class ProjectManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.expanduser("~"), ".teshi", "projects.json")
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    # Add a new project to the list of projects
    def add_project(self, project_name, project_path):
        projects = self.load_projects()
        
        # Check if project already exists and remove it
        projects = [p for p in projects if p["path"] != project_path]
        
        # Add new project to the front (most recent)
        projects.insert(0, {"name": project_name, "path": project_path})
        
        # Keep only the most recent projects (limit to 20 for example)
        projects = projects[:20]
        
        self._save_projects(projects)

    # Load the list of projects from the config file
    def load_projects(self):
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    # Save the list of projects to the config file
    def _save_projects(self, projects):
        with open(self.config_path, "w") as f:
            json.dump(projects, f)

    def update_projects(self, project_path):
        """ Update project when click one project"""
        projects = self.load_projects()
        for project in projects:
            if project["path"] == project_path:
                projects.remove(project)
                projects.insert(0, project)
                break
        self._save_projects(projects)
