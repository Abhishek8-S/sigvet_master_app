"""
Hardware Control Widget — Sigvet Assistance App
================================================
Complete port of the original tkinter SIGVET Test App V1.2 to PyQt6.

Fixes applied:
1. Unified `_process_received_data` mirrors Code 2's `receive_data()` exactly.
2. Background workers (Homing/Stress Test) emit `raw_data` signals so the UI 
   encoders update continuously in real-time during long operations.
3. Individual homing properly resets the internal step trackers to 0.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QLineEdit, QGroupBox, QFrame,
    QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
import serial
import serial.tools.list_ports
import struct
import os
import time

try:
    from core.config_loader import get_config
except ImportError:
    def get_config(): return {}


# ──────────────────────────────────────────────────────────────────────────────
# CORE PCB LOGIC — PRESERVED FROM CODE 2
# ──────────────────────────────────────────────────────────────────────────────
def bytes_to_int(value):
    return struct.unpack("<i", value)

def bytes_to_int1(value1, value2):
    return struct.unpack("<ii", value1, value2)

def Int_to_bytes1(value1, value2):
    return struct.pack("<ii", value1, value2)

def Int_to_bytes(value):
    return struct.pack("<i", value)

def concatenate(b1, b2):
    b1 = bytearray(b1)
    for i in range(0, len(b2)):
        b1.append(b2[i])
    return b1

def get_command_for_value_x(value):
    val = Int_to_bytes(value)
    return concatenate(b'\xA0\x07', val)

def get_command_for_value_y(value):
    val = Int_to_bytes(value)
    return concatenate(b'\xB0\x07', val)

def get_command_for_value_z(value):
    val = Int_to_bytes(value)
    return concatenate(b'\xD0\x07', val)

def get_command_for_value_turret(value):
    val = Int_to_bytes(value)
    return concatenate(b'\xE0\x07', val)

def get_command_for_value_led(W):
    LED_W = Int_to_bytes(W)
    return concatenate(b'\x00\x7A', LED_W)

def get_command_for_value_uv_led(W):
    LED_W = Int_to_bytes(W)
    return concatenate(b'\x0A\x70', LED_W)

def get_command_for_value_backlight(L):
    Backlight_L = Int_to_bytes(L)
    return concatenate(b'\x00\x7E', Backlight_L)

def get_command_for_value_barcode_led(M):
    Barcode_LED_M = Int_to_bytes(M)
    return concatenate(b'\x00\x7F', Barcode_LED_M)

def get_command_for_value_oil_dispense(value1, value2):
    OilDispense_S = Int_to_bytes1(value1, value2)
    return concatenate(b'\x7E\x00', OilDispense_S)

def get_command_for_value_MTorque(K):
    MTorque_K = Int_to_bytes(K)
    return concatenate(b'\x80\x00', MTorque_K)


ERROR_MAP = {
    b'\x01\xFA': "X_Motor_Not_Working",
    b'\x02\xFA': "X_Encoder_Not_Working",
    b'\x17\xFA': "X_Switch_Not_Working",
    b'\x07\xFA': "X_Motor_Driver_Fault",
    b'\x11\xFA': "Requested_X_Step_Exceeding_The_Limit",
    b'\x1D\xFA': "X_Homing_Not_Done_Yet",
    b'\x25\xFA': "X_Motor_Busy",
    b'\x03\xFA': "Y_Motor_Not_Working",
    b'\x04\xFA': "Y_Encoder_Not_Working",
    b'\x18\xFA': "Y_Switch_Not_Working",
    b'\x08\xFA': "Y_Motor_Driver_Fault",
    b'\x12\xFA': "Requested_Y_Step_Exceeding_The_Limit",
    b'\x1E\xFA': "Y_Homing_Not_Done_Yet",
    b'\x26\xFA': "Y_Motor_Busy",
    b'\x05\xFA': "Z_Motor_Not_Working",
    b'\x06\xFA': "Z_Encoder_Not_Working",
    b'\x19\xFA': "Z_Switch_Not_Working",
    b'\x09\xFA': "Z_Motor_Driver_Fault",
    b'\x13\xFA': "Requested_Z_Step_Exceeding_The_Limit",
    b'\x1F\xFA': "Z_Homing_Not_Done_Yet",
    b'\x27\xFA': "Z_Motor_Busy",
    b'\x2B\xFA': "Turret_Motor_Not_Working",
    b'\x2C\xFA': "Turret_Encoder_Not_Working",
    b'\x2D\xFA': "Turret_Switch_Not_Working",
    b'\x2E\xFA': "Turret_Motor_Driver_Fault",
    b'\x2A\xFA': "Requested_Turret_Step_Exceeding_The_Limit",
    b'\x2F\xFA': "Turret_Homing_Not_Done_Yet",
    b'\x28\xFA': "Turret_Motor_Busy",
    b'\x22\xFA': "Wrong_Command_Received",
    b'\x23\xFA': "PCB_Paused",
    b'\x24\xFA': "PCB_Busy",
    b'\x29\xFA': "All_Motors_Homing_Not_Done",
}


# ──────────────────────────────────────────────────────────────────────────────
# WORKERS (Executing exact Code 2 patterns off the UI thread)
# ──────────────────────────────────────────────────────────────────────────────
class ConnectionWorker(QThread):
    connected = pyqtSignal(object, str)
    log       = pyqtSignal(str)

    def __init__(self, baudrate, password, parent=None):
        super().__init__(parent)
        self.baudrate = baudrate
        self.password = password
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        while not self._abort:
            ports = [p.device for p in serial.tools.list_ports.comports()
                     if 'ACM' in p.device or 'USB' in p.device]

            if not ports:
                self.log.emit("Waiting for device...")
                time.sleep(1)
                continue

            for port in ports:
                try:
                    os.system(f"echo '{self.password}' | sudo -S chmod 666 {port}")
                    ser = serial.Serial(
                        port=port,
                        baudrate=self.baudrate,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1
                    )
                    ser.dtr = True
                    ser.rts = True
                    time.sleep(2)
                    ser.reset_input_buffer()
                    ser.timeout = 120
                    self.connected.emit(ser, port)
                    return
                except Exception as e:
                    self.log.emit(f"Connection failed on {port}: {e}")
                    time.sleep(1)


class SerialWorker(QThread):
    result_ready  = pyqtSignal(bytes)
    error_signal  = pyqtSignal(str)

    def __init__(self, ser, command_bytes, parent=None):
        super().__init__(parent)
        self.ser = ser
        self.command_bytes = command_bytes

    def run(self):
        try:
            self.ser.write(serial.to_bytes(self.command_bytes))
            self.ser.flushInput()
            self.ser.flushOutput()
            data = self.ser.read(46)
            self.result_ready.emit(data)
        except Exception as e:
            self.error_signal.emit(str(e))


class SequentialHomingWorker(QThread):
    axis_done  = pyqtSignal(str, str, str)
    all_done   = pyqtSignal()
    raw_data   = pyqtSignal(bytes)  # <--- Emit raw data continuously for UI encoders

    def __init__(self, ser, commands, parent=None):
        super().__init__(parent)
        self.ser      = ser
        self.commands = commands

    SUCCESS = b'\x00\xFA'

    def run(self):
        for cmd, label_key, timeout_sec in self.commands:
            try:
                old_timeout = self.ser.timeout
                self.ser.timeout = timeout_sec
                self.ser.write(serial.to_bytes(cmd))
                self.ser.flushInput()
                self.ser.flushOutput()
                data = self.ser.read(46)
                self.ser.timeout = old_timeout

                self.raw_data.emit(data)  # Keep the encoders updated

                if data and len(data) >= 4 and data[2:4] == self.SUCCESS:
                    self.axis_done.emit(label_key, "Executed!", "#a6e3a1")
                else:
                    err = data[2:4].hex() if data and len(data) >= 4 else "no response"
                    self.axis_done.emit(label_key, f"Error: {err}", "#f38ba8")
            except Exception as e:
                self.axis_done.emit(label_key, f"Error: {e}", "#f38ba8")
        self.all_done.emit()


class StressTestWorker(QThread):
    loop_update  = pyqtSignal(int, int)    
    finished_all = pyqtSignal(bool)       
    log_signal   = pyqtSignal(str)         
    raw_data     = pyqtSignal(bytes)  # <--- Emit raw data continuously for UI encoders

    def __init__(self, ser, iterations, goto_coords, parent=None):
        super().__init__(parent)
        self.ser = ser
        self.iterations = iterations
        self.goto_coords = goto_coords
        self._abort = False

    def abort(self):
        self._abort = True

    def _send_and_wait(self, cmd_bytes, timeout=120):
        old_timeout = self.ser.timeout
        self.ser.timeout = timeout
        self.ser.write(serial.to_bytes(cmd_bytes))
        self.ser.flushInput()
        self.ser.flushOutput()
        data = self.ser.read(46)
        self.ser.timeout = old_timeout
        self.raw_data.emit(data)  # Keep the encoders updated
        return data

    def run(self):
        for i in range(self.iterations):
            if self._abort:
                self.log_signal.emit(f"Stress test aborted at loop {i}")
                self.finished_all.emit(False)
                return

            self.loop_update.emit(i + 1, self.iterations)
            self.log_signal.emit(f"Starting loop {i + 1} of {self.iterations}")

            try:
                self._send_and_wait(list(b'\x7C\x00'))
                self._send_and_wait(list(b'\x7A\x00'))
                self._send_and_wait(list(b'\x7B\x00'))

                self._send_and_wait(list(get_command_for_value_y(self.goto_coords['y'])))
                self._send_and_wait(list(get_command_for_value_x(self.goto_coords['x'])))
                self._send_and_wait(list(get_command_for_value_z(self.goto_coords['z'])))
            except Exception as e:
                self.log_signal.emit(f"Error in loop {i + 1}: {e}")
                self.finished_all.emit(False)
                return

        self.log_signal.emit(f"Stress test completed: {self.iterations} loops")
        self.finished_all.emit(True)


# ──────────────────────────────────────────────────────────────────────────────
# WIDGET
# ──────────────────────────────────────────────────────────────────────────────
class HardwareControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        config = get_config()
        hw = config.get('hardware', {})
        self.baudrate = hw.get('baudrate', 9600)
        self.sudo_pw = config.get('app', {}).get('sudo_password', 'sigvet123')
        self.ser = None
        self._workers = []

        # Motor step state
        self.x_step = 0
        self.y_step = 0
        self.z_step = 0
        self.turret_step = 0

        self._build_ui()
        QTimer.singleShot(200, self._init_serial)

    # ── Serial init ──────────────────────────────────────────────────────────
    def _init_serial(self):
        self._set_status("Initialising serial…", "#f9e2af")
        self._conn_worker = ConnectionWorker(self.baudrate, self.sudo_pw, self)
        self._conn_worker.connected.connect(self._on_connected)
        self._conn_worker.log.connect(lambda msg: self._set_status(msg, "#f9e2af"))
        self._conn_worker.start()

    def _on_connected(self, ser_obj, port_name):
        self.ser = ser_obj
        self._set_status(f"✓ Connected: {port_name} @ {self.baudrate} baud", "#a6e3a1")

    def _set_status(self, text, colour="#f9e2af"):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"color: {colour}; font-weight: bold; font-size: 13px;"
        )

    # ── EXACT "receive_data()" MIRROR FOR ENCODERS ───────────────────────────
    def _process_received_data(self, data: bytes):
        """Unified method identical to Original Code 2's receive_data() UI updating."""
        if not data or len(data) < 46:
            return

        # Status Error Check
        rx_raw = data[2:4]
        if rx_raw == b'\x00\xFA':
            self._set_status("✓ No Error in PCB", "#a6e3a1")
        else:
            err_msg = ERROR_MAP.get(rx_raw, f"Error: {rx_raw.hex()}")
            self._set_status(f"⚠ {err_msg}", "#f38ba8")

        # Parse & Update Labels
        try:
            current_x_position = bytes_to_int(data[4:8])[0]
            current_y_position = bytes_to_int(data[8:12])[0]
            current_z_position = bytes_to_int(data[12:16])[0]
            current_turret_position = bytes_to_int(data[16:20])[0]
            firmware_version = struct.unpack('>H', b'\x00' + data[39:40])[0]

            self.lbl_posX.setText(str(current_x_position))
            self.lbl_posY.setText(str(current_y_position))
            self.lbl_posZ.setText(str(current_z_position))
            self.lbl_posT.setText(str(current_turret_position))
            self.lbl_fw.setText(str(firmware_version))
        except Exception as e:
            print(f"Error parsing encoder data: {e}")

    # ── Async send ───────────────────────────────────────────────────────────
    def _send(self, cmd: list, label_key=None):
        if not self.ser:
            self._set_status("Not connected", "#f38ba8")
            return
        w = SerialWorker(self.ser, cmd, self)
        w.result_ready.connect(lambda data, k=label_key: self._on_result(data, k))
        w.error_signal.connect(lambda e: self._set_status(f"Error: {e}", "#f38ba8"))
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(w)
        w.start()

    def _on_result(self, data: bytes, label_key=None):
        if not data or len(data) < 46:
            return
            
        rx = data[2:4]
        if rx == b'\x00\xFA':
            error_text = "Executed!"
            err_colour = "#a6e3a1"
        else:
            error_text = "Error!"
            err_colour = "#f38ba8"

        if label_key and label_key in self._status_labels:
            lbl = self._status_labels[label_key]
            lbl.setText(error_text)
            lbl.setStyleSheet(f"color: {err_colour}; font-size: 12px;")

        # Push to the unified UI Updater
        self._process_received_data(data)

    # ──────────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._status_labels = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #181825; border-bottom: 1px solid #313244;")
        header.setFixedHeight(56)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 8, 16, 8)

        self.btn_back = QPushButton("← BACK TO MENU")
        self.btn_back.setObjectName("SummaryButton")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedHeight(38)

        title = QLabel("Hardware Control")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #89b4fa; letter-spacing: 2px;")

        self.lbl_status = QLabel("Initialising serial…")
        self.lbl_status.setStyleSheet("color: #f9e2af; font-weight: bold;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight)

        h_lay.addWidget(self.btn_back)
        h_lay.addSpacing(16)
        h_lay.addWidget(title)
        h_lay.addStretch()
        h_lay.addWidget(self.lbl_status)
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        content.setStyleSheet("background: #1e1e2e;")
        grid = QGridLayout(content)
        grid.setSpacing(14)
        grid.setContentsMargins(16, 16, 16, 16)

        grid.addWidget(self._homing_group(),        0, 0)
        grid.addWidget(self._results_group(),        0, 1)
        grid.addWidget(self._goto_group(),           1, 0)
        grid.addWidget(self._stress_test_wp_group(), 1, 1)
        grid.addWidget(self._device_ops_group(),     2, 0)
        grid.addWidget(self._stress_test_wop_group(), 2, 1)
        grid.addWidget(self._lights_group(),         3, 0, 1, 2)
        grid.addWidget(self._instant_travel_group(), 0, 2, 4, 1)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 3)

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        self.btn_back_bottom = QPushButton("← BACK TO MENU")
        self.btn_back_bottom.setObjectName("SummaryButton")
        self.btn_back_bottom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_bottom.setFixedHeight(48)
        self.btn_back_bottom.setStyleSheet(
            "QPushButton { background: #f97316; color: #ffffff; border: none;"
            " border-radius: 8px; font-weight: 800; font-size: 14px; letter-spacing: 1px; }"
            "QPushButton:hover { background: #ea6c0a; }"
            "QPushButton:pressed { background: #dc5c00; }"
        )
        root.addWidget(self.btn_back_bottom)

    @staticmethod
    def _make_group(title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                background: #181825;
                border: 1.5px solid #313244;
                border-radius: 10px;
                margin-top: 14px;
                font-size: 13px;
                font-weight: 700;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #89b4fa;
            }
        """)
        return g

    @staticmethod
    def _action_btn(text, colour="#3b82f6", text_colour="#ffffff") -> QPushButton:
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(
            f"background: {colour}; color: {text_colour}; border: none;"
            f" border-radius: 6px; padding: 7px 10px; font-weight: 700; font-size: 12px;"
        )
        return b

    @staticmethod
    def _input_field(default="0") -> QLineEdit:
        e = QLineEdit(default)
        e.setStyleSheet(
            "background: #313244; color: #cdd6f4; border: 1.5px solid #45475a;"
            " border-radius: 6px; padding: 6px 10px; font-size: 13px;"
        )
        e.setFixedHeight(36)
        return e

    def _status_lbl(self, key: str) -> QLabel:
        l = QLabel("Ready")
        l.setStyleSheet("color: #585b70; font-size: 12px;")
        self._status_labels[key] = l
        return l

    # ── Homing ───────────────────────────────────────────────────────────────
    def _home_axis(self, axis: str, cmd: list, label_key: str):
        # MUST zero out internal python step tracker just like Code 2
        if axis == 'x': self.x_step = 0
        elif axis == 'y': self.y_step = 0
        elif axis == 'z': self.z_step = 0
        elif axis == 't': self.turret_step = 0
        self._send(cmd, label_key=label_key)

    def _homing_group(self):
        g = self._make_group("Homing")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        rows = [
            ("Home X",   lambda: self._home_axis('x', list(b'\x7A\x00'), "Home X"), "Home X"),
            ("Home Y",   lambda: self._home_axis('y', list(b'\x7B\x00'), "Home Y"), "Home Y"),
            ("Home Z",   lambda: self._home_axis('z', list(b'\x7C\x00'), "Home Z"), "Home Z"),
            ("Home All", self._home_all,                                            "Home All"),
        ]
        for i, (txt, cb, key) in enumerate(rows):
            b = self._action_btn(txt, "#3b82f6")
            b.clicked.connect(cb)
            sl = self._status_lbl(key)
            lay.addWidget(b,  i, 0)
            lay.addWidget(sl, i, 1)
        return g

    def _home_all(self):
        if not self.ser:
            self._set_status("Not connected", "#f38ba8")
            return
        self._set_status("Homing All axes sequentially…", "#f9e2af")
        commands = [
            (list(b'\x7C\x00'), "Home Z",   120),
            (list(b'\x7A\x00'), "Home X",   120),
            (list(b'\x7B\x00'), "Home Y",   120),
            (list(b'\x7D\x00'), "Home All", 120),
        ]
        worker = SequentialHomingWorker(self.ser, commands, self)
        worker.axis_done.connect(self._on_seq_axis_done)
        worker.all_done.connect(self._on_seq_all_done)
        worker.raw_data.connect(self._process_received_data)  # Keep encoders live
        self._workers.append(worker)
        worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None)
        worker.start()

    @pyqtSlot(str, str, str)
    def _on_seq_axis_done(self, label_key, text, colour):
        if label_key in self._status_labels:
            lbl = self._status_labels[label_key]
            lbl.setText(text)
            lbl.setStyleSheet(f"color: {colour}; font-size: 12px;")
        self._set_status(f"[{label_key}] {text}", colour)

    @pyqtSlot()
    def _on_seq_all_done(self):
        self.x_step = self.y_step = self.z_step = 0
        self._set_status("Home All complete", "#a6e3a1")

    # ── Results ──────────────────────────────────────────────────────────────
    def _results_group(self):
        g = self._make_group("Live Results")
        lay = QGridLayout(g)
        lay.setSpacing(6)

        self.lbl_fw   = QLabel("—")
        self.lbl_posX = QLabel("—")
        self.lbl_posY = QLabel("—")
        self.lbl_posZ = QLabel("—")
        self.lbl_posT = QLabel("—")

        value_style = "color: #a6e3a1; font-weight: bold; font-size: 13px; font-family: monospace;"
        label_style = "color: #a6adc8; font-size: 12px; font-weight: 600;"

        rows = [
            ("Firmware Ver:", self.lbl_fw),
            ("X Position:",   self.lbl_posX),
            ("Y Position:",   self.lbl_posY),
            ("Z Position:",   self.lbl_posZ),
            ("T Position:",   self.lbl_posT),
        ]
        for i, (txt, val_lbl) in enumerate(rows):
            tl = QLabel(txt)
            tl.setStyleSheet(label_style)
            val_lbl.setStyleSheet(value_style)
            lay.addWidget(tl,      i, 0)
            lay.addWidget(val_lbl, i, 1)
        return g

    # ── GoTo ─────────────────────────────────────────────────────────────────
    def _goto_group(self):
        g = self._make_group("GoTo (absolute steps)")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        self._goto_x = self._input_field("100000")
        self._goto_y = self._input_field("100000")
        self._goto_z = self._input_field("10000")

        rows = [
            ("GoTo X", self._goto_x, lambda: self._go_to("x")),
            ("GoTo Y", self._goto_y, lambda: self._go_to("y")),
            ("GoTo Z", self._goto_z, lambda: self._go_to("z")),
        ]
        for i, (txt, inp, cb) in enumerate(rows):
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #a6adc8; font-weight: 600;")
            enter = self._action_btn("Enter", "#89b4fa", "#1e1e2e")
            enter.clicked.connect(cb)
            lay.addWidget(lbl,   i, 0)
            lay.addWidget(inp,   i, 1)
            lay.addWidget(enter, i, 2)
        return g

    def _go_to(self, axis: str):
        try:
            if axis == "x":
                v = int(self._goto_x.text()); self.x_step = v
                self._send(list(get_command_for_value_x(v)))
            elif axis == "y":
                v = int(self._goto_y.text()); self.y_step = v
                self._send(list(get_command_for_value_y(v)))
            elif axis == "z":
                v = int(self._goto_z.text()); self.z_step = v
                self._send(list(get_command_for_value_z(v)))
        except ValueError:
            self._set_status("Invalid step value", "#f38ba8")

    # ── Device Ops ───────────────────────────────────────────────────────────
    def _device_ops_group(self):
        g = self._make_group("Device Operations")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        eject  = self._action_btn("⏏  Eject",  "#f38ba8", "#1e1e2e")
        insert = self._action_btn("⏩  Insert", "#3b82f6")
        eject.clicked.connect(self._eject)
        insert.clicked.connect(self._insert)
        lay.addWidget(eject,  0, 0)
        lay.addWidget(insert, 0, 1)
        return g

    def _eject(self):
        self._send(list(b'\x7C\x00'))                     
        QTimer.singleShot(400, lambda: self._send(list(get_command_for_value_y(10000))))
        QTimer.singleShot(800, lambda: self._send(list(get_command_for_value_x(490000))))

    def _insert(self):
        self._send(list(b'\x7C\x00'))                     
        QTimer.singleShot(400, lambda: self._send(list(get_command_for_value_x(250000))))
        QTimer.singleShot(800, lambda: self._send(list(get_command_for_value_y(140000))))

    # ── Stress Test WP ───────────────────────────────────────────────────────
    def _stress_test_wp_group(self):
        g = self._make_group("Stress Test WP")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        lbl_loops = QLabel("Loops:")
        lbl_loops.setStyleSheet("color: #a6adc8; font-weight: 600;")

        self._wp_combo = QComboBox()
        self._wp_combo.addItems(["10", "50", "100", "500", "1000", "2000"])
        self._wp_combo.setStyleSheet(
            "background: #313244; color: #cdd6f4; border: 1.5px solid #45475a;"
            " border-radius: 6px; padding: 4px 8px; font-size: 13px;"
        )

        btn_start = self._action_btn("Start Test", "#f97316", "#ffffff")
        btn_start.clicked.connect(self._start_stress_wp)

        self._wp_status = QLabel("Ready")
        self._wp_status.setStyleSheet("color: #585b70; font-size: 12px;")

        lay.addWidget(lbl_loops,       0, 0)
        lay.addWidget(self._wp_combo,  0, 1)
        lay.addWidget(btn_start,       1, 0)
        lay.addWidget(self._wp_status, 1, 1)
        return g

    def _start_stress_wp(self):
        if not self.ser:
            self._set_status("Not connected", "#f38ba8")
            return
        iterations = int(self._wp_combo.currentText())
        coords = {'y': 54000, 'x': 490000, 'z': 200000}
        worker = StressTestWorker(self.ser, iterations, coords, self)
        worker.loop_update.connect(lambda cur, tot: self._wp_status.setText(f"Loop {cur}/{tot}"))
        worker.log_signal.connect(lambda msg: print(f"[StressWP] {msg}"))
        worker.raw_data.connect(self._process_received_data) # Keep encoders live
        worker.finished_all.connect(lambda ok: self._wp_status.setText("✓ Done" if ok else "⚠ Stopped"))
        worker.finished_all.connect(lambda ok: self._wp_status.setStyleSheet(
                f"color: {'#a6e3a1' if ok else '#f38ba8'}; font-size: 12px;"
            ))
        self._workers.append(worker)
        worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None)
        worker.start()

    # ── Stress Test WOP ──────────────────────────────────────────────────────
    def _stress_test_wop_group(self):
        g = self._make_group("Stress Test WOP")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        lbl_loops = QLabel("Loops:")
        lbl_loops.setStyleSheet("color: #a6adc8; font-weight: 600;")

        self._wop_combo = QComboBox()
        self._wop_combo.addItems(["10", "50", "100", "500", "1000", "2000"])
        self._wop_combo.setStyleSheet(
            "background: #313244; color: #cdd6f4; border: 1.5px solid #45475a;"
            " border-radius: 6px; padding: 4px 8px; font-size: 13px;"
        )

        btn_start = self._action_btn("Start Test", "#f97316", "#ffffff")
        btn_start.clicked.connect(self._start_stress_wop)

        self._wop_status = QLabel("Ready")
        self._wop_status.setStyleSheet("color: #585b70; font-size: 12px;")

        lay.addWidget(lbl_loops,        0, 0)
        lay.addWidget(self._wop_combo,  0, 1)
        lay.addWidget(btn_start,        1, 0)
        lay.addWidget(self._wop_status, 1, 1)
        return g

    def _start_stress_wop(self):
        if not self.ser:
            self._set_status("Not connected", "#f38ba8")
            return
        iterations = int(self._wop_combo.currentText())
        coords = {'y': 220000, 'x': 320000, 'z': 200000}
        worker = StressTestWorker(self.ser, iterations, coords, self)
        worker.loop_update.connect(lambda cur, tot: self._wop_status.setText(f"Loop {cur}/{tot}"))
        worker.log_signal.connect(lambda msg: print(f"[StressWOP] {msg}"))
        worker.raw_data.connect(self._process_received_data) # Keep encoders live
        worker.finished_all.connect(lambda ok: self._wop_status.setText("✓ Done" if ok else "⚠ Stopped"))
        worker.finished_all.connect(lambda ok: self._wop_status.setStyleSheet(
                f"color: {'#a6e3a1' if ok else '#f38ba8'}; font-size: 12px;"
            ))
        self._workers.append(worker)
        worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None)
        worker.start()

    # ── Lights ───────────────────────────────────────────────────────────────
    def _lights_group(self):
        g = self._make_group("Lights & Motor Control")
        lay = QGridLayout(g)
        lay.setSpacing(8)

        self._light_inputs = {}
        items = [
            ("White Light",      "1500", lambda: self._set_light("White Light",      get_command_for_value_led)),
            ("UV Light",         "1500", lambda: self._set_light("UV Light",         get_command_for_value_uv_led)),
            ("Backlight",        "0",    lambda: self._set_light("Backlight",        get_command_for_value_backlight)),
            ("Barcode Light",    "1500", lambda: self._set_light("Barcode Light",    get_command_for_value_barcode_led)),
            ("Motor Torque Off", "100",  lambda: self._set_light("Motor Torque Off", get_command_for_value_MTorque)),
        ]

        for i, (name, default, cb) in enumerate(items):
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #a6adc8; font-weight: 600;")
            inp = self._input_field(default)
            self._light_inputs[name] = inp
            enter = self._action_btn("Set", "#cba6f7", "#1e1e2e")
            enter.clicked.connect(cb)
            sl = self._status_lbl(name)
            lay.addWidget(lbl,   i, 0)
            lay.addWidget(inp,   i, 1)
            lay.addWidget(enter, i, 2)
            lay.addWidget(sl,    i, 3)
        return g

    def _set_light(self, name: str, cmd_fn):
        try:
            v = int(self._light_inputs[name].text())

            if name in ["White Light", "UV Light", "Barcode Light"] and v > 2001:
                self._set_status("This is Wrong Value...", "#f38ba8")
                return
            if name == "Backlight" and v >= 10000:
                self._set_status("This is Wrong Value...", "#f38ba8")
                return
            if name == "Motor Torque Off" and v > 500:
                self._set_status("This is Wrong Value...", "#f38ba8")
                return

            self._send(list(cmd_fn(v)), label_key=name)
        except ValueError:
            self._set_status("Invalid value", "#f38ba8")

    # ── Instant Travel ───────────────────────────────────────────────────────
    def _instant_travel_group(self):
        g = self._make_group("Instant Travel (Incremental Steps)")
        lay = QGridLayout(g)
        lay.setSpacing(6)

        x_steps = [10000, 2000, 100, 50, 25, -25, -50, -100, -2000, -10000]
        y_steps = x_steps[:]
        z_steps = [2000, 100, 50, 10, 5, -5, -10, -50, -100, -2000]

        for col, name in enumerate(["  X Axis  ", "  Y Axis  ", "  Z Axis  "]):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "color: #89b4fa; font-weight: 800; font-size: 13px;"
                " border-bottom: 1px solid #313244; padding-bottom: 4px;"
            )
            lay.addWidget(lbl, 0, col)

        def btn_colour(val):
            return ("#a6e3a1", "#1e1e2e") if val > 0 else ("#f38ba8", "#1e1e2e")

        for row, (xv, yv, zv) in enumerate(zip(x_steps, y_steps, z_steps)):
            for col, (val, axis) in enumerate([(xv, 'x'), (yv, 'y'), (zv, 'z')]):
                sign = "++" if val > 0 else "--"
                txt  = f"  {abs(val):>6,d} {sign}  "
                fg, bg = btn_colour(val)
                b = QPushButton(txt)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
                b.setStyleSheet(
                    f"background: {fg}; color: {bg}; border: none;"
                    f" border-radius: 6px; padding: 6px 4px; font-weight: 700;"
                )
                b.clicked.connect(
                    lambda checked=False, v=val, a=axis: self._instant(a, v)
                )
                lay.addWidget(b, row + 1, col)

        return g

    def _instant(self, axis: str, delta: int):
        if axis == 'x':
            self.x_step += delta
            self._send(list(get_command_for_value_x(self.x_step)))
        elif axis == 'y':
            self.y_step += delta
            self._send(list(get_command_for_value_y(self.y_step)))
        elif axis == 'z':
            self.z_step += delta
            self._send(list(get_command_for_value_z(self.z_step)))