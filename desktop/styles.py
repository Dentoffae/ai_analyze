"""
Стили для PyQt6 приложения — тёмная тема в серых тонах
"""

DARK_THEME = """
/* === Основные стили === */
QMainWindow, QWidget {
    background-color: #181818;
    color: #f0f0f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

/* === Sidebar === */
#sidebar {
    background-color: #212121;
    border-right: 1px solid #3a3a3a;
}

#logo {
    color: #e0e0e0;
    font-size: 18px;
    font-weight: bold;
    padding: 20px;
    border-bottom: 1px solid #3a3a3a;
}

/* === Navigation Buttons === */
QPushButton#navButton {
    background-color: transparent;
    color: #b0b0b0;
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    font-size: 14px;
}

QPushButton#navButton:hover {
    background-color: #333333;
    color: #f0f0f0;
}

QPushButton#navButton:checked {
    background-color: rgba(163, 163, 163, 0.15);
    color: #e0e0e0;
    border: 1px solid rgba(163, 163, 163, 0.35);
}

/* === Cards === */
QFrame#card {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 12px;
}

QFrame#card:hover {
    border-color: #4a4a4a;
}

/* === Labels === */
QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #f0f0f0;
}

QLabel#subtitle {
    font-size: 14px;
    color: #b0b0b0;
}

QLabel#cardTitle {
    font-size: 16px;
    font-weight: 600;
    color: #f0f0f0;
}

QLabel#cardDescription {
    font-size: 13px;
    color: #b0b0b0;
}

QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #e0e0e0;
    margin-bottom: 8px;
}

/* === Text Input === */
QTextEdit, QLineEdit {
    background-color: #1c1c1c;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 12px;
    color: #f0f0f0;
    font-size: 14px;
}

QTextEdit:focus, QLineEdit:focus {
    border-color: #737373;
}

QTextEdit::placeholder, QLineEdit::placeholder {
    color: #787878;
}

/* === Primary Button === */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #525252, stop:1 #737373);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5c5c5c, stop:1 #808080);
}

QPushButton#primaryButton:disabled {
    background-color: #4a4a4a;
    color: #787878;
}

/* === Secondary Button === */
QPushButton#secondaryButton {
    background-color: #333333;
    color: #b0b0b0;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
}

QPushButton#secondaryButton:hover {
    background-color: #4a4a4a;
    color: #f0f0f0;
}

/* === Upload Zone === */
QFrame#uploadZone {
    background-color: #1c1c1c;
    border: 2px dashed #4a4a4a;
    border-radius: 12px;
    min-height: 200px;
}

QFrame#uploadZone:hover {
    border-color: #737373;
    background-color: rgba(163, 163, 163, 0.08);
}

/* === Results === */
QFrame#resultsCard {
    background-color: #2a2a2a;
    border: 1px solid #737373;
    border-radius: 12px;
}

QScrollArea#resultsScroll {
    background-color: transparent;
    border: none;
}

QScrollArea#resultsScroll > QWidget > QWidget {
    background-color: transparent;
}

QFrame#resultBlock {
    background-color: #212121;
    border-left: 3px solid #737373;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
}

/* === History === */
QFrame#historyItem {
    background-color: #212121;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 12px;
}

QFrame#historyItem:hover {
    border-color: #4a4a4a;
}

/* === ScrollArea === */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #212121;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5c5c5c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* === Progress/Loading === */
QProgressBar {
    background-color: #1c1c1c;
    border: none;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #525252, stop:1 #8a8a8a);
    border-radius: 4px;
}

/* === Tab Widget === */
QTabWidget::pane {
    border: none;
    background-color: transparent;
}

QTabBar::tab {
    background-color: transparent;
    color: #b0b0b0;
    padding: 12px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #e0e0e0;
    border-bottom: 2px solid #737373;
}

QTabBar::tab:hover:!selected {
    color: #f0f0f0;
}

/* === Status === */
QLabel#statusActive {
    color: #7a9e8e;
}

QLabel#statusError {
    color: #c45c5c;
}

/* === Tooltips === */
QToolTip {
    background-color: #2a2a2a;
    color: #f0f0f0;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 8px;
}
"""
