"""
Переиспользуемые виджеты UI
"""
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
)


class ScoreBar(QFrame):
    """Полоска оценки визуального стиля (0–10), как на сайте."""

    def __init__(self, score: int):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        value = QLabel(f"{score}/10")
        value.setStyleSheet("font-size: 32px; font-weight: bold; color: #e0e0e0;")

        bar = QProgressBar()
        bar.setRange(0, 10)
        bar.setValue(score)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        layout.addWidget(value)
        layout.addWidget(bar)


class ResultBlock(QFrame):
    """Блок результата со списком пунктов."""

    def __init__(self, title: str, items: list, icon: str = "•"):
        super().__init__()
        self.setObjectName("resultBlock")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        for item in items:
            item_label = QLabel(f"{icon} {item}")
            item_label.setWordWrap(True)
            item_label.setStyleSheet("color: #b0b0b0; margin-left: 8px; line-height: 1.5;")
            layout.addWidget(item_label)


class ParsedContentBlock(QFrame):
    """Блок распарсенного контента сайта."""

    def __init__(self, data: dict):
        super().__init__()
        self.setObjectName("resultBlock")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("🌐 Данные с сайта")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        fields = [
            ("URL", data.get("url")),
            ("Title", data.get("title") or "Не найден"),
            ("H1", data.get("h1") or "Не найден"),
            ("Первый абзац", data.get("first_paragraph") or "Не найден"),
        ]

        page_content = data.get("page_content") or "Не найден"
        if len(page_content) > 1500:
            page_content = page_content[:1500] + "..."
        fields.append(("Контент страницы", page_content))

        for label, value in fields:
            name = QLabel(label)
            name.setStyleSheet("color: #787878; font-size: 12px; font-weight: 600;")
            text = QLabel(str(value))
            text.setWordWrap(True)
            text.setStyleSheet("color: #b0b0b0; margin-bottom: 8px;")
            layout.addWidget(name)
            layout.addWidget(text)


class DropZone(QFrame):
    """Зона drag & drop изображений с превью и удалением."""

    fileSelected = pyqtSignal(str)
    fileCleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("uploadZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel("Перетащите изображение или нажмите для выбора")
        self.text_label.setStyleSheet("color: #b0b0b0; font-size: 14px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hint_label = QLabel("PNG, JPG, GIF, WEBP до 10MB")
        self.hint_label.setStyleSheet("color: #787878; font-size: 12px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_container = QFrame()
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.remove_btn = QPushButton("✕ Удалить")
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setFixedWidth(120)
        self.remove_btn.clicked.connect(self.clear)

        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.remove_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.preview_container.hide()

        self._layout.addWidget(self.icon_label)
        self._layout.addWidget(self.text_label)
        self._layout.addWidget(self.hint_label)
        self._layout.addWidget(self.preview_container)

        self.selected_file = None

    def mousePressEvent(self, event):
        if self.preview_container.isVisible():
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.gif *.webp)",
        )
        if file_path:
            self.set_file(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                "QFrame#uploadZone { border-color: #737373; background-color: rgba(163, 163, 163, 0.1); }"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                self.set_file(file_path)

    def set_file(self, file_path: str):
        self.selected_file = file_path
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                300,
                200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(pixmap)

        self.icon_label.hide()
        self.text_label.hide()
        self.hint_label.hide()
        self.preview_container.show()
        self.fileSelected.emit(file_path)

    def clear(self):
        self.selected_file = None
        self.preview_label.clear()
        self.preview_container.hide()
        self.icon_label.show()
        self.text_label.setText("Перетащите изображение или нажмите для выбора")
        self.text_label.show()
        self.hint_label.setText("PNG, JPG, GIF, WEBP до 10MB")
        self.hint_label.show()
        self.fileCleared.emit()
