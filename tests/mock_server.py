import http.server
import json
import uuid
import os
import subprocess
import sys
from urllib.parse import urlparse, parse_qs


"""
Mock Task Management HTTP Server
================================

This script provides a local mock server for simulating task management interfaces.
It is intended for development and testing environments where the actual interfaces are unavailable.

Usage:
------
1. Start the server:
   $ python tests/mock_server.py
   (The server will run on http://127.0.0.1:5000)

API Endpoints:
--------------

1. Add Task
   - Method: POST
   - Path: /tasks/add
   - Input (JSON): {"task_name": "string", "task_view": "string"}
   - Output (JSON): {"status": "success", "task_id": "uuid"} (if successful)
   - Note: Returns 400 if task_name or task_view is missing.

2. Query Task
   - Method: GET
   - Path: /tasks/query
   - Query Parameters: task_name=string, task_view=string
   - Output (JSON): {"task_name": "string", "task_id": "uuid"} (if found)
   - Note: Returns 404 if no matching task is found.

3. Delete Task
   - Method: DELETE
   - Path: /tasks/delete/<task_id>
   - Input: task_id in the URL path.
   - Output (JSON): {"status": "success"} (if successful)
   - Note: Returns 404 if task_id does not exist.

Error Responses:
----------------
- 400: Bad Request (Invalid JSON or missing parameters)
- 404: Not Found (Route not found or resource not found)
"""
class MockTaskHandler(http.server.BaseHTTPRequestHandler):
    tasks = {}

    def _send_response(self, data, status=200):
        print(f">>> [{self.command}] {self.path} - Status: {status}", flush=True)
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        # Disable default logging to avoid clutter, since we have our own print above
        pass

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self._send_response({"error": "Invalid JSON"}, 400)
            return

        if self.path == '/tasks/add':
            task_name = data.get('task_name')
            task_view = data.get('task_view')
            
            if not task_name or not task_view:
                self._send_response({"error": "Missing task_name or task_view"}, 400)
                return
            
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = {
                "task_name": task_name,
                "task_view": task_view,
                "task_id": task_id
            }
            
            self._send_response({
                "status": "success",
                "task_id": task_id
            })
        else:
            self._send_response({"error": "Not Found"}, 404)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/tasks/query':
            query_params = parse_qs(parsed_path.query)
            task_name = query_params.get('task_name', [None])[0]
            task_view = query_params.get('task_view', [None])[0]
            
            for task_id, task in self.tasks.items():
                if (not task_name or task['task_name'] == task_name) and \
                   (not task_view or task['task_view'] == task_view):
                    self._send_response({
                        "task_name": task['task_name'],
                        "task_id": task['task_id']
                    })
                    return
            
            self._send_response({"error": "Task not found"}, 404)
        else:
            self._send_response({"error": "Not Found"}, 404)

    def do_DELETE(self):
        if self.path.startswith('/tasks/delete/'):
            task_id = self.path.split('/')[-1]
            if task_id in self.tasks:
                del self.tasks[task_id]
                self._send_response({"status": "success"})
            else:
                self._send_response({"error": "Task not found"}, 404)
        else:
            self._send_response({"error": "Not Found"}, 404)

def check_and_kill_port(port):
    """Checks for and kills any process using the specified port (Windows only)."""
    if os.name != 'nt':
        return
        
    try:
        # Find PID using the port
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True).decode()
        
        pids = set()
        for line in output.strip().split('\n'):
            if 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pids.add(parts[-1])
        
        current_pid = str(os.getpid())
        for pid in pids:
            if pid != current_pid and pid != '0':
                print(f"Stopping existing process {pid} on port {port}...")
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    except subprocess.CalledProcessError:
        # Port not in use, which is fine
        pass

def run(server_class=http.server.HTTPServer, handler_class=MockTaskHandler, port=5000):
    check_and_kill_port(port)
    server_address = ('', port)
    try:
        httpd = server_class(server_address, handler_class)
        print(f'Starting mock server on port {port}...', flush=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"Error starting server: {e}", flush=True)

if __name__ == "__main__":
    run()
