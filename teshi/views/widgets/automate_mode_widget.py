import os
import sys
import uuid
import datetime
from pathlib import Path

from teshi.utils.logger import get_logger

from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtCore import QSettings, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QListWidget, QTextEdit, QPushButton, QFrame, QMessageBox, QApplication
)
from PySide6.QtGui import QColor, QAction

from teshi.controllers.automate_controller import AutomateController
from teshi.models.jupyter_node_model import JupyterNodeModel
from teshi.views.widgets.automate_widget import NodeSketchpadView, NodeSketchpadScene, JupyterGraphNode
from teshi.views.widgets.component.automate_connection_item import ConnectionItem
from teshi.config.automate_editor_config import AutomateEditorConfig
from teshi.views.widgets.automate_browser_widget import AutomateBrowserWidget
from teshi.views.widgets.component.python_highlighter import PythonHighlighter

class RawCodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_text = ""
        self.save_btn_ref = None

    def set_text_with_original(self, text):
        self.setPlainText(text)
        self.original_text = text

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Check if content changed
        if self.toPlainText() != self.original_text:
            # Defer check to allow focus to settle (e.g. if moving to Save button)
            QtCore.QTimer.singleShot(50, self.check_abandon)

    def check_abandon(self):
        # If focus moved to the save button, don't show dialog
        if self.save_btn_ref and QApplication.focusWidget() == self.save_btn_ref:
            return

        # If we are not visible (e.g. tab switch hidden us), maybe skip?
        # But requirement says "lose focus".

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save modifications?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Save the changes
            self.save_btn_ref.click()
        else:
            # Revert to original text
            self.setPlainText(self.original_text)


