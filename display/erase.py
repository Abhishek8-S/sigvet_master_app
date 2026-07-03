from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import os
import shutil

class EraseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        from core.config_loader import get_config
        import subprocess
        config = get_config()
        self.target_dirs = config.get('paths', {}).get('erase', {}).get('target_dirs', [
            "/imgarc/sigvet/tempfs/",
            "/imgarc/sigvet/data/"
        ])
        self.sudo_password = config.get('app', {}).get('sudo_password', 'sigvet123')
        self._subprocess = subprocess
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        layout.addStretch(1)
        
        title = QLabel("Erase Data Tool")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px;")
        layout.addWidget(title)
        
        self.lbl_status = QLabel("Ready to erase data.", objectName="SubHeader")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        layout.addSpacing(20)
        
        self.btn_erase = QPushButton("ERASE DATA")
        self.btn_erase.setObjectName("CancelButton") # Red button for destructive action
        self.btn_erase.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_erase.setFixedSize(250, 50)
        self.btn_erase.clicked.connect(self.perform_erase)
        layout.addWidget(self.btn_erase, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_back = QPushButton("BACK TO MENU")
        self.btn_back.setObjectName("StartButton")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedSize(250, 50)
        layout.addWidget(self.btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch(1)

    def log_status(self, message, color="#a6adc8"):
        self.lbl_status.setText(message)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600;")

    def perform_erase(self):
        reply = QMessageBox.warning(
            self, 'Confirm Erase', 
            "Are you sure you want to permanently erase all data in tempfs and data folders?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = True
            errors = []
            for dir_path in self.target_dirs:
                # Use sudo -S find + rm to handle privileged paths
                cmd = (
                    f"echo {self.sudo_password} | sudo -S "
                    f"find {dir_path} -mindepth 1 -delete"
                )
                result = self._subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    success = False
                    errors.append(result.stderr.strip() or f"Failed on {dir_path}")

            if success:
                self.log_status("Data successfully erased.", "#a6e3a1")
            else:
                self.log_status(f"Some errors occurred:\n" + "\n".join(errors), "#f38ba8")

