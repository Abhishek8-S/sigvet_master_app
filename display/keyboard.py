from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QApplication, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt

class TouchKeyboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_caps = False
        self.is_symbols = False
        self.target_widget = None
        
        self.key_layout = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', '_']
        ]
        self.symbol_layout = [
            ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '`'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?', '~']
        ]
        
        self.key_buttons = []
        self.setup_ui()

    def set_target(self, widget):
        self.target_widget = widget

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 1. Main Keys Area
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        
        for r, row in enumerate(self.key_layout):
            row_btns = []
            for c, key in enumerate(row):
                btn = QPushButton(key)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setSizePolicy(btn.sizePolicy().Policy.Expanding, btn.sizePolicy().Policy.Expanding)
                btn.setMinimumHeight(40)
                btn.setStyleSheet("""
                    QPushButton { background-color: #313244; color: #ffffff; border-radius: 4px; font-size: 16px; font-weight: bold; }
                    QPushButton:pressed { background-color: #89b4fa; }
                """)
                btn.clicked.connect(lambda checked, k=key: self.press_key(k))
                grid_layout.addWidget(btn, r, c)
                row_btns.append(btn)
            self.key_buttons.append(row_btns)
            
        main_layout.addLayout(grid_layout)
        
        # 2. Bottom Function Row
        func_layout = QHBoxLayout()
        func_layout.setSpacing(5)
        
        self.btn_caps = self.create_func_btn("CAPS", self.toggle_caps)
        self.btn_sym = self.create_func_btn("SYM", self.toggle_symbols)
        btn_space = self.create_func_btn("SPACE", lambda: self.press_key(" "))
        btn_space.setStyleSheet("""
            QPushButton { background-color: #45475a; color: #ffffff; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:pressed { background-color: #89b4fa; }
        """)
        btn_backspace = self.create_func_btn("⌫", self.backspace)
        btn_enter = self.create_func_btn("ENTER", self.enter)
        
        func_layout.addWidget(self.btn_caps, 1)
        func_layout.addWidget(self.btn_sym, 1)
        func_layout.addWidget(btn_space, 4)
        func_layout.addWidget(btn_backspace, 1)
        func_layout.addWidget(btn_enter, 1)
        
        main_layout.addLayout(func_layout)
        
        # 3. Arrow Keys Row
        arrow_layout = QHBoxLayout()
        arrow_layout.setSpacing(20) # Much more space between arrows
        arrow_layout.addStretch()
        
        btn_left = self.create_arrow_btn("←", lambda: self.press_key("Left"))
        btn_up = self.create_arrow_btn("↑", lambda: self.press_key("Up"))
        btn_down = self.create_arrow_btn("↓", lambda: self.press_key("Down"))
        btn_right = self.create_arrow_btn("→", lambda: self.press_key("Right"))
        
        arrow_layout.addWidget(btn_left)
        arrow_layout.addWidget(btn_up)
        arrow_layout.addWidget(btn_down)
        arrow_layout.addWidget(btn_right)
        arrow_layout.addStretch()
        
        main_layout.addLayout(arrow_layout)

    def create_arrow_btn(self, text, command):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(60) # Taller for touch
        btn.setMinimumWidth(80)  # Wider for touch
        btn.setStyleSheet("""
            QPushButton { background-color: #45475a; color: #ffffff; border-radius: 8px; font-size: 24px; font-weight: bold; }
            QPushButton:pressed { background-color: #89b4fa; }
        """)
        btn.clicked.connect(command)
        return btn

    def create_func_btn(self, text, command):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(45)
        btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: #ffffff; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:pressed { background-color: #2563eb; }
        """)
        btn.clicked.connect(command)
        return btn

    def press_key(self, key):
        target = self.target_widget
        if not target:
            return
            
        if key in ['Left', 'Right', 'Up', 'Down']:
            # Implement simple arrow key support via QKeyEvent or basic methods
            if isinstance(target, QLineEdit):
                if key == 'Left': target.cursorBackward(False)
                elif key == 'Right': target.cursorForward(False)
            elif isinstance(target, QTextEdit):
                # TextEdit uses cursor
                cursor = target.textCursor()
                if key == 'Left': cursor.movePosition(cursor.MoveOperation.Left)
                elif key == 'Right': cursor.movePosition(cursor.MoveOperation.Right)
                elif key == 'Up': cursor.movePosition(cursor.MoveOperation.Up)
                elif key == 'Down': cursor.movePosition(cursor.MoveOperation.Down)
                target.setTextCursor(cursor)
            return

        char = key.upper() if self.is_caps else key
        
        if isinstance(target, QLineEdit):
            target.insert(char)
        elif isinstance(target, QTextEdit):
            target.insertPlainText(char)

    def backspace(self):
        target = self.target_widget
        if not target: return
        if isinstance(target, QLineEdit):
            target.backspace()
        elif isinstance(target, QTextEdit):
            target.textCursor().deletePreviousChar()

    def enter(self):
        target = self.target_widget
        if not target: return
        if isinstance(target, QTextEdit):
            target.insertPlainText('\\n')

    def toggle_caps(self):
        self.is_caps = not self.is_caps
        color = "#e94560" if self.is_caps else "#3b82f6"
        self.btn_caps.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: #ffffff; border-radius: 4px; font-size: 14px; font-weight: bold; }}
            QPushButton:pressed {{ background-color: #2563eb; }}
        """)
        self.update_labels()

    def toggle_symbols(self):
        self.is_symbols = not self.is_symbols
        color = "#e94560" if self.is_symbols else "#3b82f6"
        self.btn_sym.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: #ffffff; border-radius: 4px; font-size: 14px; font-weight: bold; }}
            QPushButton:pressed {{ background-color: #2563eb; }}
        """)
        self.update_labels()

    def update_labels(self):
        layout = self.symbol_layout if self.is_symbols else self.key_layout
        for r, row in enumerate(layout):
            for c, key_char in enumerate(row):
                if r < len(self.key_buttons) and c < len(self.key_buttons[r]):
                    disp = key_char.upper() if (self.is_caps and not self.is_symbols) else key_char
                    self.key_buttons[r][c].setText(disp)