class AutomateModeWidget(QWidget):
    """
    Widget for Automate mode (IPyKernel Script Runner).
    Embedded inside EditorWidget.
    """
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        # Initialize Controller
        self.controller = AutomateController(file_path, parent=self)
        
        # Connect Signals
        self.controller.graph_loaded.connect(self.on_graph_loaded)
        self.controller.node_added.connect(self.on_node_added)
        self.controller.node_updated.connect(self.on_node_updated)
        self.controller.node_removed.connect(self.on_node_removed)
        self.controller.execution_status_changed.connect(self.on_execution_status_changed)
        self.controller.execution_binding.connect(self.bind_item_msg_id)
        
        self.tab_id = self.controller.tab_id # Use controller's tab_id
        
        self.scene = None
        self.view = None
        self.logger = get_logger()

        self.parent_widget = parent

        self.setup_ui()
        self.controller.load_project() # Triggers graph_loaded


    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Splitter: Canvas (Left/Center) vs Docks (Right/Bottom)
        # To mimic the Dock layout in QMainWindow, we use QSplitters.
        # Layout:
        # ------------------------------
        # |        |       Raw         |
        # | Canvas |-------------------|
        # |        |      Result       |
        # ------------------------------
        # |          Logger            |
        # ------------------------------
        # |         Buttons            |
        # ------------------------------
        
        # Splitter 0: Browser (Left) vs Main (Center+Right)
        self.root_splitter = QSplitter(Qt.Horizontal)
        self.root_splitter.splitterMoved.connect(self._on_splitter_moved)

        # Browser Widget (Left)
        # Assuming we can get project dir from notebook path or passed in.
        # Using notebook_dir as project root for now, or we might need a better way to find root.
        # But 'notebook_dir' is usually just the folder of the current file.
        # Ideally we should use the parent project root if possible.
        # For now, let's use self.notebook_dir as a starting point.
        self.browser_widget = AutomateBrowserWidget(self.controller.notebook_dir, self.controller.node_registry, self)
        self.root_splitter.addWidget(self.browser_widget)


        # Splitter 1: Top (Canvas+Side) vs Bottom (Logger)
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)


        # Splitter 2: Canvas vs Right Side (Raw/Result)
        self.center_splitter = QSplitter(Qt.Horizontal)
        self.center_splitter.splitterMoved.connect(self._on_splitter_moved)

        
        # Canvas Container
        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Right Side Container
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Raw Code Area
        self.right_layout.addWidget(QtWidgets.QLabel("Raw Code"))
        
        # Container for Raw Code + Save Button (Overlay or Layout)
        # Using a layout approach: Editor takes expanding space, Button at bottom right
        self.raw_code_container = QWidget()
        self.raw_code_container_layout = QVBoxLayout(self.raw_code_container)
        self.raw_code_container_layout.setContentsMargins(0, 0, 0, 0)
        self.raw_code_container_layout.setSpacing(2)
        
        self.raw_code_widget = RawCodeEditor()
        self.raw_code_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.raw_code_widget.setFont(AutomateEditorConfig.node_title_font)
        # Dark styling for code editor
        self.raw_code_widget.setStyleSheet(f"background-color: {AutomateEditorConfig.scene_background_color}; color: white;")
        
        # Attach Syntax Highlighter
        self.highlighter = PythonHighlighter(self.raw_code_widget.document())
        
        self.raw_code_widget.textChanged.connect(self._trigger_workspace_save)
        
        self.raw_code_container_layout.addWidget(self.raw_code_widget)
        
        # Save Button Layout (Right Aligned)
        self.save_code_layout = QHBoxLayout()
        self.save_code_layout.addStretch()
        
        self.save_code_button = QPushButton("Save Code")
        self.save_code_button.setCursor(Qt.PointingHandCursor)
        # Make save button more prominent
        self.save_code_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        # Connect later or here? Connected in separate block before, do it here to ensure ref availability
        self.save_code_button.clicked.connect(self.update_graph_node_code)
        
        self.save_code_layout.addWidget(self.save_code_button)
        self.raw_code_container_layout.addLayout(self.save_code_layout)
        
        # Link button ref to editor for focus check
        self.raw_code_widget.save_btn_ref = self.save_code_button
        
        self.right_layout.addWidget(self.raw_code_container)

        
        # Result Area
        self.right_layout.addWidget(QtWidgets.QLabel("Result"))
        self.result_widget = QTextEdit()
        self.result_widget.setReadOnly(True)
        self.result_widget.setFont(AutomateEditorConfig.node_title_font)
        self.result_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.right_layout.addWidget(self.result_widget)
        
        # Add to Center Splitter
        self.center_splitter.addWidget(self.canvas_container)
        self.center_splitter.addWidget(self.right_container)
        
        # Logger removed - now logs to file

        # Add to Main Splitter
        self.main_splitter.addWidget(self.center_splitter)
        
        # Add everything to root
        self.root_splitter.addWidget(self.main_splitter)
        
        # Set default absolute sizes (pixel widths)
        # root_splitter: Browser (Left) vs Main (Right)
        self.root_splitter.setSizes([200, 1000])

        # main_splitter: Center Splitter (now only one child)
        self.main_splitter.setSizes([1000])

        # center_splitter: Canvas (Left) vs Right Side (Raw/Result)
        self.center_splitter.setSizes([850, 350])
        
        layout.addWidget(self.root_splitter)
        
        # Button Group (Bottom)
        self.button_group = QWidget()
        self.button_layout = QHBoxLayout(self.button_group)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        
        
        run_single_node_button = QPushButton("Run Single")
        run_single_node_button.clicked.connect(self.run_single_node_and_parent)
        
        run_button = QPushButton("Run ALL")
        run_button.clicked.connect(self.run_all)
        
        restore_button = QPushButton("Restore Status")
        restore_button.clicked.connect(self.restore)
        
        # self.button_layout.addWidget(save_code_button) # Removed, moved to Raw Code area
        self.button_layout.addWidget(run_single_node_button)
        self.button_layout.addWidget(run_button)
        self.button_layout.addWidget(restore_button)
        self.button_layout.addStretch()
        
        layout.addWidget(self.button_group)


    @Slot()
    def on_graph_loaded(self):
        """Called when controller finishes loading the project data."""
        # 1. Update Browser widget
        # We need topological sort for the browser list. 
        # Controller doesn't expose it directly yet, but we can compute it or ask controller.
        # For now perform logic here as it's view-specific (display order).
        # Actually, let's defer browser update until nodes are in scene or compute from controller nodes.
        pass # Will do at end of function

        # 2. Init Scene and View (if needed)
        # We want to keep view if possible to preserve scroll, but refreshing scene is safer.
        self.scene = NodeSketchpadScene(self)
        self.view = NodeSketchpadView(self.scene, self)
        self.view.setAlignment(Qt.AlignCenter)
        
        # Add view to layout
        if self.canvas_layout.count() > 0:
             self.canvas_layout.itemAt(0).widget().deleteLater()
        self.canvas_layout.addWidget(self.view)

        # 3. Draw Nodes from Controller
        graph_nodes = {}
        # Basic layout strategy: Horizontal line if no position data (handled in controller defaults)
        for uuid, node_model in self.controller.nodes.items():
            rect = JupyterGraphNode(node_model.title, node_model.code)
            # Link the view item to the model object form controller
            rect.data_model = node_model 
            
            rect.setPos(node_model.x, node_model.y)
            # rect.update_input_widgets() # Called in init of node? No, let's call explicit
            rect.update_input_widgets()
            
            # Connect signals
            rect.signals.nodeClicked.connect(self.update_widget)
            self.scene.addItem(rect)
            graph_nodes[uuid] = rect

        # 4. Draw Connections
        for uuid, node_model in self.controller.nodes.items():
            rect = graph_nodes[uuid]
            for child_uuid in node_model.children:
                if child_uuid in graph_nodes:
                    target_rect = graph_nodes[child_uuid]
                    connection = ConnectionItem(rect, target_rect)
                    self.scene.addItem(connection)
                    rect.add_connection(connection)
                    target_rect.add_connection(connection)

        # 5. Update Browser List
        self.update_browser_canvas_nodes()

    @Slot(JupyterNodeModel)
    def on_node_added(self, node_model):
        rect = JupyterGraphNode(node_model.title, node_model.code)
        rect.data_model = node_model
        rect.setPos(node_model.x, node_model.y)
        rect.update_input_widgets()
        rect.signals.nodeClicked.connect(self.update_widget)
        self.scene.addItem(rect)
        self.update_browser_canvas_nodes()

    @Slot(JupyterNodeModel)
    def on_node_updated(self, node_model):
        # find item by uuid
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode) and item.data_model.uuid == node_model.uuid:
                # Update visual properties if needed
                item.setPos(node_model.x, node_model.y)
                if item._title != node_model.title:
                    item.set_title_text(node_model.title)
                # Ensure local data model is updated as well
                item.data_model = node_model
                # input widgets might need refresh
                item.update_input_widgets()
                break

    @Slot(str)
    def on_node_removed(self, uuid):
         for item in self.scene.items():
            if isinstance(item, JupyterGraphNode) and item.data_model.uuid == uuid:
                # Remove connections visuals first
                for conn in item.connections.copy():
                     if self.scene:
                         self.scene.removeItem(conn)
                
                if self.scene:
                    self.scene.removeItem(item)
                break

    @Slot(str, str)
    def on_execution_status_changed(self, msg_id, status_str):
        # Forward to internal logic that updates UI based on status
        # We need to map msg_id to node
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                if getattr(item.data_model, 'msg_id', None) == msg_id:
                     self._update_node_status(item, status_str)

    def update_browser_canvas_nodes(self):
        """Update the execution order list in the browser widget"""
        try:
             # Build graph for topo sort (using UUIDs)
             graph = {item.data_model.uuid: item.data_model.children for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
             
             # Calculate topological order (UUIDs)
             topo_order_uuids = graph_util.topological_sort(graph)
             
             # Map back to Titles for display
             uuid_to_title = {item.data_model.uuid: item.data_model.title for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
             topo_order_titles = [uuid_to_title.get(uuid, "Unknown") for uuid in topo_order_uuids]

             self.browser_widget.update_canvas_nodes(topo_order_titles)
        except Exception as e:
             print(f"Error updating canvas nodes list: {e}")




    def update_widget(self, data_model_dict):
        """Update side panel when a node is clicked"""
        self.raw_code_widget.set_text_with_original(data_model_dict["code"])
        self.result_widget.setText(data_model_dict.get("result", ""))
        # set uuid in tooltip to identify which node is selected
        self.result_widget.setToolTip(data_model_dict['uuid'])
        # Trigger workspace save when node selection changes
        self._trigger_workspace_save()


    def update_graph_node_code(self):
        """Save code from Raw Code widget to the selected node"""
        uuid = self.result_widget.toolTip()
        if not uuid:
            return
        
        self.controller.update_node_code(uuid, self.raw_code_widget.toPlainText())
        
        # Update original text to match saved version (prevent unsaved prompt)
        self.raw_code_widget.original_text = self.raw_code_widget.toPlainText()



    def restore(self):
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                item.set_default_color()
                item.set_default_text()
                item.data_model.last_status = ""
                
    def run_all(self):
        self.restore()
        self.controller.run_all()

    def run_single_node_and_parent(self):
        selected_items = self.scene.selectedItems()
        if not selected_items or not isinstance(selected_items[0], JupyterGraphNode):
            QMessageBox.information(self, "Info", "Please select a node first.")
            return

        self.restore()
        
        target_node = selected_items[0]
        self.controller.run_single(target_node.data_model.uuid)

    def bind_item_msg_id(self, binding):
        """Bind execution message ID to node UUID"""
        # format: msg_id:tab_id#item_uuid
        parts = binding.split(":")
        if len(parts) < 2: return
        msg_id = parts[0]
        
        rest = parts[1]
        if "#" not in rest: return
        t_id, item_id = rest.split("#")
        
        if t_id != self.tab_id: return
        
        self.logger.info(f"Binding: {binding}")
        
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                if item.data_model.uuid == item_id:
                    item.data_model.msg_id = msg_id



    def _update_node_status(self, item, status_str):
        if status_str == "status:busy":
            item.set_color(QColor('yellow'))
            item.data_model.last_status = "status:busy"
        elif status_str.startswith("execute_input"):
            item.set_color(QColor('yellow'))
            item.data_model.last_status = "execute_input"
        elif status_str == "status:idle":
            if item.data_model.last_status != "error":
                item.set_color(QColor('green'))
                item.data_model.last_status = "idle"
        elif status_str.startswith("error"):
            item.set_color(QColor('red'))
            item.data_model.last_status = "error"
            error_msg = status_str.replace("error_:", "")
            item.set_result_text(error_msg.split("\n")[0])
            item.data_model.result = error_msg
            # Update result widget if this node is selected
            if self.result_widget.toolTip() == item.data_model.uuid:
                 self.result_widget.setText(error_msg)
                 # Trigger workspace save when error is updated
                 self._trigger_workspace_save()
        elif status_str.startswith("stream"):

            item.data_model.last_status = "stream"
            stream_msg = status_str.replace("stream:", "")
            item.set_result_text(stream_msg.split("\n")[0])
            item.data_model.result = stream_msg
            if self.result_widget.toolTip() == item.data_model.uuid:
                 self.result_widget.setText(stream_msg)
                 # Trigger workspace save when result is updated
                 self._trigger_workspace_save()

    def get_automate_state(self):

        """Get current Automate interface state for workspace saving"""
        state = {
            'project_nodes': [],
            'execution_order': [],
            'raw_code': '',
            'result': '',
            'selected_node_uuid': self.result_widget.toolTip(),
            'browser_search_text': self.browser_widget.search_bar.text(),
            'splitter_sizes': {
                'root_splitter': self.root_splitter.sizes(),
                'main_splitter': self.main_splitter.sizes(),
                'center_splitter': self.center_splitter.sizes(),
                'browser_splitter': self.browser_widget.splitter.sizes()
            }
        }

        # Save project nodes (from browser widget)
        for i in range(self.browser_widget.project_list.count()):
            item = self.browser_widget.project_list.item(i)
            if item and not item.isHidden():
                state['project_nodes'].append({
                    'title': item.text(),
                    'code': item.data(Qt.UserRole) if item.data(Qt.UserRole) else ''
                })

        # Save execution order (canvas nodes)
        for i in range(self.browser_widget.canvas_list.count()):
            item = self.browser_widget.canvas_list.item(i)
            if item:
                state['execution_order'].append(item.text())

        # Save raw code and result if a node is selected
        if state['selected_node_uuid']:
            state['raw_code'] = self.raw_code_widget.toPlainText()
            state['result'] = self.result_widget.toPlainText()

        return state

    def restore_automate_state(self, state):
        """Restore Automate interface state from workspace"""
        try:
            # Check for global layout state from main window first
            if self.parent_widget:
                main_window = self.parent_widget
                while main_window and not hasattr(main_window, 'workspace_manager'):
                    main_window = main_window.parent()

                if main_window and hasattr(main_window, '_global_automate_layout'):
                    # Apply global layout first (workspace-level settings)
                    self.apply_global_layout_state(main_window._global_automate_layout)

            # Restore browser search text
            if 'browser_search_text' in state:
                self.browser_widget.search_bar.setText(state['browser_search_text'])

            # Restore raw code and result for selected node
            if state.get('selected_node_uuid'):
                self.result_widget.setToolTip(state['selected_node_uuid'])
                if 'raw_code' in state:
                    self.raw_code_widget.setText(state['raw_code'])
                if 'result' in state:
                    self.result_widget.setText(state['result'])

            # Restore splitter sizes with delay to ensure UI is fully loaded
            if 'splitter_sizes' in state:
                from PySide6.QtCore import QTimer
                splitter_sizes = state['splitter_sizes']

                def restore_splitter_sizes():
                    """Restore all splitter sizes"""
                    try:
                        # Restore root splitter (Browser vs Main)
                        if 'root_splitter' in splitter_sizes and len(splitter_sizes['root_splitter']) == 2:
                            sizes = splitter_sizes['root_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.root_splitter.setSizes(sizes)

                        # Restore main splitter (Canvas vs Logger)
                        if 'main_splitter' in splitter_sizes and len(splitter_sizes['main_splitter']) == 2:
                            sizes = splitter_sizes['main_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.main_splitter.setSizes(sizes)

                        # Restore center splitter (Canvas vs Right side)
                        if 'center_splitter' in splitter_sizes and len(splitter_sizes['center_splitter']) == 2:
                            sizes = splitter_sizes['center_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.center_splitter.setSizes(sizes)

                        # Restore browser splitter (Project nodes vs Execution order)
                        if 'browser_splitter' in splitter_sizes and len(splitter_sizes['browser_splitter']) == 2:
                            sizes = splitter_sizes['browser_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.browser_widget.splitter.setSizes(sizes)
                    except Exception as e:
                        print(f"Error restoring splitter sizes: {e}")

                # Use QTimer to delay restoration until UI is fully loaded
                QTimer.singleShot(100, restore_splitter_sizes)

        # Note: Project nodes and execution order are dynamically managed
        # and don't need explicit restoration as they are loaded from the notebook

        except Exception as e:
            print(f"Error restoring Automate state: {e}")


    def _trigger_workspace_save(self):
        """Trigger workspace save through parent widget"""
        if self.parent_widget:
            # Find main window to trigger workspace save
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'workspace_manager'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'workspace_manager'):
                main_window.workspace_manager.trigger_save()

    def get_global_layout_state(self):
        """Get global layout state that should be shared across all automate tabs"""
        return {
            'browser_width': self.root_splitter.sizes()[0] if len(self.root_splitter.sizes()) > 0 else None,
            'result_width': self.center_splitter.sizes()[1] if len(self.center_splitter.sizes()) > 1 else None,
            'logger_height': self.main_splitter.sizes()[1] if len(self.main_splitter.sizes()) > 1 else None
        }

    def apply_global_layout_state(self, state, broadcast=False):
        """Apply global layout state from workspace

        Args:
            state: The layout state to apply
            broadcast: Whether to broadcast the change to other tabs
        """
        if not state:
            return

        # Apply browser width
        if state.get('browser_width') is not None:
            current_sizes = self.root_splitter.sizes()
            if len(current_sizes) == 2:
                total_width = sum(current_sizes)
                new_sizes = [state['browser_width'], total_width - state['browser_width']]
                self.root_splitter.setSizes(new_sizes)

        # Apply result width
        if state.get('result_width') is not None:
            current_sizes = self.center_splitter.sizes()
            if len(current_sizes) == 2:
                total_width = sum(current_sizes)
                new_sizes = [total_width - state['result_width'], state['result_width']]
                self.center_splitter.setSizes(new_sizes)

        # Apply logger height
        if state.get('logger_height') is not None:
            current_sizes = self.main_splitter.sizes()
            if len(current_sizes) == 2:
                total_height = sum(current_sizes)
                new_sizes = [total_height - state['logger_height'], state['logger_height']]
                self.main_splitter.setSizes(new_sizes)

        # Broadcast layout change to all tabs if requested
        if broadcast and self.parent_widget:
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'workspace_manager'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'workspace_manager'):
                # Update the global layout in main window
                main_window._global_automate_layout = self.get_global_layout_state()
                # Notify other tabs through workspace manager
                main_window.workspace_manager.trigger_save()

    def _on_splitter_moved(self, pos, index):
        """Handle splitter move events for global layout updates"""
        # First, trigger regular workspace save
        self._trigger_workspace_save()

        # Then, if this is the active tab, update global layout and broadcast to other tabs
        if self.parent_widget:
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'tabs'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'tabs'):
                # Check if this widget is the current active tab
                if main_window.tabs.currentWidget() == self:
                    # Update global layout
                    global_layout = self.get_global_layout_state()
                    main_window._global_automate_layout = global_layout

                    # Apply to all other automate tabs (with broadcast=False to avoid recursion)
                    for i in range(main_window.tabs.count()):
                        widget = main_window.tabs.widget(i)
                        if widget and widget != self and hasattr(widget, 'apply_global_layout_state'):
                            widget.apply_global_layout_state(global_layout, broadcast=False)


