from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QComboBox, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from core.config import DEVICE_PROFILES

class DeviceSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 250)
        self.selected_device = None
        
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 350, 250)
        self.container.setStyleSheet("""
            QFrame { 
                background-color: #1e1e2e; 
                border: 2px solid #89b4fa; 
                border-radius: 12px; 
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Select Device Profile")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Dropdown
        self.combo = QComboBox()
        self.combo.addItems(list(DEVICE_PROFILES.keys()))
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
            }
        """)
        layout.addWidget(self.combo)
        
        # Button
        btn = QPushButton("CONTINUE")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #60a5fa; }
        """)
        btn.clicked.connect(self.confirm_selection)
        layout.addWidget(btn)
        
        # Animation
        self.eff = QGraphicsOpacityEffect(self.container)
        self.container.setGraphicsEffect(self.eff)
        self.anim = QPropertyAnimation(self.eff, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

    def confirm_selection(self):
        self.selected_device = self.combo.currentText()
        self.anim.setDirection(QPropertyAnimation.Direction.Backward)
        self.anim.finished.connect(self.accept)
        self.anim.start()