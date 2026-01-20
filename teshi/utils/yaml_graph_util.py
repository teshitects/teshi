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

def _sanitize_for_yaml(obj):
    """Convert object to YAML-serializable format."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_yaml(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_yaml(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert unknown types to string
        return str(obj)

def save_graph_to_yaml(graph_data, path):
    try:
        dir_path = os.path.dirname(path)
        if dir_path:  # Only makedirs if there's actually a directory component
            os.makedirs(dir_path, exist_ok=True)
        
        # Sanitize data before saving
        sanitized_data = _sanitize_for_yaml(graph_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(sanitized_data, f, allow_unicode=True, default_flow_style=False)
        print(f"[YAML] Saved graph to: {path}")
    except Exception as e:
        print(f"[YAML] Error saving graph to {path}: {e}")
        raise
