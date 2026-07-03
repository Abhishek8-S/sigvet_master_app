from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QCheckBox, QPushButton)
from display.components import ReportDialog

class TestRowWidget(QWidget):
    """
    Represents a single test row in the sidebar list.
    Contains: [Checkbox] [Name] ... [Info Button]
    """
    def __init__(self, test_instance, parent_window):
        super().__init__()
        self.test_instance = test_instance 
        self.test_type = type(test_instance)
        self.parent_window = parent_window
        self.result_data = None
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Checkbox
        self.checkbox = QCheckBox(test_instance.name)
        self.checkbox.setToolTip(test_instance.description)
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(parent_window.check_start_button_state)
        
        # Info Button (Initially Disabled)
        self.info_btn = QPushButton("i")
        self.info_btn.setObjectName("InfoButton")
        self.info_btn.setFixedSize(24, 24)
        self.info_btn.setEnabled(False)
        self.info_btn.clicked.connect(self.show_report)
        
        layout.addWidget(self.checkbox)
        layout.addStretch()
        layout.addWidget(self.info_btn)
        
    def unlock_report(self, data):
        self.result_data = data
        self.info_btn.setEnabled(True)
    
    def show_report(self):
        if self.result_data: 
            # Import locally to avoid circular import issues if any
            from display.components import ReportDialog
            dlg = ReportDialog(self.test_instance.name, self.result_data, self.parent_window)
            dlg.exec()