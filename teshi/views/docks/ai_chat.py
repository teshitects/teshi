import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView


class AIChatDock(QWidget):
    """AI Chat dock widget for AI assistant functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Teshi", "AIChat")
        self.messages = []
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Settings panel
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(5)
        
        # Base URL input
        self.base_url_label = QLabel("Base URL:")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1")
        
        # API Key input
        self.api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        
        # Model input
        self.model_label = QLabel("Model:")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4, gpt-3.5-turbo, etc.")
        self.model_input.setText("gpt-3.5-turbo")
        
        # Save settings button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._save_settings)
        
        settings_layout.addWidget(self.base_url_label)
        settings_layout.addWidget(self.base_url_input)
        settings_layout.addWidget(self.api_key_label)
        settings_layout.addWidget(self.api_key_input)
        settings_layout.addWidget(self.model_label)
        settings_layout.addWidget(self.model_input)
        settings_layout.addWidget(self.save_button)
        
        layout.addWidget(settings_frame)
        
        # Chat display area
        chat_label = QLabel("Chat:")
        layout.addWidget(chat_label)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("AI chat messages will appear here...")
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self._send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_message)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_chat)
        
        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.clear_button)
        
        layout.addLayout(input_layout)
        
    def _load_settings(self):
        """Load settings from QSettings"""
        base_url = self.settings.value("base_url", "")
        api_key = self.settings.value("api_key", "")
        model = self.settings.value("model", "gpt-3.5-turbo")
        
        self.base_url_input.setText(base_url)
        self.api_key_input.setText(api_key)
        self.model_input.setText(model)
        
    def _save_settings(self):
        """Save settings to QSettings"""
        base_url = self.base_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        
        self.settings.setValue("base_url", base_url)
        self.settings.setValue("api_key", api_key)
        self.settings.setValue("model", model)
        
        self._append_system_message("Settings saved successfully!")
        
    def _append_message(self, role: str, content: str):
        """Append a message to the chat display"""
        if role == "system":
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.chat_display.setTextColor(Qt.gray)
            self.chat_display.insertPlainText(content + "\n\n")
            
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            return
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if role == "user":
            self.chat_display.setTextColor(Qt.blue)
            self.chat_display.insertPlainText("You: ")
        elif role == "assistant":
            self.chat_display.setTextColor(Qt.darkGreen)
            self.chat_display.insertPlainText("AI: ")
        
        self.chat_display.setTextColor(Qt.black)
        self.chat_display.insertPlainText(content + "\n\n")
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _append_system_message(self, message: str):
        """Append a system message"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextColor(Qt.gray)
        self.chat_display.insertPlainText(message + "\n\n")

        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _remove_last_message(self, message: str):
        """Remove the last occurrence of a message"""
        text = self.chat_display.toPlainText()
        if message in text:
            # Find the position
            pos = text.rfind(message)
            if pos != -1:
                cursor = self.chat_display.textCursor()
                cursor.setPosition(pos, QTextCursor.MoveAnchor)
                cursor.setPosition(pos + len(message) + 2, QTextCursor.KeepAnchor)  # +2 for \n\n
                cursor.removeSelectedText()
        
    def _send_message(self):
        """Send a message to AI"""
        user_message = self.message_input.text().strip()
        if not user_message:
            return
            
        base_url = self.base_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        
        if not api_key:
            self._append_system_message("Error: Please enter API Key in settings!")
            return
            
        if not base_url:
            base_url = "https://api.openai.com/v1"
            
        if not model:
            model = "gpt-3.5-turbo"
            
        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})
        
        # Display user message
        self._append_message("user", user_message)
        
        # Clear input
        self.message_input.clear()
        
        # Show loading message
        thinking_message = "Thinking..."
        self._append_system_message(thinking_message)

        # Send API request (in a separate thread would be better, but using simple approach here)
        try:
            import urllib.request
            import urllib.error
            import ssl

            # Prepare request
            # Ensure URL ends with /chat/completions
            if not base_url.endswith('/chat/completions'):
                url = base_url.rstrip('/') + '/chat/completions'
            else:
                url = base_url

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": model,
                "messages": self.messages
            }

            # Create request
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            # Create SSL context (for self-signed certificates)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Send request
            response = urllib.request.urlopen(req, timeout=30, context=ssl_context)
            response_data = json.loads(response.read().decode('utf-8'))

            # Remove "Thinking..." message
            self._remove_last_message(thinking_message)

            # Extract AI response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_message = response_data["choices"][0]["message"]["content"]

                # Add to history
                self.messages.append({"role": "assistant", "content": ai_message})

                # Display AI message
                self._append_message("assistant", ai_message)
            else:
                self._append_system_message("Error: Invalid response from API")
                
        except urllib.error.URLError as e:
            self._append_system_message(f"Network Error: {str(e)}")
        except json.JSONDecodeError as e:
            self._append_system_message(f"JSON Decode Error: {str(e)}")
        except Exception as e:
            self._append_system_message(f"Error: {str(e)}")
            
    def _clear_chat(self):
        """Clear chat history"""
        self.messages = []
        self.chat_display.clear()
        self._append_system_message("Chat cleared. Start a new conversation!")
