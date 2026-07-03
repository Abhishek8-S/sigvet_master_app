from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import os
import shutil
from datetime import datetime
import subprocess

class BackupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        from core.config_loader import get_config
        config = get_config()
        backup_cfg = config.get('paths', {}).get('backup', {})
        self.source_dir = backup_cfg.get('source_dir', "/imgarc/sigvet/")
        self.db_file_name = backup_cfg.get('db_file_name', "order_store.db")
        self.source_path = os.path.join(self.source_dir, self.db_file_name)
        self.backup_base_dir = backup_cfg.get('backup_base_dir', "/home/sigvet/Downloads/")
        self.sudo_password = config.get('app', {}).get('sudo_password', 'sigvet123')
        
        self.setup_ui()
        self.setup_test_environment()

    def setup_test_environment(self):
        try:
            os.makedirs(self.source_dir, exist_ok=True)
            os.makedirs(self.backup_base_dir, exist_ok=True)
            if not os.path.exists(self.source_path):
                with open(self.source_path, "w") as f:
                    f.write("This is a dummy order database.")
        except OSError:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        layout.addStretch(1)
        
        title = QLabel("Order Backup Tool")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px;")
        layout.addWidget(title)
        
        self.lbl_status = QLabel("Ready to back up orders.", objectName="SubHeader")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        layout.addSpacing(20)
        
        self.btn_backup = QPushButton("BACK UP ORDERS")
        self.btn_backup.setObjectName("StartButton")
        self.btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backup.setFixedSize(250, 50)
        self.btn_backup.clicked.connect(self.perform_backup)
        layout.addWidget(self.btn_backup, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_back = QPushButton("BACK TO MENU")
        self.btn_back.setObjectName("CancelButton")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedSize(250, 50)
        layout.addWidget(self.btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch(1)

    def log_status(self, message, color="#a6adc8"):
        self.lbl_status.setText(message)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600;")

    def perform_backup(self):
        try:
            if not os.path.exists(self.source_path):
                # Try listing with sudo to check if it exists but lacks read perms
                check = subprocess.run(
                    f"echo {self.sudo_password} | sudo -S ls {self.source_path}",
                    shell=True, capture_output=True, text=True
                )
                if check.returncode != 0:
                    self.log_status(f"Error: Database not found at {self.source_path}.\nPlease restart the system.", "#f38ba8")
                    return

            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_folder_name = f"{current_time}_order_store"
            full_backup_path = os.path.join(self.backup_base_dir, backup_folder_name)

            os.makedirs(full_backup_path, exist_ok=True)
            destination_file = os.path.join(full_backup_path, self.db_file_name)

            # Use sudo -S to copy from privileged path
            copy_cmd = f"echo {self.sudo_password} | sudo -S cp {self.source_path} {destination_file}"
            result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log_status(f"Copy failed: {result.stderr.strip()}", "#f38ba8")
                return

            # Remove source with sudo
            rm_cmd = f"echo {self.sudo_password} | sudo -S rm -f {self.source_path}"
            subprocess.run(rm_cmd, shell=True)

            self.log_status(f"Backup completed successfully!\nSaved to: {full_backup_path}", "#a6e3a1")

            reply = QMessageBox.question(
                self, 'Restart Device?',
                "Backup completed successfully.\n\nDo you want to restart the device now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    cmd = f"echo {self.sudo_password} | sudo -S reboot"
                    subprocess.run(cmd, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "Reboot Failed", f"Could not restart the device.\nError: {e}")

        except Exception as e:
            self.log_status(f"An unexpected error occurred.\n{e}", "#f38ba8")

