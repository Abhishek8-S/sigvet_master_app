from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QScrollArea, 
                             QStackedWidget, QFrame, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QIcon, QScreen

from core.config import CONFIG, apply_device_profile, BENCHMARK_STANDARDS
from core.loader import load_tests_from_folder
from core.worker import BenchmarkWorker
from display.splash import SplashScreen
from display.components import GlobalReportDialog, ToggleSwitch # Added ToggleSwitch
from display.row_widget import TestRowWidget
from display.device_selector import DeviceSelector
from display.menu import MainMenu
from display.backup import BackupWidget
from display.erase import EraseWidget
from display.db_editor import DBEditorWidget
from display.hardware_control import HardwareControlWidget
from display.xy_stage import XYStageWidget
from display.animated_stack import AnimatedStackedWidget
from display.phone_numpad import PhoneNumpadDialog
import os
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sigvet Assistance App")
        
        # Robust Icon Loading
        # Try finding assets relative to this file's parent directory (project root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'icon.png') # Changed to root based on user info
        
        # If not in root, check assets folder (standard structure)
        if not os.path.exists(icon_path):
             icon_path = os.path.join(base_dir, 'assets', 'icon.png')

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon not found at {icon_path}")
        
        self.worker = None
        self.stack = AnimatedStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Wrap splash in a centering container so it appears centred on the
        # maximized window rather than being stretched to fill it.
        splash_container = QWidget()
        splash_layout = QVBoxLayout(splash_container)
        splash_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.setContentsMargins(0, 0, 0, 0)
        self.splash = SplashScreen()
        self.splash.finished.connect(self.show_main_menu)
        splash_layout.addWidget(self.splash)
        self.stack.addWidget(splash_container)  # Index 0
        
        self.main_menu = MainMenu()
        self.main_menu.btn_compute.clicked.connect(self.show_device_selector)
        self.main_menu.btn_backup.clicked.connect(self.show_backup_view)
        self.main_menu.btn_db_editor.clicked.connect(self.show_db_editor_view)
        self.main_menu.btn_hw_control.clicked.connect(self.show_hw_control_view)
        self.main_menu.btn_xy_stage.clicked.connect(self.show_xy_stage_view)
        self.main_menu.btn_erase.clicked.connect(self.show_erase_view)
        self.stack.addWidget(self.main_menu) # Index 1
        
        self.dashboard = QWidget()
        self.stack.addWidget(self.dashboard) # Index 2
        
        self.backup_view = BackupWidget()
        self.backup_view.btn_back.clicked.connect(self.show_main_menu)
        self.stack.addWidget(self.backup_view) # Index 3
        
        self.erase_view = EraseWidget()
        self.erase_view.btn_back.clicked.connect(self.show_main_menu)
        self.stack.addWidget(self.erase_view) # Index 4
        
        self.db_editor_view = DBEditorWidget()
        self.db_editor_view.btn_back.clicked.connect(self.show_main_menu)
        self.db_editor_view.btn_back_tables.clicked.connect(self.show_main_menu)
        self.stack.addWidget(self.db_editor_view) # Index 5
        
        self.hw_control_view = HardwareControlWidget()
        self.hw_control_view.btn_back.clicked.connect(self.show_main_menu)
        self.hw_control_view.btn_back_bottom.clicked.connect(self.show_main_menu)
        self.stack.addWidget(self.hw_control_view) # Index 6
        
        self.xy_stage_view = XYStageWidget()
        self.xy_stage_view.btn_back.clicked.connect(self.show_main_menu)
        self.stack.addWidget(self.xy_stage_view) # Index 7
        
        self.test_rows = {}
        self.results_cache = {}

    def _go_to_page(self, index: int):
        """Instant (no animation) page switch — eliminates main-menu flicker."""
        self.stack.jump_to(index)

    def show_main_menu(self):
        self._go_to_page(1)

    def show_backup_view(self):
        self._go_to_page(3)

    def show_erase_view(self):
        self._go_to_page(4)

    def show_db_editor_view(self):
        self._go_to_page(5)

    def show_hw_control_view(self):
        self._go_to_page(6)

    def show_xy_stage_view(self):
        self._go_to_page(7)

    def show_device_selector(self):
        selector = DeviceSelector(self)
        if selector.exec():
            device_name = selector.selected_device
            apply_device_profile(device_name)
            self.init_dashboard()
        else:
            self.close()

    def init_dashboard(self):
        self.setup_ui()          # guarded internally — safe to call again
        self.available_tests = load_tests_from_folder()
        self.populate_list()
        self.check_start_button_state()
        self.stack.slide_to(2)

    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def setup_ui(self):
        # Guard: don't rebuild the layout if it already exists
        if self.dashboard.layout():
            return
        layout = QHBoxLayout(self.dashboard)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(340)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(20, 30, 20, 30)
        
        # Back button at the very top
        self.btn_back_to_menu = QPushButton("← BACK TO MENU")
        self.btn_back_to_menu.setObjectName("SummaryButton")
        self.btn_back_to_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_to_menu.clicked.connect(self.show_main_menu)
        side_layout.addWidget(self.btn_back_to_menu)
        side_layout.addSpacing(10)
        
        side_layout.addWidget(QLabel("Test Configuration", objectName="Header"))
        side_layout.addSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.test_container = QWidget()
        self.test_container.setObjectName("TestContainer")
        self.test_layout = QVBoxLayout(self.test_container)
        self.test_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.test_container)
        side_layout.addWidget(scroll)
        
        # --- Notification UI ---
        notif_frame = QFrame()
        notif_frame.setStyleSheet("background: #181825; border-radius: 8px; padding: 5px;")
        notif_layout = QVBoxLayout(notif_frame)
        notif_layout.setContentsMargins(10, 10, 10, 10)
        
        top_n = QHBoxLayout()
        lbl_notif = QLabel("Notify via WhatsApp when done?")
        lbl_notif.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold;")
        self.wa_toggle = ToggleSwitch()
        self.wa_toggle.setFixedSize(40, 22)
        top_n.addWidget(lbl_notif)
        top_n.addStretch()
        top_n.addWidget(self.wa_toggle)
        notif_layout.addLayout(top_n)
        
        # Phone input container (hidden initially)
        self.wa_input_container = QWidget()
        wa_inp_layout = QVBoxLayout(self.wa_input_container)
        wa_inp_layout.setContentsMargins(0, 10, 0, 0)
        
        lbl_phone = QLabel("Tap to enter phone number:")
        lbl_phone.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.wa_input = QLineEdit()
        self.wa_input.setPlaceholderText("Tap here — e.g. +919876543210")
        self.wa_input.setReadOnly(True)
        self.wa_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.wa_input.setStyleSheet(
            "background: #313244; color: white; border-radius: 4px; padding: 8px;"
            " border: 1.5px solid #45475a;"
        )
        self.wa_input.mousePressEvent = self._open_phone_numpad
        
        wa_inp_layout.addWidget(lbl_phone)
        wa_inp_layout.addWidget(self.wa_input)
        
        self.wa_input_container.setVisible(False)
        notif_layout.addWidget(self.wa_input_container)
        side_layout.addWidget(notif_frame)
        side_layout.addSpacing(10)

        # Hook toggle animation
        self.wa_toggle.mouseReleaseEvent = self._on_wa_toggle # Overriding click handler
        
        self.btn_start = QPushButton("START BENCHMARK")
        self.btn_start.setObjectName("StartButton")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_benchmarks)
        side_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_benchmarks)
        side_layout.addWidget(self.btn_cancel)
        
        self.btn_summary = QPushButton("VIEW FULL SUMMARY")
        self.btn_summary.setObjectName("SummaryButton")
        self.btn_summary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_summary.setEnabled(False)
        self.btn_summary.clicked.connect(self.show_summary_report)
        side_layout.addWidget(self.btn_summary)
        
        side_layout.addStretch()
        lbl_copy = QLabel("© 2025 Abhishek S, Sigtuple Technologies")
        lbl_copy.setStyleSheet("color: #45475a; font-size: 11px; font-weight: 600; margin-top: 10px;")
        lbl_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(lbl_copy)
        
        layout.addWidget(sidebar)
        
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(50, 50, 50, 50)
        
        self.lbl_status = QLabel("Ready to Perform", objectName="Header")
        self.lbl_status.setStyleSheet("font-size: 30px; color: #ffffff;")
        content_layout.addWidget(self.lbl_status)
        content_layout.addSpacing(30)
        
        content_layout.addWidget(QLabel("Current Module Progress", objectName="SubHeader"))
        self.prog_current = QProgressBar()
        self.prog_current.setFixedHeight(10)
        content_layout.addWidget(self.prog_current)
        content_layout.addSpacing(20)
        
        content_layout.addWidget(QLabel("Overall Benchmarking Progress", objectName="SubHeader"))
        self.prog_total = QProgressBar()
        self.prog_total.setObjectName("TotalProgress")
        self.prog_total.setFixedHeight(10)
        content_layout.addWidget(self.prog_total)
        content_layout.addSpacing(30)
        
        content_layout.addWidget(QLabel("Execution Log", objectName="SubHeader"))
        self.log_area = QScrollArea()
        self.log_area.setStyleSheet("QScrollArea { background: #11111b; border-radius: 8px; border: 1px solid #313244; } QWidget { background: #11111b; }")
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_area.setWidgetResizable(True)
        self.log_area.setWidget(self.log_widget)
        content_layout.addWidget(self.log_area)
        
        content_layout.addWidget(self.log_area)
        
        layout.addWidget(content)

    def _on_wa_toggle(self, event):
        ToggleSwitch.mouseReleaseEvent(self.wa_toggle, event)
        is_on = self.wa_toggle.isChecked()
        self.wa_input_container.setVisible(is_on)

    def _open_phone_numpad(self, event):
        """Open the phone numpad dialog when the user taps the phone input field."""
        dlg = PhoneNumpadDialog(parent=self, initial_value=self.wa_input.text())
        # Centre dialog over the main window
        geo = self.geometry()
        dlg.adjustSize()
        dlg.move(
            geo.center().x() - dlg.width() // 2,
            geo.center().y() - dlg.height() // 2,
        )
        if dlg.exec():
            self.wa_input.setText(dlg.result_number)


    def populate_list(self):
        class_map = {}
        for TestClass in self.available_tests:
            temp_instance = TestClass(CONFIG)
            class_map[temp_instance.name] = TestClass

        configured_tests = list(BENCHMARK_STANDARDS.keys())
        
        for test_name in configured_tests:
            if test_name in class_map:
                TestClass = class_map[test_name]
                temp = TestClass(CONFIG)
                row = TestRowWidget(temp, self)
                self.test_layout.addWidget(row)
                self.test_rows[temp.name] = row

    def check_start_button_state(self):
        if self.worker and self.worker.isRunning(): return
        any_checked = any(w.checkbox.isChecked() for w in self.test_rows.values())
        self.btn_start.setEnabled(any_checked)
        self.btn_start.setText("START BENCHMARK" if any_checked else "SELECT A TEST")

    def log_message(self, message, color="#cdd6f4"):
        lbl = QLabel(message)
        lbl.setStyleSheet(f"color: {color}; font-family: 'Consolas', monospace; font-size: 13px; margin-bottom: 4px;")
        self.log_layout.addWidget(lbl)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def start_benchmarks(self):
        selected_tests = []
        for name, widget in self.test_rows.items():
            if widget.checkbox.isChecked():
                selected_tests.append(widget.test_type(CONFIG))
                widget.info_btn.setEnabled(False)
        
        if not selected_tests: return

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_start.setText("RUNNING...")
        self.lbl_status.setText("Benchmarking In Progress...")
        self.log_message("--- Initializing Batch ---", "#89b4fa")
        self.prog_current.setValue(0); self.prog_total.setValue(0)

        self.worker = BenchmarkWorker(selected_tests)
        self.worker.progress_current.connect(self.prog_current.setValue)
        self.worker.progress_total.connect(self.prog_total.setValue)
        self.worker.test_finished.connect(self.on_test_finished)
        self.worker.all_finished.connect(self.on_batch_finished)
        self.worker.start()

    def cancel_benchmarks(self):
        if self.worker and self.worker.isRunning():
            self.log_message("--- Stopping... ---", "#f38ba8")
            self.worker.stop()
            self.btn_cancel.setEnabled(False)
            self.lbl_status.setText("Cancelling...")

    def on_test_finished(self, name, result):
        status = result.get("status", "Unknown")
        color = "#a6e3a1" if status == "Success" else "#f38ba8"
        self.log_message(f"[{name}] {status}.", color)
        if name in self.test_rows: self.test_rows[name].unlock_report(result)
        self.results_cache[name] = result
        self.btn_summary.setEnabled(True)

    def on_batch_finished(self):
        self.btn_cancel.setEnabled(False)
        self.check_start_button_state()
        self.lbl_status.setText("Benchmarks Completed")
        self.log_message("--- Batch Finished ---", "#fab387")
        
        self.log_message("Starting automated report upload pipeline...", "#cba6f7")
        
        from core.env_parser import get_device_id
        from core.pdf_generator import generate_headless_pdf
        from core.drive_handler import upload_report_to_drive
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class UploadWorker(QThread):
            log_signal = pyqtSignal(str, str)
            def __init__(self, data, parent_window, phone_number=None):
                super().__init__(parent_window)
                self.data = data
                self.phone_number = phone_number
            def run(self):
                try:
                    self.log_signal.emit("Evaluating Benchmark Tolerances...", "#89b4fa")
                    passed_all = True
                    from core.config_loader import get_config
                    from core.evaluator import evaluate_result
                    import re
                    
                    tolerances = get_config().get('tolerances', {})
                    for test_name, res in self.data.items():
                        test_tolerances = tolerances.get(test_name, {})
                        has_bench, comparisons = evaluate_result(test_name, res)
                        
                        if has_bench:
                            for comp in comparisons:
                                label = comp.get('label', '')
                                if label in test_tolerances:
                                    dev_str = str(comp.get('deviation', '0%'))
                                    match = re.search(r'[-+]?\d*\.\d+|\d+', dev_str)
                                    if match:
                                        dev_val = float(match.group())
                                        tol = test_tolerances[label]
                                        if 'max' in tol and dev_val > tol['max']:
                                            passed_all = False
                                            self.log_signal.emit(f"FAIL: {test_name} - {label} (Dev {dev_val}% > MAX {tol['max']}%)", "#f38ba8")
                                        if 'min' in tol and dev_val < tol['min']:
                                            passed_all = False
                                            self.log_signal.emit(f"FAIL: {test_name} - {label} (Dev {dev_val}% < MIN {tol['min']}%)", "#f38ba8")
                    
                    if passed_all:
                        self.log_signal.emit("All evaluated metrics PASSED tolerance.", "#a6e3a1")
                        
                    self.log_signal.emit("Parsing DEVICE_ID...", "#89b4fa")
                    device_id = get_device_id()
                    self.log_signal.emit(f"Extracted Device ID: {device_id}", "#a6e3a1")
                    
                    self.log_signal.emit("Generating PDF Report...", "#89b4fa")
                    pdf_path = f"/tmp/{device_id}_Report.pdf"
                    result_path = generate_headless_pdf(self.data, device_id, pdf_path)
                    
                    if not result_path:
                        self.log_signal.emit("Failed to generate PDF.", "#f38ba8")
                        return
                    
                    self.log_signal.emit("Connecting to Google Drive...", "#89b4fa")
                    success, msg = upload_report_to_drive(result_path, device_id, passed_all)
                    
                    if success:
                        self.log_signal.emit(msg, "#a6e3a1")
                    else:
                        self.log_signal.emit(f"Drive Upload Warning: {msg}", "#fab387")
                        
                    # --- WhatsApp Notification via Twilio ---
                    if self.phone_number:
                        self.log_signal.emit(f"Sending WhatsApp Notification to {self.phone_number}...", "#89b4fa")
                        from utils.notifier import send_whatsapp_via_twilio
                        from core.config_loader import get_config as _get_cfg

                        status_text = "✅ PASSED" if passed_all else "❌ FAILED tolerances"
                        msg_body = (
                            f"🧪 *Compute Tester Report*\n"
                            f"Device ID: {device_id}\n"
                            f"Status: {status_text}\n"
                            f"(Check Shared Drive for the full PDF report)"
                        )

                        ok, detail = send_whatsapp_via_twilio(
                            self.phone_number, msg_body, _get_cfg()
                        )
                        if ok:
                            self.log_signal.emit(f"WhatsApp message sent! {detail}", "#a6e3a1")
                        else:
                            self.log_signal.emit(f"WhatsApp send failed: {detail}", "#f38ba8")
                            
                except Exception as e:
                    self.log_signal.emit(f"Pipeline Automation Error: {e}", "#f38ba8")
                    
        phone_val = self.wa_input.text().strip() if self.wa_toggle.isChecked() else None
        self.uploader = UploadWorker(self.results_cache, self, phone_val)
        self.uploader.log_signal.connect(self.log_message)
        self.uploader.start()
    
    def show_summary_report(self):
        if self.results_cache: GlobalReportDialog(self.results_cache, self).exec()