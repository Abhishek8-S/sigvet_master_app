import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from display.styles import STYLESHEET
from display.window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply Global Styles
    app.setStyleSheet(STYLESHEET)
    
    # Launch Window
    window = MainWindow()
    
    # Get the current screen's full resolution dynamically
    screen = app.primaryScreen()
    if screen:
        size = screen.availableGeometry()
        window.resize(size.width(), size.height())
    
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.show()
    
    sys.exit(app.exec())