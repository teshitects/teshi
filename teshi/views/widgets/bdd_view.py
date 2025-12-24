from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QLabel, QScrollArea, QToolButton, QButtonGroup, QGraphicsDropShadowEffect)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from typing import List, Dict, Optional
import re

from teshi.utils.keyword_highlighter import KeywordHighlighter


class BDDStepWidget(QFrame):
    """Single BDD step widget with styling"""
    
    def __init__(self, step_type: str, content, is_alternate: bool = False, parent=None):
        super().__init__(parent)
        self.step_type = step_type
        self.content = content  # Can be string or dict with 'content' and 'number'
        self.is_alternate = is_alternate
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        # Extract content and number
        if isinstance(self.content, dict):
            content_text = self.content['content']
            number_text = self.content['number']
        else:
            content_text = self.content
            number_text = ''
        
        # Combine number and content for display
        display_content = f"{number_text}{content_text}" if number_text else content_text
        
        # Step type indicator
        type_label = QLabel(self.step_type)
        type_label.setObjectName("stepType")
        type_label.setAlignment(Qt.AlignTop)
        
        # Add specific class for step type
        if self.step_type == "Given":
            type_label.setProperty("stepClass", "given")
        elif self.step_type == "When":
            type_label.setProperty("stepClass", "when")
        elif self.step_type == "Then":
            type_label.setProperty("stepClass", "then")
        elif self.step_type == "#":
            type_label.setProperty("stepClass", "notes")
        
        # Step content
        content_label = QLabel(display_content)
        content_label.setObjectName("stepContent")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignTop)
        
        # Add specific class for step content
        if self.step_type == "Given":
            content_label.setProperty("stepClass", "given")
        elif self.step_type == "When":
            content_label.setProperty("stepClass", "when")
        elif self.step_type == "Then":
            content_label.setProperty("stepClass", "then")
        elif self.step_type == "#":
            content_label.setProperty("stepClass", "notes")
        
        layout.addWidget(type_label)
        layout.addWidget(content_label, 1)
        
        # Set object name and step type class for styling
        self.setObjectName("bddStep")
        self.setProperty("stepType", self.step_type.lower())
        if self.is_alternate:
            self.setProperty("alternate", "true")
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(3)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class BDDScenarioWidget(QFrame):
    """Single BDD scenario widget"""
    
    def __init__(self, scenario_data: Dict, scenario_index: int, parent=None):
        super().__init__(parent)
        self.scenario_data = scenario_data
        self.scenario_index = scenario_index
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scenario header
        header_frame = QFrame()
        header_frame.setObjectName("scenarioHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        # Scenario number and title
        title_label = QLabel(f"Scenario {self.scenario_index}: {self.scenario_data['title']}")
        title_label.setObjectName("scenarioTitle")
        title_label.setFont(QFont("", 10, QFont.Bold))
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Add header to main layout
        layout.addWidget(header_frame)
        
        # Steps container
        steps_container = QFrame()
        steps_container.setObjectName("stepsContainer")
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(0)
        
        # Add Given steps
        for i, given in enumerate(self.scenario_data['given']):
            is_alternate = i % 2 == 1
            step_widget = BDDStepWidget("Given", given, is_alternate)
            steps_layout.addWidget(step_widget)
        
        # Add When steps
        for i, when in enumerate(self.scenario_data['when']):
            is_alternate = (len(self.scenario_data['given']) + i) % 2 == 1
            step_widget = BDDStepWidget("When", when, is_alternate)
            steps_layout.addWidget(step_widget)
        
        # Add Then steps
        for i, then in enumerate(self.scenario_data['then']):
            is_alternate = (len(self.scenario_data['given']) + len(self.scenario_data['when']) + i) % 2 == 1
            step_widget = BDDStepWidget("Then", then, is_alternate)
            steps_layout.addWidget(step_widget)
        
        # Add notes if present
        if self.scenario_data['notes']:
            notes_frame = QFrame()
            notes_frame.setObjectName("notesFrame")
            notes_layout = QHBoxLayout(notes_frame)
            notes_layout.setContentsMargins(15, 10, 15, 10)
            notes_layout.setSpacing(12)
            
            notes_type = QLabel("#")
            notes_type.setObjectName("stepType")
            notes_type.setAlignment(Qt.AlignTop)
            
            notes_content = QLabel(f"Notes: {self.scenario_data['notes']}")
            notes_content.setObjectName("stepContent")
            notes_content.setWordWrap(True)
            notes_content.setAlignment(Qt.AlignTop)
            notes_content.setProperty("notes", "true")
            
            notes_layout.addWidget(notes_type)
            notes_layout.addWidget(notes_content, 1)
            
            steps_layout.addWidget(notes_frame)
        
        layout.addWidget(steps_container)


class BDDViewWidget(QWidget):
    """BDD view widget with componentized display and theme support"""
    
    # Signal for when content is modified
    contentModified = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenarios = []
        self.is_dark_theme = True
        
        # Initialize keyword highlighter
        self.keyword_highlighter = KeywordHighlighter()
        
        self._setup_ui()
        self._setup_styles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Theme toggle button
        toolbar = QFrame()
        toolbar.setObjectName("bddToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(10)
        
        # Theme toggle button
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setText("🌙")
        self.theme_button.setToolTip("Toggle theme")
        self.theme_button.clicked.connect(self._toggle_theme)
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.theme_button)
        
        layout.addWidget(toolbar)
        
        # Scroll area for scenarios
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("bddScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for scenarios
        self.container_widget = QWidget()
        self.container_widget.setObjectName("bddContainer")
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(15)
        self.container_layout.addStretch()
        
        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)
    
    def _setup_styles(self):
        """Setup initial styles"""
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme-based styling"""
        if self.is_dark_theme:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            #bddToolbar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #3c3c3c;
            }
            
            #themeButton {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
            
            #themeButton:hover {
                background-color: #505050;
                border-color: #4a9eff;
            }
            
            #themeButton:pressed {
                background-color: #353535;
            }
            
            #bddScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            #bddContainer {
                background-color: #1e1e1e;
            }
            
            #bddStep {
                background-color: #252525;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                margin: 3px 0;
            }
            
            #bddStep[stepType="given"] {
                border-left: 4px solid #4CAF50;
            }
            
            #bddStep[stepType="when"] {
                border-left: 4px solid #FF9800;
            }
            
            #bddStep[stepType="then"] {
                border-left: 4px solid #2196F3;
            }
            
            #bddStep[alternate="true"] {
                background-color: #2a2a2a;
            }
            
            #bddStep:hover {
                background-color: #303030;
            }
            
            #bddStep[stepType="given"]:hover {
                border-color: #66BB6A;
            }
            
            #bddStep[stepType="when"]:hover {
                border-color: #FFB74D;
            }
            
            #bddStep[stepType="then"]:hover {
                border-color: #64B5F6;
            }
            
            #stepType {
                font-weight: bold;
                font-size: 11px;
                min-width: 50px;
                text-transform: uppercase;
            }
            
            #stepType[stepClass="given"] {
                color: #4CAF50; /* Green for Given */
            }
            
            #stepType[stepClass="when"] {
                color: #FF9800; /* Orange for When */
            }
            
            #stepType[stepClass="then"] {
                color: #2196F3; /* Blue for Then */
            }
            
            #stepType[stepClass="notes"] {
                color: #9C27B0; /* Purple for Notes */
            }
            
            #stepContent {
                color: #e0e0e0;
                font-size: 12px;
                line-height: 1.5;
            }
            
            #stepContent[stepClass="given"] {
                color: #e8f5e8;
                border-left: 3px solid #4CAF50;
                padding-left: 8px;
            }
            
            #stepContent[stepClass="when"] {
                color: #fff3e0;
                border-left: 3px solid #FF9800;
                padding-left: 8px;
            }
            
            #stepContent[stepClass="then"] {
                color: #e3f2fd;
                border-left: 3px solid #2196F3;
                padding-left: 8px;
            }
            
            #stepContent[stepClass="notes"] {
                color: #f3e5f5;
                border-left: 3px solid #9C27B0;
                padding-left: 8px;
                font-style: italic;
            }
            
            #scenarioHeader {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #333333, stop: 1 #3a3a3a);
                border: 1px solid #3c3c3c;
                border-radius: 8px 8px 0 0;
            }
            
            #scenarioTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            
            #stepsContainer {
                background-color: transparent;
                border: 1px solid #3c3c3c;
                border-top: none;
                border-radius: 0 0 8px 8px;
            }
            
            #notesFrame {
                background-color: #2a2a2a;
                border-top: 1px solid #444;
            }
        """)
        
        self.theme_button.setText("🌙")
    
    def _apply_light_theme(self):
        """Apply light theme styling"""
        self.setStyleSheet("""
            #bddToolbar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            
            #themeButton {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 6px 10px;
                color: #495057;
                font-size: 12px;
                font-weight: bold;
            }
            
            #themeButton:hover {
                background-color: #e9ecef;
                border-color: #2196f3;
            }
            
            #themeButton:pressed {
                background-color: #f1f3f4;
            }
            
            #bddScrollArea {
                background-color: #ffffff;
                border: none;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            #bddContainer {
                background-color: #ffffff;
            }
            
            #bddStep {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin: 3px 0;
            }
            
            #bddStep[stepType="given"] {
                border-left: 4px solid #2E7D32;
                background-color: #f1f8e9;
            }
            
            #bddStep[stepType="when"] {
                border-left: 4px solid #E65100;
                background-color: #fff3e0;
            }
            
            #bddStep[stepType="then"] {
                border-left: 4px solid #1565C0;
                background-color: #e3f2fd;
            }
            
            #bddStep[alternate="true"] {
                background-color: #f1f3f4;
            }
            
            #bddStep:hover {
                border-color: #007bff;
            }
            
            #bddStep[stepType="given"]:hover {
                border-color: #4CAF50;
            }
            
            #bddStep[stepType="when"]:hover {
                border-color: #FF9800;
            }
            
            #bddStep[stepType="then"]:hover {
                border-color: #2196F3;
            }
            
            #stepType {
                font-weight: bold;
                font-size: 11px;
                min-width: 50px;
                text-transform: uppercase;
            }
            
            #stepType[stepClass="given"] {
                color: #2E7D32; /* Dark Green for Given */
            }
            
            #stepType[stepClass="when"] {
                color: #E65100; /* Dark Orange for When */
            }
            
            #stepType[stepClass="then"] {
                color: #1565C0; /* Dark Blue for Then */
            }
            
            #stepType[stepClass="notes"] {
                color: #6A1B9A; /* Dark Purple for Notes */
            }
            
            #stepContent {
                color: #212529;
                font-size: 12px;
                line-height: 1.5;
            }
            
            #stepContent[stepClass="given"] {
                color: #1b5e20;
                border-left: 3px solid #2E7D32;
                padding-left: 8px;
                background-color: #f1f8e9;
            }
            
            #stepContent[stepClass="when"] {
                color: #e65100;
                border-left: 3px solid #E65100;
                padding-left: 8px;
                background-color: #fff3e0;
            }
            
            #stepContent[stepClass="then"] {
                color: #1565C0;
                border-left: 3px solid #1565C0;
                padding-left: 8px;
                background-color: #e3f2fd;
            }
            
            #stepContent[stepClass="notes"] {
                color: #6A1B9A;
                border-left: 3px solid #6A1B9A;
                padding-left: 8px;
                font-style: italic;
                background-color: #f3e5f5;
            }
            
            #scenarioHeader {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #e9ecef, stop: 1 #f8f9fa);
                border: 1px solid #dee2e6;
                border-radius: 8px 8px 0 0;
            }
            
            #scenarioTitle {
                color: #212529;
                font-size: 14px;
                font-weight: bold;
            }
            
            #stepsContainer {
                background-color: transparent;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 8px 8px;
            }
            
            #notesFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        self.theme_button.setText("☀️")
    
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_theme = not self.is_dark_theme
        self._apply_theme()
    
    def set_bdd_content(self, bdd_content: str):
        """Set BDD content and update the view"""
        self.scenarios = self._parse_bdd_content(bdd_content)
        self._update_view()
    
    def _parse_bdd_content(self, content: str) -> List[Dict]:
        """Parse BDD content into scenarios"""
        scenarios = []
        sections = re.split(r'\n(?:---\n)?(?=Scenario:)', content)
        
        for section in sections:
            section = section.strip()
            if section and section.startswith('Scenario:'):
                scenario = self._parse_single_scenario(section)
                if scenario:
                    scenarios.append(scenario)
        
        return scenarios
    
    def _parse_single_scenario(self, content: str) -> Optional[Dict]:
        """Parse a single BDD scenario with numbered steps"""
        lines = content.split('\n')
        if not lines:
            return None
        
        scenario = {
            'title': '',
            'given': [],
            'when': [],
            'then': [],
            'notes': ''
        }
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Scenario:'):
                scenario['title'] = line[9:].strip()
            elif line.startswith('Given '):
                content = line[5:].strip()
                # Extract number prefix if present
                match = re.match(r'^(\d+[、.]\s*)(.*)', content)
                if match:
                    number = match.group(1)
                    step_content = match.group(2)
                    scenario['given'].append({'content': step_content, 'number': number})
                else:
                    scenario['given'].append({'content': content, 'number': ''})
            elif line.startswith('When '):
                content = line[5:].strip()
                # Extract number prefix if present
                match = re.match(r'^(\d+[、.]\s*)(.*)', content)
                if match:
                    number = match.group(1)
                    step_content = match.group(2)
                    scenario['when'].append({'content': step_content, 'number': number})
                else:
                    scenario['when'].append({'content': content, 'number': ''})
            elif line.startswith('Then '):
                content = line[5:].strip()
                # Extract number prefix if present
                match = re.match(r'^(\d+[、.]\s*)(.*)', content)
                if match:
                    number = match.group(1)
                    step_content = match.group(2)
                    scenario['then'].append({'content': step_content, 'number': number})
                else:
                    scenario['then'].append({'content': content, 'number': ''})
            elif line.startswith('And '):
                content = line[4:].strip()
                # Extract number prefix if present
                match = re.match(r'^(\d+[、.]\s*)(.*)', content)
                if match:
                    number = match.group(1)
                    step_content = match.group(2)
                else:
                    number = ''
                    step_content = content
                
                # Determine which section this "And" belongs to
                if scenario['when']:
                    if not scenario['then']:
                        scenario['when'].append({'content': step_content, 'number': number})
                    else:
                        scenario['then'].append({'content': step_content, 'number': number})
                elif scenario['given']:
                    scenario['given'].append({'content': step_content, 'number': number})
            elif line.startswith('# Notes:'):
                scenario['notes'] = line[9:].strip()
        
        return scenario if scenario['title'] else None
    
    def _update_view(self):
        """Update the view with current scenarios"""
        # Clear existing widgets
        while self.container_layout.count() > 1:  # Keep the stretch at the end
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add scenario widgets
        for i, scenario in enumerate(self.scenarios, 1):
            scenario_widget = BDDScenarioWidget(scenario, i, self.container_widget)
            self.container_layout.insertWidget(i - 1, scenario_widget)
    
    def clear(self):
        """Clear all content"""
        self.scenarios = []
        self._update_view()
    
    def get_scenario_count(self) -> int:
        """Get the number of scenarios"""
        return len(self.scenarios)
    
    # Keyword highlighting methods
    def set_highlight_keywords(self, keywords: list):
        """Set the list of keywords to highlight"""
        self.keyword_highlighter.set_keywords(keywords)
        if not keywords:
            # If no keywords, clear all highlighting
            self._clear_all_highlighting()
        else:
            # Apply highlighting
            self._apply_keyword_highlighting()
    
    def add_highlight_keyword(self, keyword: str):
        """Add a single keyword for highlighting"""
        self.keyword_highlighter.add_keyword(keyword)
        self._apply_keyword_highlighting()
    
    def remove_highlight_keyword(self, keyword: str):
        """Remove keyword highlighting"""
        self.keyword_highlighter.remove_keyword(keyword)
        self._apply_keyword_highlighting()
    
    def clear_highlight_keywords(self):
        """Clear all keyword highlighting"""
        self.keyword_highlighter.clear_keywords()
        self._apply_keyword_highlighting()
    
    def set_highlight_color(self, color: QColor):
        """Set highlight color"""
        self.keyword_highlighter.set_highlight_color(color)
        self._apply_keyword_highlighting()
    
    def get_highlight_keywords(self) -> list:
        """Get the current list of keywords"""
        return self.keyword_highlighter.keywords.copy()
    
    def _apply_keyword_highlighting(self):
        """Apply keyword highlighting in BDD view"""
        # Iterate through all scenarios and steps, apply or clear highlighting
        for i in range(self.container_layout.count()):
            item = self.container_layout.itemAt(i)
            widget = item.widget()
            
            if isinstance(widget, BDDScenarioWidget):
                self._highlight_scenario_widget(widget)
    
    def _clear_all_highlighting(self):
        """Clear all highlighting, restore plain text"""
        for i in range(self.container_layout.count()):
            item = self.container_layout.itemAt(i)
            widget = item.widget()
            
            if isinstance(widget, BDDScenarioWidget):
                self._clear_scenario_highlighting(widget)
    
    def _clear_scenario_highlighting(self, scenario_widget):
        """Clear highlighting for a single scenario"""
        # Find scenario title
        for child in scenario_widget.findChildren(QLabel, "scenarioTitle"):
            from PySide6.QtGui import QTextDocument
            doc = QTextDocument()
            doc.setHtml(child.text())
            plain_text = doc.toPlainText()
            child.setTextFormat(Qt.PlainText)  # Restore plain text
            child.setText(plain_text)
        
        # Find step content
        for step_widget in scenario_widget.findChildren(BDDStepWidget):
            self._clear_step_highlighting(step_widget)
    
    def _clear_step_highlighting(self, step_widget):
        """Clear highlighting for a single step"""
        for child in step_widget.findChildren(QLabel, "stepContent"):
            if hasattr(child, 'text'):
                from PySide6.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(child.text())
                plain_text = doc.toPlainText()
                child.setTextFormat(Qt.PlainText)  # Restore plain text
                child.setText(plain_text)
    
    def _highlight_scenario_widget(self, scenario_widget):
        """Apply keyword highlighting to a single scenario widget"""
        # Find scenario title
        for child in scenario_widget.findChildren(QLabel, "scenarioTitle"):
            original_text = child.text()
            # Remove previous HTML tags
            from PySide6.QtGui import QTextDocument
            doc = QTextDocument()
            doc.setHtml(original_text)
            plain_text = doc.toPlainText()
            
            highlighted_text = self.keyword_highlighter.highlight_html_content(plain_text)
            child.setTextFormat(Qt.RichText)  # Enable rich text
            child.setText(highlighted_text)
        
        # Find step content
        for step_widget in scenario_widget.findChildren(BDDStepWidget):
            self._highlight_step_widget(step_widget)
    
    def _highlight_step_widget(self, step_widget):
        """Apply keyword highlighting to a single step widget"""
        for child in step_widget.findChildren(QLabel, "stepContent"):
            if hasattr(child, 'text'):
                original_text = child.text()
                # Remove previous HTML tags
                from PySide6.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(original_text)
                plain_text = doc.toPlainText()
                
                highlighted_text = self.keyword_highlighter.highlight_html_content(plain_text)
                child.setTextFormat(Qt.RichText)  # Enable rich text
                child.setText(highlighted_text)