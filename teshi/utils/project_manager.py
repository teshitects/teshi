import os
import json

class ProjectManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.expanduser("~"), ".teshi", "projects.json")
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    # Add a new project to the list of projects
    def add_project(self, project_name, project_path):
        projects = self.load_projects()
        projects.append({"name": project_name, "path": project_path})
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