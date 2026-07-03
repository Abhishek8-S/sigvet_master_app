from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QScrollArea, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import struct
import time
import os

# ─── Serial helper (reuses the existing VID/PID from config) ──────────────────
def _get_serial():
    """Finds and opens the motor serial port or returns None."""
    try:
        import serial
        import subprocess
        from serial.tools import list_ports
        from core.config_loader import get_config
        cfg = get_config()
        hw = cfg.get('hardware', {})
        VID = hw.get('vid', 0x04B4)
        PID = hw.get('pid', 0xF232)
        sudo_pw = cfg.get('app', {}).get('sudo_password', 'sigvet123')

        port = None
        # 1. Prefer VID/PID match
        for dev in list_ports.comports():
            if dev.vid == VID and dev.pid == PID:
                port = dev.device
                break
        # 2. Fallback: first /dev/ttyACM* or /dev/ttyUSB*
        if port is None:
            for dev in list_ports.comports():
                if dev.device.startswith(('/dev/ttyACM', '/dev/ttyUSB')):
                    port = dev.device
                    break
        if port is None:
            return None

        # 3. Fix permissions with sudo (stdin-based, no TTY needed)
        if os.name == 'posix':
            subprocess.run(
                ['sudo', '-S', 'chmod', '666', port],
                input=f"{sudo_pw}\n",
                capture_output=True, text=True
            )

        return serial.Serial(port, timeout=2)
    except Exception:
        pass
    return None


# ─── Background worker so blocking serial calls don't freeze the UI ───────────
class _StageWorker(QThread):
    log_signal   = pyqtSignal(str, str)   # message, css-colour
    done_signal  = pyqtSignal()

    def __init__(self, fn, *args):
        super().__init__()
        self._fn   = fn
        self._args = args

    def run(self):
        try:
            result = self._fn(*self._args)
            if result is not None:
                self.log_signal.emit(str(result), "#a6e3a1")
        except Exception as e:
            self.log_signal.emit(f"ERROR: {e}", "#f38ba8")
        finally:
            self.done_signal.emit()


# ─── Motor helpers (all pure-functions so they can be unit-tested) ─────────────
def _bytes_to_int(b):
    return struct.unpack("<i", b)[0]

def _int_to_bytes(v):
    return struct.pack("<i", v)

def _int2_to_bytes(a, b):
    return struct.pack("<ii", a, b)

def _cat(b1, b2):
    b = bytearray(b1)
    b.extend(b2)
    return bytes(b)

def _rx(ser, timeout=60):
    ser.flushInput(); ser.flushOutput()
    t0 = time.time()
    while True:
        data = ser.read(46)
        if len(data) == 46:
            return data
        if time.time() - t0 > timeout:
            raise TimeoutError("No response from PCB within timeout.")

def _home(ser, axis):
    cmd = {'x': [0x7A, 0x00], 'y': [0x7B, 0x00]}[axis]
    ser.write(bytes(cmd))
    rx = _rx(ser, 120)
    pos = _bytes_to_int(rx[4:8] if axis == 'x' else rx[8:12])
    return f"{axis.upper()} homed. Position: {pos}"

def _goto(ser, axis, step, x_max=2560000, y_max=800000):
    limit = x_max if axis == 'x' else y_max
    step  = max(0, min(step, limit))
    prefix = b'\xA0\x07' if axis == 'x' else b'\xB0\x07'
    for _ in range(5):
        ser.write(_cat(prefix, _int_to_bytes(step)))
        rx = _rx(ser)
        pos = _bytes_to_int(rx[4:8] if axis == 'x' else rx[8:12])
        return f"{axis.upper()} moved. Position: {pos}"
    raise Exception("Move failed after 5 retries.")

def _set_current(ser, xi, yi):
    ser.write(_cat(b'\x00\xA7', _int2_to_bytes(xi, yi)))
    return f"XY current set to X={xi}, Y={yi}"

def _stress(ser, gui_log_fn, speed, n_loops):
    speed_map = {
        "High Speed":     b'\x00\xA1',
        "Moderate Speed": b'\x00\xA3',
        "Low Speed":      b'\x00\xA2',
    }
    prefix = speed_map.get(speed)
    if not prefix:
        raise ValueError("Unknown speed selection.")
    for i in range(n_loops):
        gui_log_fn(f"Stress loop {i+1}/{n_loops}…", "#cba6f7")
        ser.write(_cat(prefix, b'\x00'))
        _rx(ser, 180)
    return f"Stress test complete ({n_loops} loops)."


