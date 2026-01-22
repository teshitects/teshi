from .base_node import BaseNode
import json

class APINode(BaseNode):
    """
    Node for API Automation.
    Params:
        - method: GET, POST, PUT, DELETE
        - url: params['url']
        - headers: params['headers'] (dict)
        - body: params['body'] (dict or str)
    """
    def __init__(self, title, pos=(0,0), params=None, node_uuid=None):
        super().__init__(title, pos, params, node_uuid)
        self.node_type = "api"
        # Ensure defaults
        if "method" not in self.params: self.params["method"] = "GET"
        if "url" not in self.params: self.params["url"] = "http://localhost"
        if "headers" not in self.params: self.params["headers"] = {}
        if "body" not in self.params: self.params["body"] = {}

    def generate_code(self) -> str:
        """
        Generates python code to make an HTTP request.
        """
        method = self.params.get("method", "GET")
        url = self.params.get("url", "")
        headers = self.params.get("headers", {})
        body = self.params.get("body", {})
        
        # Simple generation using requests
        code_lines = [
            "import requests",
            "import json",
            f"url = '{url}'",
            f"headers = {json.dumps(headers)}",
            f"payload = {json.dumps(body)}",
            "",
            f"# Execute {method} Request",
            f"response = requests.{method.lower()}(url, headers=headers, json=payload)",
            "print(f'Status Code: {response.status_code}')",
            "print(f'Response: {response.text}')"
        ]
        
        self.code = "\n".join(code_lines)
        return self.code
