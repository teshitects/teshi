from .ui_node import UINode

class MobileUINode(UINode):
    """
    Example: Mobile UI Automation Node (Appium).
    Inherits from UINode, so it shares 'action', 'target', 'value' params structure,
    but generates Appium-specific code.
    """
    def __init__(self, title, pos=(0,0), params=None, node_uuid=None):
        super().__init__(title, pos, params, node_uuid)
        self.node_type = "mobile_ui"
        # Add mobile-specific params defaults if needed
        if "device" not in self.params: self.params["device"] = "Android"

    def generate_code(self) -> str:
        """
        Generates Appium-specific python code.
        """
        action = self.params.get("action", "open")
        target = self.params.get("target", "") # id, xpath, etc
        value = self.params.get("value", "")
        
        code_lines = []
        
        # Skeleton for Appium Logic
        if action == "open":
            code_lines.append(f"# Launch App")
            code_lines.append(f"from appium import webdriver")
            code_lines.append(f"opts = {{'platformName': '{self.params['device']}', 'app': '{target}'}}")
            code_lines.append(f"driver = webdriver.Remote('http://localhost:4723', opts)")
            
        elif action == "click":
            code_lines.append(f"# Tap Element")
            code_lines.append(f"driver.find_element(by='xpath', value='{target}').click()")
            
        elif action == "type":
            code_lines.append(f"# Type Text")
            code_lines.append(f"el = driver.find_element(by='xpath', value='{target}')")
            code_lines.append(f"el.send_keys('{value}')")
            
        else:
            code_lines.append(f"# Unknown Mobile Action: {action}")
            
        self.code = "\n".join(code_lines)
        return self.code
