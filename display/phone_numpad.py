"""
display/phone_numpad.py — Professional Phone Number Numpad Dialog
=================================================================
A floating, touch-friendly numpad that pops up over the phone
number input field in the benchmarking sidebar.

Matches the existing Catppuccin Mocha dark theme of the app.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont


# ── Colour palette (matches the rest of the app) ──────────────────────────────
_BG        = "#1e1e2e"
_SURFACE   = "#181825"
_OVERLAY   = "#313244"
_MUTED     = "#45475a"
_TEXT      = "#cdd6f4"
_SUBTEXT   = "#a6adc8"
_BLUE      = "#89b4fa"
_GREEN     = "#a6e3a1"
_RED       = "#f38ba8"
_MAUVE     = "#cba6f7"
_PEACH     = "#fab387"


class PhoneNumpadDialog(QDialog):
    """
    A modal numpad dialog for entering a phone number.

    Usage:
        dlg = PhoneNumpadDialog(parent=self, initial_value=self.wa_input.text())
        if dlg.exec():
            self.wa_input.setText(dlg.result_number)
    """

    def __init__(self, parent=None, initial_value: str = ""):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.result_number = ""
        self._value = initial_value or "+"

        self._build_ui()
        self._update_display()

        # Fade-in animation
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card frame
        card = QFrame()
        card.setObjectName("NumpadCard")
        card.setStyleSheet(f"""
            QFrame#NumpadCard {{
                background: {_SURFACE};
                border: 1.5px solid {_OVERLAY};
                border-radius: 16px;
            }}
        """)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setFixedWidth(340)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel("📱")
        icon_lbl.setFont(QFont("Arial", 18))
        title_lbl = QLabel("Enter Phone Number")
        title_lbl.setStyleSheet(
            f"color: {_BLUE}; font-size: 15px; font-weight: 800; letter-spacing: 1px;"
        )
        hint_lbl = QLabel("Include country code")
        hint_lbl.setStyleSheet(f"color: {_SUBTEXT}; font-size: 10px;")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(hint_lbl)
        card_layout.addLayout(header)

        # ── Display ──────────────────────────────────────────────────────────
        display_frame = QFrame()
        display_frame.setStyleSheet(
            f"background: {_BG}; border: 1.5px solid {_OVERLAY}; border-radius: 10px;"
        )
        display_layout = QHBoxLayout(display_frame)
        display_layout.setContentsMargins(14, 10, 14, 10)

        self.display_lbl = QLabel("+")
        self.display_lbl.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self.display_lbl.setStyleSheet(f"color: {_TEXT}; border: none; background: transparent;")
        self.display_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.display_lbl.setMinimumHeight(48)

        self._cursor_lbl = QLabel("|")
        self._cursor_lbl.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self._cursor_lbl.setStyleSheet(f"color: {_BLUE}; border: none; background: transparent;")

        display_layout.addWidget(self.display_lbl, stretch=1)
        display_layout.addWidget(self._cursor_lbl)
        card_layout.addWidget(display_frame)

        # ── Numpad grid ───────────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(8)

        # Layout:
        # [ 1 ] [ 2 ] [ 3 ]
        # [ 4 ] [ 5 ] [ 6 ]
        # [ 7 ] [ 8 ] [ 9 ]
        # [ + ] [ 0 ] [ ⌫ ]
        keys = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("+", 3, 0), ("0", 3, 1), ("⌫", 3, 2),
        ]

        for key, row, col in keys:
            btn = self._make_key(key)
            grid.addWidget(btn, row, col)

        card_layout.addLayout(grid)

        # ── Separator ────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_OVERLAY};")
        card_layout.addWidget(sep)

        # ── Action buttons ────────────────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        btn_clear = QPushButton("✕  Clear")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setFixedHeight(44)
        btn_clear.setStyleSheet(self._action_style(_MUTED, _TEXT))
        btn_clear.clicked.connect(self._clear)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setFixedHeight(44)
        btn_cancel.setStyleSheet(self._action_style(_MUTED, _RED))
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("✓  Confirm")
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setFixedHeight(44)
        btn_confirm.setStyleSheet(self._action_style(_GREEN, _BG))
        btn_confirm.clicked.connect(self._confirm)

        action_row.addWidget(btn_clear, 1)
        action_row.addWidget(btn_cancel, 1)
        action_row.addWidget(btn_confirm, 2)
        card_layout.addLayout(action_row)

        outer.addWidget(card)

    # ── Key factory ───────────────────────────────────────────────────────────
    def _make_key(self, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(56)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if label == "⌫":
            bg, fg, hover = _RED, _BG, "#e58097"
        elif label == "+":
            bg, fg, hover = _MAUVE, _BG, "#b891e0"
        else:
            bg, fg, hover = _OVERLAY, _TEXT, _MUTED

        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: 800;
                font-family: "Consolas", monospace;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton:pressed {{
                background: {_BLUE};
                color: {_BG};
            }}
        """)

        btn.clicked.connect(lambda _, k=label: self._on_key(k))
        return btn

    @staticmethod
    def _action_style(bg: str, fg: str) -> str:
        return f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:pressed {{ background: {_BLUE}; color: {_BG}; }}
        """

    # ── Logic ────────────────────────────────────────────────────────────────
    def _on_key(self, key: str):
        if key == "⌫":
            if len(self._value) > 1:          # always keep the leading "+"
                self._value = self._value[:-1]
            elif self._value == "+":
                pass                           # don't delete the "+"
            else:
                self._value = "+"
        elif key == "+":
            if not self._value.startswith("+"):
                self._value = "+" + self._value
        else:
            if len(self._value) < 16:          # max E.164 length
                self._value += key
        self._update_display()

    def _update_display(self):
        self.display_lbl.setText(self._value)

    def _clear(self):
        self._value = "+"
        self._update_display()

    def _confirm(self):
        # Accept only if looks like a plausible number (+countrycode + digits)
        digits = self._value.replace("+", "")
        if len(digits) >= 7:
            self.result_number = self._value
            self.accept()
        else:
            self.display_lbl.setStyleSheet(
                f"color: {_RED}; border: none; background: transparent;"
            )
            self.display_lbl.setText("Too short!")
            # Reset after 800 ms
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(800, self._restore_display)

    def _restore_display(self):
        self.display_lbl.setStyleSheet(
            f"color: {_TEXT}; border: none; background: transparent;"
        )
        self._update_display()
