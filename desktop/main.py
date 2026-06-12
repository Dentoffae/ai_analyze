"""
Мониторинг конкурентов — Desktop приложение на PyQt6
Полный аналог веб-интерфейса.
"""
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from api_client import api_client
from styles import DARK_THEME
from widgets import DropZone, ParsedContentBlock, ResultBlock, ScoreBar


class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мониторинг конкурентов | AI Ассистент")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet(DARK_THEME)

        self.current_worker = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._setup_sidebar(root)
        self._setup_content(root)
        self.check_server_connection()

    def _setup_sidebar(self, parent: QHBoxLayout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)

        logo = QLabel("⚡ CompetitorAI")
        logo.setObjectName("logo")
        layout.addWidget(logo)

        nav = QWidget()
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)

        self.nav_buttons = []
        for text, index in [
            ("📝 Анализ текста", 0),
            ("🖼️ Анализ изображений", 1),
            ("🌐 Парсинг сайта", 2),
            ("📋 История", 3),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        self.nav_buttons[0].setChecked(True)
        nav_layout.addStretch()

        self.status_label = QLabel("● Проверка подключения...")
        self.status_label.setStyleSheet("color: #b8944f; padding: 16px;")
        nav_layout.addWidget(self.status_label)

        layout.addWidget(nav)
        parent.addWidget(sidebar)

    def _setup_content(self, parent: QHBoxLayout):
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(40, 32, 40, 32)

        header = QVBoxLayout()
        title = QLabel("Мониторинг конкурентов")
        title.setObjectName("title")
        subtitle = QLabel("AI-ассистент для анализа конкурентной среды")
        subtitle.setObjectName("subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.setContentsMargins(0, 0, 0, 24)
        self.content_layout.addLayout(header)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.stacked_widget.addWidget(self._create_text_tab())
        self.stacked_widget.addWidget(self._create_image_tab())
        self.stacked_widget.addWidget(self._create_parse_tab())
        self.stacked_widget.addWidget(self._create_history_tab())
        self.content_layout.addWidget(self.stacked_widget, stretch=1)

        self.results_frame = QFrame()
        self.results_frame.setObjectName("resultsCard")
        self.results_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        results_outer = QVBoxLayout(self.results_frame)
        results_outer.setContentsMargins(20, 20, 20, 20)
        results_outer.setSpacing(12)

        results_header = QHBoxLayout()
        self.results_back_btn = QPushButton("← Назад")
        self.results_back_btn.setObjectName("secondaryButton")
        self.results_back_btn.clicked.connect(self.hide_results)
        results_title = QLabel("📊 Результаты анализа")
        results_title.setObjectName("cardTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("secondaryButton")
        close_btn.setFixedSize(36, 36)
        close_btn.clicked.connect(self.hide_results)
        results_header.addWidget(self.results_back_btn)
        results_header.addWidget(results_title)
        results_header.addStretch()
        results_header.addWidget(close_btn)
        results_outer.addLayout(results_header)

        self.results_scroll = QScrollArea()
        self.results_scroll.setObjectName("resultsScroll")
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.results_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(4, 4, 12, 16)
        self.results_layout.setSpacing(12)
        self.results_scroll.setWidget(self.results_widget)
        results_outer.addWidget(self.results_scroll, stretch=1)

        self.results_frame.hide()
        self.content_layout.addWidget(self.results_frame, stretch=1)

        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(300)
        self.loading_label = QLabel("Анализирую данные...")
        self.loading_label.setStyleSheet("color: #b0b0b0; font-size: 16px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        self.loading_widget.hide()
        self.content_layout.addWidget(self.loading_widget)

        parent.addWidget(content)

    def _create_text_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        card_layout.addWidget(self._card_title("Анализ текста конкурента"))
        card_layout.addWidget(
            self._card_desc("Вставьте текст с сайта конкурента, из рекламы или описания продукта")
        )
        card_layout.addSpacing(16)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Вставьте текст конкурента для анализа...\n\n"
            "Например: описание продукта, текст с лендинга, рекламное объявление..."
        )
        self.text_input.setMinimumHeight(200)
        card_layout.addWidget(self.text_input)
        card_layout.addSpacing(16)

        self.analyze_text_btn = QPushButton("⚡ Проанализировать")
        self.analyze_text_btn.setObjectName("primaryButton")
        self.analyze_text_btn.clicked.connect(self.analyze_text)
        card_layout.addWidget(self.analyze_text_btn)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _create_image_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        card_layout.addWidget(self._card_title("Анализ изображений"))
        card_layout.addWidget(
            self._card_desc("Загрузите скриншот сайта, баннер или фото упаковки конкурента")
        )
        card_layout.addSpacing(16)

        self.drop_zone = DropZone()
        self.drop_zone.fileSelected.connect(lambda _: self.analyze_image_btn.setEnabled(True))
        self.drop_zone.fileCleared.connect(lambda: self.analyze_image_btn.setEnabled(False))
        card_layout.addWidget(self.drop_zone)
        card_layout.addSpacing(16)

        self.analyze_image_btn = QPushButton("⚡ Проанализировать")
        self.analyze_image_btn.setObjectName("primaryButton")
        self.analyze_image_btn.setEnabled(False)
        self.analyze_image_btn.clicked.connect(self.analyze_image)
        card_layout.addWidget(self.analyze_image_btn)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _create_parse_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        card_layout.addWidget(self._card_title("Парсинг сайта конкурента"))
        card_layout.addWidget(
            self._card_desc("Введите URL сайта для автоматического извлечения и анализа контента")
        )
        card_layout.addSpacing(16)

        url_row = QHBoxLayout()
        prefix = QLabel("https://")
        prefix.setStyleSheet(
            "background-color: #333333; padding: 12px 16px; border-radius: 8px 0 0 8px; color: #787878;"
        )
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("example.com")
        self.url_input.setStyleSheet("border-radius: 0 8px 8px 0;")
        self.url_input.returnPressed.connect(self.parse_site)
        url_row.addWidget(prefix)
        url_row.addWidget(self.url_input)
        card_layout.addLayout(url_row)
        card_layout.addSpacing(16)

        self.parse_btn = QPushButton("⚡ Парсить и анализировать")
        self.parse_btn.setObjectName("primaryButton")
        self.parse_btn.clicked.connect(self.parse_site)
        card_layout.addWidget(self.parse_btn)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QHBoxLayout()
        header.addWidget(self._card_title("История запросов"))
        header.addStretch()
        self.clear_history_btn = QPushButton("🗑️ Очистить")
        self.clear_history_btn.setObjectName("secondaryButton")
        self.clear_history_btn.clicked.connect(self.clear_history)
        header.addWidget(self.clear_history_btn)
        layout.addLayout(header)

        desc = QLabel("Последние 10 запросов к системе")
        desc.setObjectName("cardDescription")
        layout.addWidget(desc)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_scroll.setWidget(self.history_widget)
        layout.addWidget(self.history_scroll)
        return widget

    @staticmethod
    def _card_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("cardTitle")
        return label

    @staticmethod
    def _card_desc(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("cardDescription")
        return label

    def switch_tab(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)
        if index == 3:
            self.load_history()

    def check_server_connection(self):
        if api_client.check_health():
            self.status_label.setText("● Система активна")
            self.status_label.setStyleSheet("color: #7a9e8e; padding: 16px;")
        else:
            self.status_label.setText("● Сервер недоступен")
            self.status_label.setStyleSheet("color: #c45c5c; padding: 16px;")

    def show_loading(self, message: str = "Анализирую данные..."):
        self.loading_label.setText(message)
        self.loading_widget.show()
        self.results_frame.hide()
        for btn in (self.analyze_text_btn, self.analyze_image_btn, self.parse_btn):
            btn.setEnabled(False)

    def hide_loading(self):
        self.loading_widget.hide()
        self.analyze_text_btn.setEnabled(True)
        self.analyze_image_btn.setEnabled(bool(self.drop_zone.selected_file))
        self.parse_btn.setEnabled(True)

    def hide_results(self):
        self.results_frame.hide()
        self.stacked_widget.show()

    def _open_results_view(self):
        self.stacked_widget.hide()
        self.results_frame.show()
        self.results_scroll.verticalScrollBar().setValue(0)

    def _clear_results_layout(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_text_analysis(self, analysis: dict):
        self._clear_results_layout()
        self._append_text_analysis_blocks(analysis)
        self.results_layout.addStretch()
        self._open_results_view()

    def show_image_analysis(self, analysis: dict):
        self._clear_results_layout()

        if analysis.get("description"):
            block = QFrame()
            block.setObjectName("resultBlock")
            bl = QVBoxLayout(block)
            bl.addWidget(self._section_title("🖼️ Описание изображения"))
            desc = QLabel(analysis["description"])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #b0b0b0;")
            bl.addWidget(desc)
            self.results_layout.addWidget(block)

        design_score = analysis.get("design_score", analysis.get("visual_style_score"))
        if design_score is not None:
            block = QFrame()
            block.setObjectName("resultBlock")
            bl = QVBoxLayout(block)
            bl.addWidget(self._section_title("⭐ Оценка визуального стиля"))
            bl.addWidget(ScoreBar(design_score))
            if analysis.get("visual_style_analysis"):
                va = QLabel(analysis["visual_style_analysis"])
                va.setWordWrap(True)
                va.setStyleSheet("color: #b0b0b0;")
                bl.addWidget(va)
            self.results_layout.addWidget(block)

        if "animation_potential" in analysis:
            block = QFrame()
            block.setObjectName("resultBlock")
            bl = QVBoxLayout(block)
            bl.addWidget(self._section_title("🎬 Потенциал для анимации"))
            bl.addWidget(ScoreBar(analysis["animation_potential"]))
            if analysis.get("animation_potential_analysis"):
                aa = QLabel(analysis["animation_potential_analysis"])
                aa.setWordWrap(True)
                aa.setStyleSheet("color: #b0b0b0;")
                bl.addWidget(aa)
            self.results_layout.addWidget(block)

        if analysis.get("marketing_insights"):
            self.results_layout.addWidget(
                ResultBlock("💡 Маркетинговые инсайты", analysis["marketing_insights"])
            )
        if analysis.get("recommendations"):
            self.results_layout.addWidget(
                ResultBlock("📋 Рекомендации", analysis["recommendations"])
            )

        self.results_layout.addStretch()
        self._open_results_view()

    def show_parse_results(self, data: dict):
        self._clear_results_layout()
        self.results_layout.addWidget(ParsedContentBlock(data))
        if data.get("analysis"):
            self._append_text_analysis_blocks(data["analysis"])
        self.results_layout.addStretch()
        self._open_results_view()

    def _append_text_analysis_blocks(self, analysis: dict):
        design_score = analysis.get("design_score")
        if design_score is not None:
            block = QFrame()
            block.setObjectName("resultBlock")
            bl = QVBoxLayout(block)
            bl.addWidget(self._section_title("🎨 Оценка дизайна текста"))
            bl.addWidget(ScoreBar(design_score))
            self.results_layout.addWidget(block)

        if "animation_potential" in analysis:
            block = QFrame()
            block.setObjectName("resultBlock")
            bl = QVBoxLayout(block)
            bl.addWidget(self._section_title("🎬 Потенциал для анимации"))
            bl.addWidget(ScoreBar(analysis["animation_potential"]))
            if analysis.get("animation_potential_analysis"):
                aa = QLabel(analysis["animation_potential_analysis"])
                aa.setWordWrap(True)
                aa.setStyleSheet("color: #b0b0b0;")
                bl.addWidget(aa)
            self.results_layout.addWidget(block)

        if analysis.get("strengths"):
            self.results_layout.addWidget(ResultBlock("✅ Сильные стороны", analysis["strengths"]))
        if analysis.get("weaknesses"):
            self.results_layout.addWidget(ResultBlock("⚠️ Слабые стороны", analysis["weaknesses"]))
        if analysis.get("unique_offers"):
            self.results_layout.addWidget(
                ResultBlock("⭐ Уникальные предложения", analysis["unique_offers"])
            )
        if analysis.get("recommendations"):
            self.results_layout.addWidget(ResultBlock("💡 Рекомендации", analysis["recommendations"]))
        if analysis.get("summary"):
            summary = QFrame()
            summary.setObjectName("resultBlock")
            summary.setStyleSheet(
                "QFrame#resultBlock { background: qlineargradient("
                "x1:0, y1:0, x2:1, y2:1, stop:0 rgba(163, 163, 163, 0.12), stop:1 rgba(255, 255, 255, 0.04)); }"
            )
            sl = QVBoxLayout(summary)
            sl.addWidget(self._section_title("📝 Резюме"))
            text = QLabel(analysis["summary"])
            text.setWordWrap(True)
            text.setStyleSheet("color: #f0f0f0; font-size: 15px;")
            sl.addWidget(text)
            self.results_layout.addWidget(summary)

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def show_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)

    def analyze_text(self):
        text = self.text_input.toPlainText().strip()
        if len(text) < 10:
            self.show_error("Введите текст минимум 10 символов для анализа")
            return
        self.show_loading("Анализирую текст...")
        self.current_worker = WorkerThread(api_client.analyze_text, text)
        self.current_worker.finished.connect(self._on_text_done)
        self.current_worker.error.connect(self.on_error)
        self.current_worker.start()

    def _on_text_done(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("analysis"):
            self.show_text_analysis(result["analysis"])
        else:
            self.show_error(result.get("error", "Произошла ошибка при анализе"))

    def analyze_image(self):
        if not self.drop_zone.selected_file:
            self.show_error("Выберите изображение для анализа")
            return
        self.show_loading("Анализирую изображение...")
        self.current_worker = WorkerThread(api_client.analyze_image, self.drop_zone.selected_file)
        self.current_worker.finished.connect(self._on_image_done)
        self.current_worker.error.connect(self.on_error)
        self.current_worker.start()

    def _on_image_done(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("analysis"):
            self.show_image_analysis(result["analysis"])
        else:
            self.show_error(result.get("error", "Произошла ошибка при анализе изображения"))

    def parse_site(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_error("Введите URL сайта для парсинга")
            return
        self.show_loading("Загружаю и анализирую сайт...")
        self.current_worker = WorkerThread(api_client.parse_demo, url)
        self.current_worker.finished.connect(self._on_parse_done)
        self.current_worker.error.connect(self.on_error)
        self.current_worker.start()

    def _on_parse_done(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("data"):
            self.show_parse_results(result["data"])
        else:
            self.show_error(result.get("error", "Не удалось распарсить сайт"))

    def load_history(self):
        result = api_client.get_history()
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = result.get("items") or []
        if not items:
            empty = QLabel("📋 История пуста")
            empty.setStyleSheet("color: #787878; font-size: 16px; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(empty)
            self.history_layout.addStretch()
            return

        icons = {"text": "📝", "image": "🖼️", "parse": "🌐"}
        labels = {
            "text": "Анализ текста",
            "image": "Анализ изображения",
            "parse": "Парсинг сайта",
        }

        for item in items:
            frame = QFrame()
            frame.setObjectName("historyItem")
            row = QHBoxLayout(frame)

            icon = QLabel(icons.get(item.get("request_type", ""), "📄"))
            icon.setStyleSheet("font-size: 24px;")

            content = QVBoxLayout()
            type_label = QLabel(labels.get(item.get("request_type", ""), item.get("request_type", "")))
            type_label.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold;")
            summary = QLabel(item.get("request_summary", ""))
            summary.setWordWrap(True)
            summary.setStyleSheet("color: #b0b0b0;")
            content.addWidget(type_label)
            content.addWidget(summary)

            time_str = ""
            ts = item.get("timestamp", "")
            if ts:
                try:
                    time_str = datetime.fromisoformat(ts).strftime("%d.%m.%Y %H:%M")
                except ValueError:
                    time_str = str(ts)[:16]

            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #787878; font-size: 12px;")

            row.addWidget(icon)
            row.addLayout(content, stretch=1)
            row.addWidget(time_label)
            self.history_layout.addWidget(frame)

        self.history_layout.addStretch()

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите очистить историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            api_client.clear_history()
            self.load_history()

    def on_error(self, error: str):
        self.hide_loading()
        self.show_error(error)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