# ─── Main Widget ───────────────────────────────────────────────────────────────
class XYStageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ser      = None
        self.x_step   = 0
        self.y_step   = 0
        self._worker  = None
        self.setup_ui()
        self._connect_serial()

    # ── Serial init ──────────────────────────────────────────────────────────
    def _connect_serial(self):
        self.ser = _get_serial()
        if self.ser:
            self._log("✅  XY Stage PCB connected.", "#a6e3a1")
        else:
            self._log("⚠️  PCB not detected. Connect hardware and re-open this panel.", "#fab387")

    def _require_serial(self):
        if not self.ser or not self.ser.is_open:
            self._connect_serial()
        if not self.ser:
            QMessageBox.critical(self, "No Hardware", "PCB not connected. Check serial port and VID/PID in config.yaml.")
            return False
        return True

    # ── Logging ──────────────────────────────────────────────────────────────
    def _log(self, msg, color="#cdd6f4"):
        lbl = QLabel(f"▸ {msg}")
        lbl.setStyleSheet(f"color: {color}; font-family: Consolas, monospace; font-size: 13px; margin-bottom: 3px;")
        lbl.setWordWrap(True)
        self._log_layout.addWidget(lbl)
        self._log_area.verticalScrollBar().setValue(self._log_area.verticalScrollBar().maximum())

    # ── Run blocking call in background thread ────────────────────────────────
    def _run(self, fn, *args):
        self._set_busy(True)
        self._worker = _StageWorker(fn, *args)
        self._worker.log_signal.connect(self._log)
        self._worker.done_signal.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _set_busy(self, busy):
        for btn in self._all_btns:
            btn.setEnabled(not busy)

    # ── UI Setup ──────────────────────────────────────────────────────────────
    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QLabel("XY Stage Tester")
        hdr.setObjectName("Header")
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hdr)

        # Main row: controls left, log right
        main_row = QHBoxLayout()
        main_row.setSpacing(18)

        # ── Left: control panels ────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(14)

        # -- Homing --
        grp_home = QGroupBox("Homing")
        grp_home.setStyleSheet(self._grp_style("#89b4fa"))
        h_home = QHBoxLayout(grp_home)
        h_home.setSpacing(10)
        self.btn_home_x = self._btn("HOME X", "#89b4fa")
        self.btn_home_y = self._btn("HOME Y", "#89b4fa")
        self.btn_home_x.clicked.connect(lambda: self._do_home("x"))
        self.btn_home_y.clicked.connect(lambda: self._do_home("y"))
        h_home.addWidget(self.btn_home_x)
        h_home.addWidget(self.btn_home_y)
        left.addWidget(grp_home)

        # -- Set Current --
        grp_cur = QGroupBox("Set Motor Current (X / Y)")
        grp_cur.setStyleSheet(self._grp_style("#f9e2af"))
        v_cur = QVBoxLayout(grp_cur)
        cur_row = QHBoxLayout()
        self.combo_cur_x = self._combo(["1", "2", "3"])
        self.combo_cur_y = self._combo(["1", "2", "3"])
        cur_row.addWidget(QLabel("X Current:"))
        cur_row.addWidget(self.combo_cur_x)
        cur_row.addSpacing(12)
        cur_row.addWidget(QLabel("Y Current:"))
        cur_row.addWidget(self.combo_cur_y)
        v_cur.addLayout(cur_row)
        self.btn_set_cur = self._btn("SET CURRENT", "#f9e2af")
        self.btn_set_cur.clicked.connect(self._do_set_current)
        v_cur.addWidget(self.btn_set_cur)
        left.addWidget(grp_cur)

        # -- Stress Test --
        grp_stress = QGroupBox("Stress Test")
        grp_stress.setStyleSheet(self._grp_style("#a6e3a1"))
        v_stress = QVBoxLayout(grp_stress)
        stress_row = QHBoxLayout()
        self.combo_speed  = self._combo(["High Speed", "Moderate Speed", "Low Speed"])
        self.combo_loops  = self._combo(["1", "5", "10", "25", "50", "100"])
        stress_row.addWidget(QLabel("Speed:"))
        stress_row.addWidget(self.combo_speed)
        stress_row.addSpacing(12)
        stress_row.addWidget(QLabel("Loops:"))
        stress_row.addWidget(self.combo_loops)
        v_stress.addLayout(stress_row)
        self.btn_stress = self._btn("START STRESS TEST", "#a6e3a1")
        self.btn_stress.clicked.connect(self._do_stress)
        v_stress.addWidget(self.btn_stress)
        left.addWidget(grp_stress)

        # -- Move --
        grp_move = QGroupBox("Move")
        grp_move.setStyleSheet(self._grp_style("#cba6f7"))
        v_move = QVBoxLayout(grp_move)
        for axis in ["X", "Y"]:
            ax_lbl = QLabel(f"Move {axis}")
            ax_lbl.setStyleSheet("color: #cba6f7; font-weight: 600;")
            v_move.addWidget(ax_lbl)
            move_row = QHBoxLayout()
            move_row.setSpacing(8)
            for step in ["+5000", "+10000", "-5000", "-10000"]:
                btn = self._btn(step, "#cba6f7", small=True)
                btn.clicked.connect(lambda _, ax=axis, s=step: self._do_move(ax, s))
                move_row.addWidget(btn)
            v_move.addLayout(move_row)
        left.addWidget(grp_move)

        left.addStretch(1)
        main_row.addLayout(left, 2)

        # ── Right: log area ─────────────────────────────────────────────────
        log_box = QGroupBox("Output Log")
        log_box.setStyleSheet(self._grp_style("#6c7086"))
        log_vbox = QVBoxLayout(log_box)
        self._log_area = QScrollArea()
        self._log_area.setWidgetResizable(True)
        self._log_area.setStyleSheet("QScrollArea { background: #11111b; border-radius: 6px; border: none; } QWidget { background: #11111b; }")
        log_inner = QWidget()
        self._log_layout = QVBoxLayout(log_inner)
        self._log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._log_area.setWidget(log_inner)
        log_vbox.addWidget(self._log_area)
        main_row.addWidget(log_box, 3)

        root.addLayout(main_row, 1)

        # Back button
        self.btn_back = QPushButton("← BACK TO MENU")
        self.btn_back.setObjectName("SummaryButton")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedHeight(44)
        root.addWidget(self.btn_back)

        # Collect all action buttons for busy-state management
        self._all_btns = [
            self.btn_home_x, self.btn_home_y, self.btn_set_cur,
            self.btn_stress, self.btn_back
        ]

    # ── Button / widget helpers ───────────────────────────────────────────────
    @staticmethod
    def _btn(label, accent="#89b4fa", small=False):
        b = QPushButton(label)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        h = 36 if small else 44
        b.setFixedHeight(h)
        b.setStyleSheet(f"""
            QPushButton {{
                background: #313244;
                color: {accent};
                border: 1.5px solid {accent};
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background: {accent}22; }}
            QPushButton:disabled {{ color: #45475a; border-color: #45475a; background: #181825; }}
        """)
        return b

    @staticmethod
    def _combo(choices):
        c = QComboBox()
        c.addItems(choices)
        c.setStyleSheet("""
            QComboBox {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 4px 8px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #313244; color: #cdd6f4; }
        """)
        return c

    @staticmethod
    def _grp_style(accent):
        return f"""
            QGroupBox {{
                border: 1.5px solid {accent}55;
                border-radius: 10px;
                margin-top: 10px;
                color: {accent};
                font-weight: 700;
                font-size: 13px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
            QLabel {{ color: #cdd6f4; font-size: 13px; }}
        """

    # ── Action handlers ───────────────────────────────────────────────────────
    def _do_home(self, axis):
        if not self._require_serial(): return
        self._log(f"Homing {axis.upper()}…", "#89b4fa")
        self._run(_home, self.ser, axis)
        if axis == 'x': self.x_step = 0
        else:            self.y_step = 0

    def _do_set_current(self):
        if not self._require_serial(): return
        xi = int(self.combo_cur_x.currentText())
        yi = int(self.combo_cur_y.currentText())
        self._log(f"Setting current X={xi} Y={yi}…", "#f9e2af")
        self._run(_set_current, self.ser, xi, yi)

    def _do_stress(self):
        if not self._require_serial(): return
        speed  = self.combo_speed.currentText()
        loops  = int(self.combo_loops.currentText())
        self._log(f"Stress test: {speed}, {loops} loops…", "#a6e3a1")
        self._run(_stress, self.ser, self._log, speed, loops)

    def _do_move(self, axis, action):
        if not self._require_serial(): return
        delta = int(action)   # e.g. "+5000" -> 5000, "-5000" -> -5000
        if axis == 'X':
            self.x_step = max(0, self.x_step + delta)
            step = self.x_step
        else:
            self.y_step = max(0, self.y_step + delta)
            step = self.y_step
        self._log(f"Move {axis} {action:+} → target {step}", "#cba6f7")
        self._run(_goto, self.ser, axis.lower(), step)
