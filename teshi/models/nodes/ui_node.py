from .base_node import BaseNode

class UINode(BaseNode):
    """
    Node for Web UI Automation (Simple Selenium Example).
    Params:
        - action: open, click, type, assert
        - target: selector (url for open, xpath/css for others)
        - value: input value (for type/assert)
    """
    def __init__(self, title, pos=(0,0), params=None, node_uuid=None):
        super().__init__(title, pos, params, node_uuid)
        self.node_type = "ui"
        if "action" not in self.params: self.params["action"] = "open"
        if "target" not in self.params: self.params["target"] = ""
        if "value" not in self.params: self.params["value"] = ""

    def generate_code(self) -> str:
        """
        Generates python code for UI actions.
        Assumes a driver 'driver' is already initialized or we init it here (simplified).
        """
        action = self.params.get("action", "open")
        target = self.params.get("target", "")
        value = self.params.get("value", "")
        
        code_lines = []
        
        # For simplicity, we assume we might need to setup driver if not exists, 
        # but in a real graph, setup usually happens in a Setup Node.
        # We will generate standalone-ish snippets or rely on shared scope context.
        # Let's assume shared 'driver' variable in the notebook context.
        
        if action == "open":
            code_lines.append(f"# Open URL")
            code_lines.append(f"if 'driver' not in globals():")
            code_lines.append(f"    from selenium import webdriver")
            code_lines.append(f"    driver = webdriver.Chrome()")
            code_lines.append(f"driver.get('{target}')")
            
        elif action == "click":
            code_lines.append(f"# Click Element")
            code_lines.append(f"from selenium.webdriver.common.by import By")
            code_lines.append(f"driver.find_element(By.XPATH, '{target}').click()")
            
        elif action == "type":
            code_lines.append(f"# Type Text")
            code_lines.append(f"from selenium.webdriver.common.by import By")
            code_lines.append(f"el = driver.find_element(By.XPATH, '{target}')")
            code_lines.append(f"el.clear()")
            code_lines.append(f"el.send_keys('{value}')")
            
        elif action == "assert":
            code_lines.append(f"# Assert Text")
            code_lines.append(f"from selenium.webdriver.common.by import By")
            code_lines.append(f"actual = driver.find_element(By.XPATH, '{target}').text")
            code_lines.append(f"assert '{value}' in actual, f'Expected {value} in {{actual}}'")
            
        else:
            code_lines.append(f"# Unknown Action: {action}")
            
        self.code = "\n".join(code_lines)
        return self.code
