import os
import json
import time
from typing import Dict, List, Any
from PySide6.QtCore import QObject, QTimer


class WorkspaceManager(QObject):
    """Workspace manager, responsible for auto-saving and restoring workspace state"""
    
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.teshi_dir = os.path.join(project_path, '.teshi')
        self.workspace_file = os.path.join(self.teshi_dir, 'workspace.json')
        self.main_window = None
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_workspace)
        self.save_delay = 2000  # Save after 2 seconds
        
        # Ensure .teshi directory exists
        os.makedirs(self.teshi_dir, exist_ok=True)
    
    def set_main_window(self, main_window):
        """Set main window reference"""
        self.main_window = main_window
    
    def trigger_save(self):
        """Trigger delayed save"""
        self.save_timer.stop()
        self.save_timer.start(self.save_delay)
    
    def get_workspace_state(self, main_window) -> Dict[str, Any]:
        """Get current workspace state"""
        workspace_data = {
            'timestamp': time.time(),
            'window_geometry': {
                'x': main_window.x(),
                'y': main_window.y(),
                'width': main_window.width(),
                'height': main_window.height(),
                'maximized': main_window.isMaximized()
            },
            'open_tabs': [],
            'current_tab_index': main_window.tabs.currentIndex() if hasattr(main_window, 'tabs') else -1,
            'dock_states': {}
        }
        
        # Save open tabs
        if hasattr(main_window, 'tabs'):
            for i in range(main_window.tabs.count()):
                widget = main_window.tabs.widget(i)
                if hasattr(widget, 'filePath'):
                    workspace_data['open_tabs'].append({
                        'file_path': widget.filePath,
                        'is_dirty': widget.dirty if hasattr(widget, 'dirty') else False
                    })
        
        # Save dock widget states
        if hasattr(main_window, 'project_dock'):
            workspace_data['dock_states']['project'] = main_window.project_dock.isVisible()
            
            # Save project explorer expanded state
            if hasattr(main_window, 'explorer'):
                workspace_data['project_explorer'] = {
                    'expanded_folders': main_window.explorer.get_expanded_state()
                }
        
        return workspace_data
    
    def save_workspace(self, main_window):
        """Save workspace immediately"""
        workspace_data = self.get_workspace_state(main_window)
        try:
            with open(self.workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2, ensure_ascii=False)
            print(f"Workspace saved to: {self.workspace_file}")
        except Exception as e:
            print(f"Failed to save workspace: {e}")
    
    def _save_workspace(self):
        """Save method triggered by timer"""
        if self.main_window:
            self.save_workspace(self.main_window)
    
    def load_workspace(self) -> Dict[str, Any]:
        """Load workspace state"""
        if not os.path.exists(self.workspace_file):
            return {}
        
        try:
            with open(self.workspace_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load workspace: {e}")
            return {}
    
    def restore_workspace(self, main_window):
        """Restore workspace state"""
        workspace_data = self.load_workspace()
        if not workspace_data:
            return
        
        # Restore window geometry
        geometry = workspace_data.get('window_geometry', {})
        if geometry:
            main_window.setGeometry(
                geometry.get('x', 100),
                geometry.get('y', 100),
                geometry.get('width', 1200),
                geometry.get('height', 800)
            )
            if geometry.get('maximized', False):
                main_window.showMaximized()
        
        # Restore dock widget states
        dock_states = workspace_data.get('dock_states', {})
        if hasattr(main_window, 'project_dock') and 'project' in dock_states:
            if dock_states['project']:
                main_window.project_dock.show()
            else:
                main_window.project_dock.hide()
        
        # Restore project explorer state
        project_explorer = workspace_data.get('project_explorer', {})
        if project_explorer and hasattr(main_window, 'explorer'):
            expanded_folders = project_explorer.get('expanded_folders', [])
            # Use QTimer to delay restoration until the tree is fully populated
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: main_window.explorer.set_expanded_state(expanded_folders))
        
        # Restore open tabs
        open_tabs = workspace_data.get('open_tabs', [])
        for tab_data in open_tabs:
            file_path = tab_data.get('file_path')
            if file_path and os.path.exists(file_path):
                main_window.open_file_in_tab(file_path)
        
        # Restore current tab
        current_tab_index = workspace_data.get('current_tab_index', -1)
        if current_tab_index >= 0 and current_tab_index < main_window.tabs.count():
            main_window.tabs.setCurrentIndex(current_tab_index)
    
    def clear_workspace(self):
        """Clear workspace state"""
        if os.path.exists(self.workspace_file):
            try:
                os.remove(self.workspace_file)
                print(f"Cleared workspace state: {self.workspace_file}")
            except Exception as e:
                print(f"Failed to clear workspace state: {e}")