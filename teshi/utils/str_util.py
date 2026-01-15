import re

def format_jupyter_traceback(traceback_list):
    """
    Formats a Jupyter traceback list into a readable string.
    Removes ANSI color codes.
    """
    if not traceback_list:
        return ""
    
    full_text = "\n".join(traceback_list)
    
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', full_text)
