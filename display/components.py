import json
import os
from PyQt6.QtWidgets import (QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QGridLayout, QGraphicsOpacityEffect,
                             QWidget, QFileDialog, QLineEdit)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from core.evaluator import evaluate_result

# --- CUSTOM TOGGLE SWITCH ---
class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self._checked = False
        self._thumb_position = 3
        
        self.anim = QPropertyAnimation(self, b"thumb_position", self)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.setDuration(200)

    @pyqtProperty(int)
    def thumb_position(self):
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos):
        self._thumb_position = pos
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        if self._checked:
            self.anim.setStartValue(3)
            self.anim.setEndValue(24)
        else:
            self.anim.setStartValue(24)
            self.anim.setEndValue(3)
        self.anim.start()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.setChecked(not self._checked)
        # Emit pseudo signal / call custom callback if required

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background track
        p.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor("#a6e3a1") if self._checked else QColor("#45475a")
        p.setBrush(bg_color)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)
        
        # Draw thumb
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(self._thumb_position, 3, 20, 20)

# --- DEVICE NAME INPUT DIALOG ---
class DeviceNameInput(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        self.device_name = "Unknown_Device"
        
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 400, 300)
        self.container.setStyleSheet("QFrame { background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 12px; }")
        
        layout = QVBoxLayout(self.container)
        layout.addWidget(QLabel("Enter Device Name/Number", styleSheet="color:white; font-size:16px; font-weight:bold;", alignment=Qt.AlignmentFlag.AlignCenter))
        
        self.input = QLineEdit()
        self.input.setStyleSheet("background:#313244; color:white; padding:8px; border-radius:4px;")
        layout.addWidget(self.input)
        
        # Simulated Keyboard (Row 1)
        kb_layout = QGridLayout()
        keys = "1234567890QWERTYUIOPASDFGHJKLZXCVBNM"
        r, c = 0, 0
        for k in keys:
            btn = QPushButton(k)
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("background:#45475a; color:white; border:none; border-radius:4px;")
            btn.clicked.connect(lambda _, x=k: self.input.setText(self.input.text() + x))
            kb_layout.addWidget(btn, r, c)
            c += 1
            if c > 9: r += 1; c = 0
        layout.addLayout(kb_layout)
        
        # Actions
        h = QHBoxLayout()
        ok = QPushButton("OK", styleSheet="background:#3b82f6; color:white; padding:10px; border-radius:4px; font-weight:bold;")
        ok.clicked.connect(self.accept_input)
        back = QPushButton("BACK", styleSheet="background:#313244; color:white; padding:10px; border-radius:4px;")
        back.clicked.connect(self.input.backspace)
        h.addWidget(back); h.addWidget(ok)
        layout.addLayout(h)

    def accept_input(self):
        if self.input.text(): self.device_name = self.input.text()
        self.accept()

