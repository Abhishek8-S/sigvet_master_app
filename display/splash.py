from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
import os

class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        # DO NOT set a fixed size here — the splash is inside a centering
        # container widget so the window can remain maximized.
        self.setMaximumWidth(500)   # keeps the visual card compact
        
        # 2. Main Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 60, 40, 60)
        
        # 3. Icon Logo (icon.png, resolves from either source or installed path)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'icon.png')
        
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            pixmap = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo.setPixmap(pixmap)
        self.logo.setStyleSheet("""
            QLabel {
                background: transparent;
                border-radius: 24px;
                padding: 6px;
            }
        """)
        
        # 4. Title text
        self.title = QLabel("SIGVET\nASSISTANCE")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 900; 
            color: #89b4fa; 
            letter-spacing: 4px;
            line-height: 1.2;
        """)
        
        # 5. Status Text
        self.status = QLabel("Initializing Core Modules...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size: 14px; color: #a6adc8; font-style: italic;")
        
        # 6. Loader
        self.loader = QProgressBar()
        self.loader.setFixedHeight(6)
        self.loader.setTextVisible(False)
        self.loader.setRange(0, 100)
        self.loader.setStyleSheet("""
            QProgressBar { 
                border: none; 
                background: #313244; 
                border-radius: 3px; 
            }
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #cba6f7);
                border-radius: 3px; 
            }
        """)

        # 7. Copyright Footer
        self.copy = QLabel("© 2025 Abhishek S\nSigtuple Technologies")
        self.copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copy.setStyleSheet("color: #45475a; font-size: 11px; font-weight: 600;")

        # Assemble layout
        layout.addStretch(1)
        layout.addWidget(self.logo)
        layout.addSpacing(10)
        layout.addWidget(self.title)
        layout.addSpacing(20)
        layout.addWidget(self.status)
        layout.addSpacing(10)
        layout.addWidget(self.loader)
        layout.addStretch(2)
        layout.addWidget(self.copy)

        self.setLayout(layout)

        # Animation Loop
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(35) 

    def update_progress(self):
        self.counter += 1
        self.loader.setValue(self.counter)
        
        if self.counter == 30:
            self.status.setText("Loading Modules...")
        elif self.counter == 60:
            self.status.setText("Verifying Configuration...")
        elif self.counter == 90:
            self.status.setText("Preparing User Interface...")
            
        if self.counter >= 100:
            self.timer.stop()
            self.finished.emit()