from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont


class MainMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btn_animations = []
        self.setup_ui()
        QTimer.singleShot(80, self._animate_entrance)

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addStretch(1)

        # ── Icon Glyph ──────────────────────────────────────────────────────
        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_dot = QLabel("◈")
        icon_dot.setStyleSheet("font-size: 40px; color: #89b4fa; background: transparent;")
        icon_row.addWidget(icon_dot)
        root.addLayout(icon_row)
        root.addSpacing(8)

        # ── Title ───────────────────────────────────────────────────────────
        title = QLabel("SIGVET ASSISTANCE")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 30px;
            font-weight: 900;
            letter-spacing: 4px;
            color: #89b4fa;
            background: transparent;
        """)
        root.addWidget(title)

        sub = QLabel("Production Compute Suite  ·  v1.0")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            "font-size: 12px; color: #585b70; letter-spacing: 1.5px;"
            " background: transparent; margin-bottom: 6px;"
        )
        root.addWidget(sub)

        # Gradient divider
        div = QLabel()
        div.setFixedSize(120, 2)
        div.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #89b4fa, stop:1 #cba6f7); border-radius: 1px;"
        )
        div_row = QHBoxLayout()
        div_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        div_row.addWidget(div)
        root.addLayout(div_row)

        root.addSpacing(32)

        # ── Buttons ─────────────────────────────────────────────────────────
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(14)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        menu_items = [
            ("btn_compute",    "     COMPUTE TESTER",    "StartButton"),
            ("btn_backup",     "     ORDERSTORE BACKUP", "StartButton"),
            ("btn_db_editor",  "     CALIB DB EDITOR",   "StartButton"),
            ("btn_hw_control", "     HARDWARE CONTROL",  "StartButton"),
            ("btn_xy_stage",   "     XY STAGE TESTER",   "StartButton"),
            ("btn_erase",      "     ERASE DATA",         "CancelButton"),
        ]

        self._all_btn_widgets = []
        for attr, label, obj_name in menu_items:
            btn = QPushButton(label)
            btn.setObjectName(obj_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(320, 56)
            btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            setattr(self, attr, btn)
            btn_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self._all_btn_widgets.append(btn)

        root.addLayout(btn_layout)
        root.addStretch(2)

        # ── Footer ──────────────────────────────────────────────────────────
        footer = QLabel("© 2025 Abhishek S  ·  Sigtuple Technologies")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(
            "color: #313244; font-size: 11px; letter-spacing: 1px;"
            " margin-bottom: 18px; background: transparent;"
        )
        root.addWidget(footer)

    # ── Staggered fade-in for each button on first display ──────────────────
    def _animate_entrance(self):
        for i, btn in enumerate(self._all_btn_widgets):
            fx = QGraphicsOpacityEffect(btn)
            fx.setOpacity(0.0)
            btn.setGraphicsEffect(fx)

            anim = QPropertyAnimation(fx, b"opacity", self)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setDuration(350)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            QTimer.singleShot(i * 75, anim.start)
            self._btn_animations.append((fx, anim))   # keep refs alive
