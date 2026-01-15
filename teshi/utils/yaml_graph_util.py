import yaml
import os

def load_graph_from_yaml(path):
    if not os.path.exists(path):
        return {"nodes": [], "connections": []}
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
            return data or {"nodes": [], "connections": []}
        except yaml.YAMLError as e:
            print(f"Error loading graph from {path}: {e}")
            return {"nodes": [], "connections": []}

def save_graph_to_yaml(graph_data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(graph_data, f, allow_unicode=True)
