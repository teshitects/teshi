import json
import os
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QPushButton, QSpinBox, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QFrame, QGroupBox
)
from PySide6.QtCore import Qt
from teshi.utils.resource_path import resource_path


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(resource_path("assets/teshi_icon64.png")))
        self.setFixedSize(800, 600)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QListWidget {
                background-color: #3c3f41;
                border: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4c5255;
            }
            QListWidget::item:hover {
                background-color: #45494d;
            }
            QGroupBox {
                border: 1px solid #4c5255;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #a9b7c6;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #4c5255;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QPushButton {
                background-color: #365880;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a6a94;
            }
            QPushButton:pressed {
                background-color: #2d4a6d;
            }
            QSpinBox {
                background-color: #3c3f41;
                border: 1px solid #4c5255;
                border-radius: 4px;
                padding: 4px;
                color: #a9b7c6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4c5255;
                width: 16px;
            }
        """)
        
        # Load settings
        self.settings = self._load_settings()
        
        self._setup_ui()
        
    def _load_settings(self):
        """Load settings from config file"""
        config_file = os.path.join(os.path.expanduser('~'), '.teshi', 'settings.json')
        default_settings = {
            'font_size': 12,
            'editor_font_size': 12,
            'ui_font_size': 12
        }
        
        try:
            if os.path.exists(config_file):
                print(f"[Settings] Loading settings from: {config_file}")
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                    print(f"[Settings] Loaded settings: {default_settings}")
            else:
                print(f"[Settings] Settings file not found: {config_file}, using defaults")
        except Exception as e:
            print(f"[Settings] Error loading settings: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save settings to config file"""
        config_dir = os.path.join(os.path.expanduser('~'), '.teshi')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'settings.json')
        
        try:
            print(f"[Settings] Saving settings to: {config_file}")
            print(f"[Settings] Settings to save: {self.settings}")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            print(f"[Settings] Settings saved successfully")
            # Verify the file was written
            if os.path.exists(config_file):
                print(f"[Settings] File exists and size: {os.path.getsize(config_file)} bytes")
            else:
                print(f"[Settings] Warning: File does not exist after save!")
        except Exception as e:
            print(f"[Settings] Error saving settings: {e}")
    
    def _setup_ui(self):
        """Setup the settings dialog UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - categories
        self.categories = QListWidget()
        self.categories.setFixedWidth(200)
        self.categories.setStyleSheet("border-right: 1px solid #4c5255;")

        # Right panel container
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Right panel - content
        self.content = QStackedWidget()

        # Add categories and pages
        self._add_category_page("Appearance", self._create_appearance_page())
        self._add_category_page("Editor", self._create_editor_page())

        right_layout.addWidget(self.content)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self._apply_settings)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._accept_and_close)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(apply_button)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        right_layout.addLayout(button_layout)

        main_layout.addWidget(self.categories)
        main_layout.addWidget(right_container)

        # Select first category
        self.categories.setCurrentRow(0)
    
    def _add_category_page(self, name, page):
        """Add a category and its page"""
        item = QListWidgetItem(name)
        self.categories.addItem(item)
        self.content.addWidget(page)
        
        # Connect category selection
        self.categories.currentRowChanged.connect(self.content.setCurrentIndex)
    
    def _create_appearance_page(self):
        """Create appearance settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Appearance")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        layout.addSpacing(20)
        
        # Font size settings group
        font_group = QGroupBox("Font Size")
        font_layout = QVBoxLayout()
        
        # UI Font Size
        ui_font_layout = QHBoxLayout()
        ui_font_label = QLabel("UI Font Size:")
        self.ui_font_spinbox = QSpinBox()
        self.ui_font_spinbox.setRange(8, 24)
        self.ui_font_spinbox.setValue(self.settings.get('ui_font_size', 12))
        ui_font_layout.addWidget(ui_font_label)
        ui_font_layout.addStretch()
        ui_font_layout.addWidget(self.ui_font_spinbox)
        font_layout.addLayout(ui_font_layout)
        
        # Preview
        preview_label = QLabel("UI Font Size Preview")
        preview_label.setStyleSheet(f"font-size: {self.ui_font_spinbox.value()}px; color: #a9b7c6;")
        self.ui_font_preview = preview_label
        font_layout.addWidget(preview_label)
        
        # Connect spinbox to preview
        self.ui_font_spinbox.valueChanged.connect(
            lambda v: preview_label.setStyleSheet(f"font-size: {v}px; color: #a9b7c6;")
        )
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        layout.addStretch()
        
        return page
    
    def _create_editor_page(self):
        """Create editor settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Editor")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        layout.addSpacing(20)
        
        # Editor font size settings group
        font_group = QGroupBox("Font Size")
        font_layout = QVBoxLayout()
        
        # Editor Font Size with slider
        editor_font_label = QLabel("Editor Font Size:")
        font_layout.addWidget(editor_font_label)
        
        slider_layout = QHBoxLayout()
        self.editor_font_slider = QSlider(Qt.Horizontal)
        self.editor_font_slider.setRange(8, 24)
        self.editor_font_slider.setValue(self.settings.get('editor_font_size', 12))
        self.editor_font_slider.setTickPosition(QSlider.TicksBelow)
        self.editor_font_slider.setTickInterval(1)
        
        self.editor_font_value = QLabel(str(self.settings.get('editor_font_size', 12)))
        self.editor_font_value.setFixedWidth(30)
        
        slider_layout.addWidget(self.editor_font_slider)
        slider_layout.addWidget(self.editor_font_value)
        font_layout.addLayout(slider_layout)
        
        # Connect slider to value label
        self.editor_font_slider.valueChanged.connect(
            lambda v: self.editor_font_value.setText(str(v))
        )
        
        # Preview
        preview_label = QLabel("Editor Font Size Preview - This is a sample text to show how the font will appear.")
        preview_label.setStyleSheet(f"font-family: Consolas, monospace; font-size: {self.editor_font_slider.value()}px; color: #a9b7c6;")
        preview_label.setWordWrap(True)
        self.editor_font_preview = preview_label
        font_layout.addWidget(preview_label)
        
        # Connect slider to preview
        self.editor_font_slider.valueChanged.connect(
            lambda v: preview_label.setStyleSheet(f"font-family: Consolas, monospace; font-size: {v}px; color: #a9b7c6;")
        )
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        layout.addStretch()
        
        return page
    
    def _apply_settings(self):
        """Apply the settings"""
        # Update settings dictionary
        self.settings['ui_font_size'] = self.ui_font_spinbox.value()
        self.settings['editor_font_size'] = self.editor_font_slider.value()
        self.settings['font_size'] = self.editor_font_slider.value()
        
        print(f"[Settings] Applying settings: {self.settings}")
        
        # Save to file
        self._save_settings()
        
        # Apply to main window if parent is MainWindow
        parent = self.parent()
        print(f"[Settings] Parent: {parent}, has apply_settings: {hasattr(parent, 'apply_settings')}")
        if hasattr(parent, 'apply_settings'):
            parent.apply_settings(self.settings)
        
        self.show_message("Settings applied successfully!")
    
    def _accept_and_close(self):
        """Apply settings and close dialog"""
        self._apply_settings()
        self.accept()
    
    def show_message(self, message):
        """Show a temporary message"""
        from PySide6.QtWidgets import QStatusBar
        if self.parent():
            main_window = self.parent()
            if hasattr(main_window, 'show_message'):
                main_window.show_message(message, 3000)
