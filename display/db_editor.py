import sqlite3
import os
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QStackedWidget, QFileDialog, QMessageBox, QFrame, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# We use the config loader for system database credentials and paths.
from core.config_loader import get_config
from display.keyboard import TouchKeyboard


def _make_writable(path):
    """
    Ensure the user has write access to both the .db file itself, and the parent 
    directory, to accommodate SQLite's WAL temp files.
    """
    try:
        cfg = get_config()
        sudo_pw = cfg.get('app', {}).get('sudo_password', 'sigvet123')
        
        # 1. DB file
        subprocess.run(
            ['sudo', '-S', 'chmod', '666', path],
            input=f"{sudo_pw}\n",
            capture_output=True, text=True, timeout=10
        )
        
        # 2. Directory
        parent_dir = os.path.dirname(path)
        if parent_dir and os.path.exists(parent_dir):
            subprocess.run(
                ['sudo', '-S', 'chmod', '777', parent_dir],
                input=f"{sudo_pw}\n",
                capture_output=True, text=True, timeout=10
            )
    except Exception:
        pass


class DBEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection = None
        self.cursor = None
        self.latest_row_data_map = {}
        self.original_values = {}
        self.entries = {}
        self.current_edit_table = ""

        # Using a stacked widget to transition smoothly from landing to table to edit mode.
        self.stack = QStackedWidget(self)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        self.create_landing_view()
        self.create_tables_view()
        self.create_edit_view()

    # ── Landing Page ──────────────────────────────────────────────────────────
    def create_landing_view(self):
        self.landing = QWidget()
        layout = QVBoxLayout(self.landing)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        title = QLabel("System DB Editor")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px;")
        layout.addWidget(title)

        btn_load = QPushButton("LOAD SYSTEM DB (dll.db)")
        btn_load.setObjectName("StartButton")
        btn_load.setFixedSize(400, 60)
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load.clicked.connect(self.load_default_db)
        layout.addWidget(btn_load, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_browse = QPushButton("BROWSE OTHER DB...")
        btn_browse.setObjectName("SummaryButton")
        btn_browse.setFixedSize(400, 60)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self.load_db)
        layout.addWidget(btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btn_back = QPushButton("BACK TO MENU")
        self.btn_back.setObjectName("CancelButton")
        self.btn_back.setFixedSize(400, 60)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(self.landing) # Index 0

    # ── Tables List Page ──────────────────────────────────────────────────────
    def create_tables_view(self):
        self.tables_widget = QWidget()
        layout = QVBoxLayout(self.tables_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        top_bar = QHBoxLayout()

        self.btn_back_tables = QPushButton("BACK TO MENU")
        self.btn_back_tables.setObjectName("CancelButton")
        self.btn_back_tables.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_tables.clicked.connect(self.show_landing)

        btn_reload = QPushButton("RELOAD DB")
        btn_reload.setObjectName("InfoButton")
        btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reload.clicked.connect(self.load_default_db)

        btn_open = QPushButton("OPEN OTHER")
        btn_open.setObjectName("InfoButton")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.clicked.connect(self.load_db)

        top_bar.addWidget(self.btn_back_tables)
        top_bar.addWidget(btn_reload)
        top_bar.addWidget(btn_open)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.tables_scroll = QScrollArea()
        self.tables_scroll.setWidgetResizable(True)
        self.tables_scroll.setStyleSheet("background: transparent; border: none;")

        self.tables_container = QWidget()
        self.tables_layout = QVBoxLayout(self.tables_container)
        self.tables_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.tables_scroll.setWidget(self.tables_container)
        layout.addWidget(self.tables_scroll, stretch=1)

        self.stack.addWidget(self.tables_widget) # Index 1

    # ── Edit Page (Giant Keyboard Appears Here) ───────────────────────────────
    def create_edit_view(self):
        self.edit_widget = QWidget()
        layout = QVBoxLayout(self.edit_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QHBoxLayout()
        self.edit_title = QLabel("EDITING: ")
        self.edit_title.setObjectName("Header")
        self.edit_title.setStyleSheet("font-size: 24px;")

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setObjectName("CancelButton")
        btn_cancel.setFixedSize(120, 40)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        header.addWidget(self.edit_title)
        header.addStretch()
        header.addWidget(btn_cancel)
        layout.addLayout(header)

        # Body - split between form on top and keyboard on bottom
        self.edit_scroll = QScrollArea()
        self.edit_scroll.setWidgetResizable(True)
        self.edit_scroll.setStyleSheet("background: transparent; border: none;")
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.edit_scroll.setWidget(self.form_container)
        
        layout.addWidget(self.edit_scroll, stretch=3)

        self.btn_save_new = QPushButton("💾  SAVE NEW VERSION")
        self.btn_save_new.setObjectName("StartButton")
        self.btn_save_new.setMinimumHeight(60)
        self.btn_save_new.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.btn_save_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_new.clicked.connect(self.save_new)
        
        layout.addWidget(self.btn_save_new)

        self.keyboard = TouchKeyboard()
        layout.addWidget(self.keyboard, stretch=2)

        self.stack.addWidget(self.edit_widget) # Index 2

    def show_landing(self):
        self.stack.setCurrentIndex(0)

    # ── Database Logic ────────────────────────────────────────────────────────
    def load_default_db(self):
        self.db_path = get_config().get('paths', {}).get(
            'calib_db_path', "/opt/sigtuple/sigvet/dcm/dll.db"
        )
        if os.path.exists(self.db_path):
            # Always try to ensure write access before opening
            _make_writable(self.db_path)
            self._load_db_from_path(self.db_path)
        else:
            QMessageBox.critical(
                self, "File Not Found",
                f"System database not found at:\n{self.db_path}"
            )

    def load_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select DB", "", "Database Files (*.db)"
        )
        if path:
            # Always ensure write permissions before connecting
            _make_writable(path)
            self._load_db_from_path(path)

    def _load_db_from_path(self, path):
        try:
            if self.connection:
                self.connection.close()
            # WAL mode database connect
            self.connection = sqlite3.connect(path, isolation_level=None)
            self.connection.execute('pragma journal_mode=wal')
            self.cursor = self.connection.cursor()

            self.stack.setCurrentIndex(1)
            self.display_tables()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load database:\n{e}")

    def display_tables(self):
        # Clear existing tables
        while self.tables_layout.count():
            child = self.tables_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.latest_row_data_map = {}

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in self.cursor.fetchall() if not r[0].startswith("sqlite_")]

        if not tables:
            lbl = QLabel("No application tables found.")
            lbl.setStyleSheet("color: white; font-size: 18px;")
            self.tables_layout.addWidget(lbl)
            return

        for table in tables:
            self._render_table_card(table)

    def clean_col_name(self, name):
        """Simplifies very long column names for UI display."""
        n = name.replace("device__level__component__systems_microscope__", "") \
                .replace("imaging__component__systems_microscope__40x__condenser_camera__", "")
        if len(n) > 35:
            if "profile__" in n: return "..." + n.split("profile__", 1)[1]
            if "tray__" in n: return "..." + n.split("tray__", 1)[1]
        return n

    def get_pk(self, table):
        try:
            self.cursor.execute(f"PRAGMA table_info('{table}')")
            for r in self.cursor.fetchall():
                if r[5] == 1: return r[1]
        except Exception:
            pass
        return None

    def _render_table_card(self, table):
        pk = self.get_pk(table)
        order = f'ORDER BY "{pk}" DESC' if pk else "ORDER BY ROWID DESC"

        self.cursor.execute(f'SELECT * FROM "{table}" {order} LIMIT 1')
        cols = [d[0] for d in self.cursor.description]
        row = self.cursor.fetchone()

        self.latest_row_data_map[table] = {"cols": cols, "data": row}

        card = QFrame()
        card.setObjectName("DataPanel")
        card_layout = QVBoxLayout(card)

        # Header
        hdr = QHBoxLayout()
        title = QLabel(f"{table.upper()}")
        title.setObjectName("SubHeader")
        
        btn_edit = QPushButton("DUPLICATE & EDIT NEW")
        btn_edit.setObjectName("StartButton")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setFixedSize(260, 45) # Increased width and height to fit text comfortably
        btn_edit.setStyleSheet("font-weight: bold; font-size: 14px;")
        btn_edit.clicked.connect(lambda _, t=table: self.open_edit_view(t))

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(btn_edit)
        card_layout.addLayout(hdr)

        if not row:
            lbl = QLabel("No Data in Table")
            lbl.setStyleSheet("color: #a0a0a0; padding: 20px;")
            card_layout.addWidget(lbl)
            self.tables_layout.addWidget(card)
            return

        # Body - last few entries
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(4)
        content_layout.setContentsMargins(0,0,0,0)

        for i, col in enumerate(cols):
            val = row[i] if row[i] is not None else "NULL"
            
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(10, 5, 10, 5)
            
            bg_color = "#16213e" if i % 2 == 0 else "transparent"
            row_w.setStyleSheet(f"background: {bg_color}; border-radius: 4px;")

            lbl_col = QLabel(self.clean_col_name(col))
            lbl_col.setFixedWidth(200)
            lbl_col.setStyleSheet("color: #a0a0a0; font-family: 'Consolas'; font-size: 13px; font-weight: bold;")
            
            lbl_val = QLabel(str(val))
            lbl_val.setWordWrap(True)
            lbl_val.setStyleSheet("color: white; font-size: 14px;")

            row_l.addWidget(lbl_col)
            row_l.addWidget(lbl_val, stretch=1)
            content_layout.addWidget(row_w)

        card_layout.addWidget(content_widget)
        self.tables_layout.addWidget(card)


    def open_edit_view(self, table):
        info = self.latest_row_data_map.get(table)
        if not info or not info['data']: return

        self.current_edit_table = table
        self.edit_title.setText(f"EDITING: {table}")

        # Clear form
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.entries = {}
        self.original_values[table] = {}
        cols, vals = info['cols'], info['data']

        now_date = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M:%S")

        for i, col in enumerate(cols):
            val = vals[i]
            self.original_values[table][col] = val

            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            
            lbl = QLabel(self.clean_col_name(col))
            lbl.setFixedWidth(200)
            lbl.setStyleSheet("color: #a0a0a0; font-weight: bold;")
            row_l.addWidget(lbl)

            if col == 'id':
                ent = QLineEdit("AUTO (NEW)")
                ent.setReadOnly(True)
                ent.setStyleSheet("background: #111; color: #777; border: none; padding: 8px;")
                row_l.addWidget(ent, stretch=1)
            elif col == 'date':
                ent = QLineEdit(now_date)
                ent.setStyleSheet("background: #2a2a40; color: white; border: none; padding: 8px;")
                self.setup_keyboard_focus(ent)
                self.entries[col] = ent
                row_l.addWidget(ent, stretch=1)
            elif col == 'time':
                ent = QLineEdit(now_time)
                ent.setStyleSheet("background: #2a2a40; color: white; border: none; padding: 8px;")
                self.setup_keyboard_focus(ent)
                self.entries[col] = ent
                row_l.addWidget(ent, stretch=1)
            else:
                is_long = isinstance(val, str) and len(val) > 50
                if is_long:
                    ent = QTextEdit()
                    ent.setFixedHeight(100)
                    ent.setPlainText(str(val) if val else "")
                    ent.setStyleSheet("background: #2a2a40; color: white; border: none; padding: 8px;")
                else:
                    ent = QLineEdit(str(val) if val is not None else "")
                    ent.setStyleSheet("background: #2a2a40; color: white; border: none; padding: 8px;")
                
                self.setup_keyboard_focus(ent)
                self.entries[col] = ent
                row_l.addWidget(ent, stretch=1)

            self.form_layout.addWidget(row_w)

        self.stack.setCurrentIndex(2) # Switch to Edit View

    def setup_keyboard_focus(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.Type.FocusIn and hasattr(self, 'keyboard'):
            if isinstance(source, (QLineEdit, QTextEdit)):
                self.keyboard.set_target(source)
        return super().eventFilter(source, event)

    def save_new(self):
        if not self.current_edit_table: return
        table = self.current_edit_table
        
        info = self.latest_row_data_map.get(table)
        if not info: return
        cols = info['cols']

        try:
            new_data = {}
            pk = self.get_pk(table)

            for col in cols:
                if col == pk: continue

                if col in self.entries:
                    w = self.entries[col]
                    val = w.toPlainText() if isinstance(w, QTextEdit) else w.text()
                    new_data[col] = val
                else:
                    new_data[col] = self.original_values[table].get(col)

            cols_sql = [f'"{k}"' for k in new_data.keys()]
            placeholders = ','.join(['?']*len(new_data))

            sql = f'INSERT INTO "{table}" ({",".join(cols_sql)}) VALUES ({placeholders})'
            self.cursor.execute(sql, list(new_data.values()))
            
            # Since connection uses basic Isolation mode, this immediately writes to WAL
            
            QMessageBox.information(self, "Success", "Record Duplicated & Saved!")
            self.display_tables() # Refresh data
            self.stack.setCurrentIndex(1) # Back to tables view

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