# --- GLOBAL REPORT DIALOG ---
class GlobalReportDialog(QDialog):
    def __init__(self, all_data, parent=None):
        super().__init__(parent)
        self.all_data = all_data 
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 700)
        
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 600, 700)
        self.container.setStyleSheet("QFrame { background-color: #1e1e2e; border: 2px solid #cba6f7; border-radius: 12px; }")
        
        layout = QVBoxLayout(self.container)
        h = QHBoxLayout()
        h.addWidget(QLabel("Session Summary", objectName="ReportTitle"))
        h.addStretch()
        self.btn_save = QPushButton("DOWNLOAD REPORT", objectName="SaveButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.start_download_flow)
        h.addWidget(self.btn_save)
        h.addSpacing(10)
        cl = QPushButton("X", objectName="CloseButton")
        cl.setFixedSize(30,30); cl.clicked.connect(self.close)
        h.addWidget(cl)
        layout.addLayout(h)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget(); content.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(content); c_layout.setSpacing(15)
        
        for name, data in all_data.items():
            card = QFrame()
            card.setStyleSheet("background-color: #181825; border-radius: 8px; border: 1px solid #313244;")
            cl_inner = QVBoxLayout(card)
            cl_inner.addWidget(QLabel(name, objectName="CardTitle"))
            
            has_bench, comparisons = evaluate_result(name, data)
            grid_w = QWidget(); grid = QGridLayout(grid_w); row = 0
            for k, v in data.items():
                if k not in ['report', 'status', 'report_saved', 'metrics', 'key']:
                    grid.addWidget(QLabel(f"{str(k).title()}:", objectName="ReportLabel"), row, 0)
                    grid.addWidget(QLabel(str(v), objectName="ReportValue"), row, 1)
                    row += 1
            if has_bench:
                grid.addWidget(QLabel("──────────────", styleSheet="color:#45475a;"), row, 0, 1, 3); row += 1
                for c in comparisons:
                    grid.addWidget(QLabel(c['label'], objectName="ReportLabel"), row, 0)
                    grid.addWidget(QLabel(f"{c['expected']}/{c['actual']}", objectName="ReportValue"), row, 1)
                    lbl = QLabel(c['deviation']); lbl.setStyleSheet(f"color:{c['dev_color']}; font-weight:bold;")
                    grid.addWidget(lbl, row, 2); row += 1
            cl_inner.addWidget(grid_w); c_layout.addWidget(card)

        c_layout.addStretch()
        scroll.setWidget(content); layout.addWidget(scroll)
        self.show_anim()

    def show_anim(self):
        self.eff = QGraphicsOpacityEffect(self.container)
        self.container.setGraphicsEffect(self.eff)
        self.a = QPropertyAnimation(self.eff, b"opacity")
        self.a.setDuration(300); self.a.setStartValue(0); self.a.setEndValue(1); self.a.start()

    def start_download_flow(self):
        inp = DeviceNameInput(self)
        if inp.exec():
            device_name = inp.device_name
            default_name = f"{device_name}_Report.pdf"
            path, _ = QFileDialog.getSaveFileName(self, "Save Report PDF", default_name, "PDF Files (*.pdf)")
            if path:
                self.generate_pdf(path, device_name)

    def draw_footer(self, c):
        c.saveState()
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.gray)
        c.drawString(50, 40, "Developed by")
        c.setFillColor(colors.black)
        c.drawString(50, 28, "© 2025 Abhishek S | Sigtuple Technologies")
        c.restoreState()

    def generate_pdf(self, path, device_name):
        try:
            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            y = h - 50
            
            c.setFillColor(colors.HexColor("#3b82f6"))
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, y, "Compute Benchmark Report")
            y -= 25
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, f"Device Identifier: {device_name}")
            y -= 20
            
            c.setLineWidth(1)
            c.setStrokeColor(colors.gray)
            c.line(50, y, w-50, y)
            y -= 40
            
            for name, data in self.all_data.items():
                if y < 150: 
                    self.draw_footer(c)
                    c.showPage()
                    y = h - 50 
                
                c.setFillColor(colors.HexColor("#1e1e2e"))
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, name)
                y -= 20
                
                has_bench, comparisons = evaluate_result(name, data)
                
                c.setFillColor(colors.gray)
                c.setFont("Helvetica", 9)
                c.drawString(60, y, "METRIC")
                c.drawString(250, y, "VALUE / (EXPECTED)")
                c.drawString(450, y, "DEVIATION")
                y -= 15
                
                c.setFont("Helvetica", 10)
                if has_bench:
                    for comp in comparisons:
                        label = comp['label']
                        val = f"{comp['actual']} (Exp: {comp['expected']})"
                        dev = comp['deviation']
                        
                        c.setFillColor(colors.black)
                        c.drawString(60, y, label)
                        c.drawString(250, y, val)
                        
                        if "FAIL" in dev or "-" in dev: c.setFillColor(colors.red)
                        else: c.setFillColor(colors.green)
                        c.drawString(450, y, dev)
                        
                        y -= 15
                
                c.setFillColor(colors.darkgray)
                c.setFont("Helvetica", 9)
                for k, v in data.items():
                    if k not in ['report', 'status', 'report_saved', 'metrics', 'key']:
                        if y < 60: 
                            self.draw_footer(c)
                            c.showPage()
                            y = h - 50
                        c.drawString(60, y, f"{k}: {v}")
                        y -= 12
                
                y -= 25 

            # Draw footer on the last page as well
            self.draw_footer(c)
            c.save()
            self.btn_save.setText("SAVED PDF!")
            self.btn_save.setEnabled(False)
        except Exception as e:
            print(f"PDF Error: {e}")

class ReportDialog(QDialog):
    def __init__(self, test_name, data, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 500)
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 450, 500)
        self.container.setStyleSheet("QFrame { background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 12px; }")
        
        layout = QVBoxLayout(self.container)
        h = QHBoxLayout()
        h.addWidget(QLabel(test_name, objectName="ReportTitle"))
        h.addStretch()
        cl = QPushButton("X", objectName="CloseButton")
        cl.setFixedSize(30,30); cl.clicked.connect(self.close)
        h.addWidget(cl)
        layout.addLayout(h)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget(); content.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(content)
        
        grid_w = QWidget(); grid = QGridLayout(grid_w); grid.setSpacing(10); r = 0
        for k, v in data.items():
            if k in ['report', 'status', 'report_saved']: continue
            grid.addWidget(QLabel(f"{str(k).replace('_', ' ').title()}:", objectName="ReportLabel"), r, 0)
            val = QLabel(str(v), objectName="ReportValue"); val.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(val, r, 1); r+=1
        c_layout.addWidget(grid_w)

        has_bench, comparisons = evaluate_result(test_name, data)
        if has_bench:
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("background: #45475a;")
            c_layout.addWidget(sep)
            lbl_b = QLabel("BENCHMARK ANALYSIS"); lbl_b.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px; letter-spacing: 1px;"); lbl_b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(lbl_b)
            
            b_grid_w = QWidget(); b_grid = QGridLayout(b_grid_w)
            b_grid.addWidget(QLabel("Metric", styleSheet="color:#a6adc8; font-size:11px;"), 0, 0)
            b_grid.addWidget(QLabel("Exp / Act", styleSheet="color:#a6adc8; font-size:11px;"), 0, 1)
            b_grid.addWidget(QLabel("Dev", styleSheet="color:#a6adc8; font-size:11px;"), 0, 2)
            
            row = 1
            for comp in comparisons:
                b_grid.addWidget(QLabel(comp['label'], objectName="ReportLabel"), row, 0)
                b_grid.addWidget(QLabel(f"{comp['expected']} / {comp['actual']}", objectName="ReportValue"), row, 1)
                
                dev_lbl = QLabel(comp['deviation'])
                dev_lbl.setStyleSheet(f"color: {comp['dev_color']}; font-weight: bold; font-family: monospace;")
                b_grid.addWidget(dev_lbl, row, 2)
                row += 1
                
            c_layout.addWidget(b_grid_w)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)