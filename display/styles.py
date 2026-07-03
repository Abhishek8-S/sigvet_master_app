# Professional Premium Dark Theme — Catppuccin Mocha palette
# All PyQt6 CSS; no external dependencies.

STYLESHEET = """
/* ══════════════════════════════════
   ROOT & WINDOW
══════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'SF Pro Display', 'Roboto', sans-serif;
    font-size: 14px;
}

/* ══════════════════════════════════
   TYPOGRAPHY
══════════════════════════════════ */
QLabel {
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    background: transparent;
}

QLabel#Header {
    font-size: 28px;
    font-weight: 800;
    color: #89b4fa;
    letter-spacing: 1px;
}

QLabel#SubHeader {
    font-size: 15px;
    color: #a6adc8;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel#ReportTitle {
    font-size: 20px;
    font-weight: bold;
    color: #cdd6f4;
}

QLabel#CardTitle {
    font-size: 15px;
    font-weight: bold;
    color: #f9e2af;
}

QLabel#ReportLabel {
    color: #a6adc8;
    font-size: 13px;
    font-weight: bold;
}

QLabel#ReportValue {
    color: #a6e3a1;
    font-size: 14px;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
}

/* ══════════════════════════════════
   BUTTONS — StartButton
══════════════════════════════════ */
QPushButton#StartButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #3b82f6, stop:1 #6366f1);
    color: #ffffff;
    border: none;
    font-weight: 700;
    font-size: 15px;
    border-radius: 12px;
    padding: 10px 20px;
    letter-spacing: 1px;
}
QPushButton#StartButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #60a5fa, stop:1 #818cf8);
}
QPushButton#StartButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2563eb, stop:1 #4f46e5);
    padding-top: 12px;
    padding-bottom: 8px;
}
QPushButton#StartButton:disabled {
    background: #313244;
    color: #6c7086;
    border: 1px solid #45475a;
}

/* ══════════════════════════════════
   BUTTONS — CancelButton
══════════════════════════════════ */
QPushButton#CancelButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f38ba8, stop:1 #e06c75);
    color: #1e1e2e;
    border: none;
    font-weight: 700;
    font-size: 15px;
    border-radius: 12px;
    padding: 10px 20px;
}
QPushButton#CancelButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ff99b8, stop:1 #f38ba8);
}
QPushButton#CancelButton:pressed {
    background: #d0384d;
    padding-top: 12px;
    padding-bottom: 8px;
}
QPushButton#CancelButton:disabled {
    background: #313244;
    color: #6c7086;
    border: 1px dashed #45475a;
}

/* ══════════════════════════════════
   BUTTONS — SummaryButton (purple)
══════════════════════════════════ */
QPushButton#SummaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #cba6f7, stop:1 #a78bfa);
    color: #1e1e2e;
    border: none;
    font-weight: 700;
    font-size: 14px;
    border-radius: 10px;
    padding: 9px 18px;
}
QPushButton#SummaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #d8b4fe, stop:1 #c084fc);
}
QPushButton#SummaryButton:pressed {
    background: #7c3aed;
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton#SummaryButton:disabled {
    background: transparent;
    color: #45475a;
    border: 1px dashed #45475a;
}

/* ══════════════════════════════════
   BUTTONS — InfoButton
══════════════════════════════════ */
QPushButton#InfoButton {
    background-color: #313244;
    color: #585b70;
    border: 2px solid #45475a;
    border-radius: 12px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#InfoButton:enabled {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-color: #89b4fa;
}

/* ══════════════════════════════════
   BUTTONS — SaveButton (teal)
══════════════════════════════════ */
QPushButton#SaveButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2a9d8f, stop:1 #06b6d4);
    color: #ffffff;
    border: none;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 7px 18px;
}
QPushButton#SaveButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ec4b6, stop:1 #22d3ee);
}
QPushButton#SaveButton:pressed {
    background: #164e63;
}

/* ══════════════════════════════════
   BUTTONS — CloseButton
══════════════════════════════════ */
QPushButton#CloseButton {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
    border-radius: 15px;
    font-weight: bold;
}
QPushButton#CloseButton:hover {
    background-color: #ff99b8;
}

/* ══════════════════════════════════
   CHECKBOXES
══════════════════════════════════ */
QCheckBox {
    spacing: 10px;
    color: #cdd6f4;
    font-size: 15px;
    padding: 5px;
}
QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    border: 2px solid #585b70;
    background: #313244;
}
QCheckBox::indicator:hover {
    border-color: #89b4fa;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #89b4fa, stop:1 #6366f1);
    border-color: #89b4fa;
}

/* ══════════════════════════════════
   GROUP BOXES
══════════════════════════════════ */
QGroupBox {
    border: 1.5px solid #313244;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 10px;
    color: #89b4fa;
    font-weight: 700;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #89b4fa;
    font-size: 13px;
    font-weight: 700;
}

/* ══════════════════════════════════
   SCROLL BARS
══════════════════════════════════ */
QScrollBar:vertical {
    background: #181825;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #89b4fa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #181825;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #89b4fa; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ══════════════════════════════════
   PROGRESS BAR
══════════════════════════════════ */
QProgressBar {
    border: none;
    background: #313244;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #89b4fa, stop:1 #cba6f7);
    border-radius: 5px;
}

/* ══════════════════════════════════
   COMBO BOX
══════════════════════════════════ */
QComboBox {
    background: #313244;
    color: #cdd6f4;
    border: 1.5px solid #45475a;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
}
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { width: 8px; height: 8px; }
QComboBox QAbstractItemView {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
    border-radius: 6px;
}

/* ══════════════════════════════════
   LINE EDIT
══════════════════════════════════ */
QLineEdit {
    background: #313244;
    color: #cdd6f4;
    border: 1.5px solid #45475a;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 14px;
}
QLineEdit:focus { border-color: #89b4fa; }

/* ══════════════════════════════════
   SLIDERS
══════════════════════════════════ */
QSlider::groove:horizontal {
    height: 4px;
    background: #313244;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #89b4fa;
    border: none;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #89b4fa, stop:1 #cba6f7);
    border-radius: 2px;
}

/* ══════════════════════════════════
   CONTAINERS
══════════════════════════════════ */
QFrame#Sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}
QScrollArea {
    border: none;
    background: transparent;
}
QFrame#ReportCard {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 12px;
}

/* ══════════════════════════════════
   MESSAGE BOX
══════════════════════════════════ */
QMessageBox {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QMessageBox QPushButton {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 6px 20px;
    font-weight: 600;
}
QMessageBox QPushButton:hover {
    background: #3b4261;
    border-color: #89b4fa;
}
"""