"""
Сервис для парсинга веб-страниц через Selenium Chrome
"""
import base64
import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from backend.config import settings

logger = logging.getLogger("competitor_monitor.parser")

MAX_PAGE_CONTENT_LENGTH = 20000


@dataclass
class ParsedPage:
    """Результат парсинга страницы"""
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    page_content: Optional[str] = None
    screenshot_bytes: Optional[bytes] = None
    error: Optional[str] = None


class ParserService:
    """Парсинг веб-страниц через Chrome: скриншот + полный текстовый контент"""

    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация Parser сервиса")
        logger.info(f"  Timeout: {settings.parser_timeout} сек")
        logger.info(f"  User-Agent: {settings.parser_user_agent[:50]}...")

        self.timeout = settings.parser_timeout
        self._executor = ThreadPoolExecutor(max_workers=2)

        logger.info("Parser сервис инициализирован ✓")
        logger.info("=" * 50)

    def _create_driver(self) -> webdriver.Chrome:
        """Создать экземпляр Chrome через Selenium"""
        logger.info("  🌐 Запуск Chrome через Selenium...")
        start_time = time.time()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={settings.parser_user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        elapsed = time.time() - start_time
        logger.info(f"  ✓ Chrome запущен за {elapsed:.2f} сек")
        return driver

    def _wait_for_page(self, driver: webdriver.Chrome) -> None:
        """Дождаться загрузки страницы и динамического контента"""
        WebDriverWait(driver, self.timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        WebDriverWait(driver, self.timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)

    def _extract_page_content(self, driver: webdriver.Chrome) -> dict:
        """Извлечь весь видимый текстовый контент страницы"""
        return driver.execute_script("""
            const removeNodes = (root, selector) => {
                root.querySelectorAll(selector).forEach(node => node.remove());
            };

            const bodyClone = document.body.cloneNode(true);
            removeNodes(bodyClone, 'script, style, noscript, svg, iframe');

            const pageText = (bodyClone.innerText || '')
                .replace(/\\n{3,}/g, '\\n\\n')
                .trim();

            const metaDescription = document.querySelector('meta[name="description"]');
            const metaKeywords = document.querySelector('meta[name="keywords"]');
            const h1 = document.querySelector('h1');
            const firstParagraph = Array.from(document.querySelectorAll('p'))
                .map(p => (p.innerText || '').trim())
                .find(text => text.length > 50) || null;

            const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
                .map(node => (node.innerText || '').trim())
                .filter(Boolean)
                .slice(0, 20);

            const links = Array.from(document.querySelectorAll('a[href]'))
                .map(link => ({
                    text: (link.innerText || '').trim(),
                    href: link.href
                }))
                .filter(item => item.text)
                .slice(0, 30);

            return {
                title: document.title || null,
                metaDescription: metaDescription ? metaDescription.content : null,
                metaKeywords: metaKeywords ? metaKeywords.content : null,
                h1: h1 ? h1.innerText.trim() : null,
                firstParagraph: firstParagraph,
                headings: headings,
                links: links,
                pageText: pageText
            };
        """)

    def _build_page_content(self, extracted: dict) -> str:
        """Собрать полный текст страницы для передачи в ИИ"""
        parts = []

        if extracted.get("title"):
            parts.append(f"Заголовок страницы (title): {extracted['title']}")
        if extracted.get("metaDescription"):
            parts.append(f"Meta description: {extracted['metaDescription']}")
        if extracted.get("metaKeywords"):
            parts.append(f"Meta keywords: {extracted['metaKeywords']}")
        if extracted.get("h1"):
            parts.append(f"Главный заголовок (H1): {extracted['h1']}")

        headings = extracted.get("headings") or []
        if headings:
            parts.append("Заголовки на странице:\n" + "\n".join(f"- {item}" for item in headings))

        links = extracted.get("links") or []
        if links:
            link_lines = [f"- {item['text']} ({item['href']})" for item in links]
            parts.append("Ссылки на странице:\n" + "\n".join(link_lines))

        page_text = extracted.get("pageText") or ""
        if page_text:
            parts.append("Полный текст страницы:\n" + page_text)

        combined = "\n\n".join(parts).strip()
        if len(combined) > MAX_PAGE_CONTENT_LENGTH:
            combined = combined[:MAX_PAGE_CONTENT_LENGTH] + "\n\n[... контент обрезан ...]"
        return combined

    def _take_full_page_screenshot(self, driver: webdriver.Chrome) -> bytes:
        """Сделать скриншот всей страницы"""
        total_width = driver.execute_script(
            "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);"
        )
        total_height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
        )

        width = min(max(int(total_width), 1280), 3840)
        height = min(max(int(total_height), 720), 12000)
        driver.set_window_size(width, height)
        time.sleep(0.5)

        return driver.get_screenshot_as_png()

    def _parse_sync(self, url: str) -> ParsedPage:
        """Синхронный парсинг URL в отдельном потоке"""
        logger.info("=" * 50)
        logger.info(f"🔍 ПАРСИНГ САЙТА: {url}")

        driver = None
        total_start = time.time()

        try:
            driver = self._create_driver()
            driver.set_page_load_timeout(self.timeout)

            logger.info("  📄 Открытие страницы в Chrome...")
            page_start = time.time()
            driver.get(url)
            logger.info(f"  ✓ Страница открыта за {time.time() - page_start:.2f} сек")

            logger.info("  ⏳ Ожидание загрузки контента...")
            self._wait_for_page(driver)

            logger.info("  📝 Извлечение всего контента страницы...")
            extracted = self._extract_page_content(driver)
            page_content = self._build_page_content(extracted)

            title = extracted.get("title")
            h1 = extracted.get("h1")
            first_paragraph = extracted.get("firstParagraph")

            logger.info(f"  📌 Title: {title[:60] if title else 'N/A'}...")
            logger.info(f"  📌 H1: {h1[:60] if h1 else 'N/A'}...")
            logger.info(f"  📌 Контент: {len(page_content)} символов")

            logger.info("  📸 Создание скриншота страницы...")
            screenshot_start = time.time()
            screenshot_bytes = self._take_full_page_screenshot(driver)
            screenshot_size_kb = len(screenshot_bytes) / 1024
            logger.info(
                f"  ✓ Скриншот создан за {time.time() - screenshot_start:.2f} сек "
                f"({screenshot_size_kb:.1f} KB)"
            )

            total_elapsed = time.time() - total_start
            logger.info(f"  ✅ ПАРСИНГ ЗАВЕРШЁН за {total_elapsed:.2f} сек")
            logger.info("=" * 50)

            return ParsedPage(
                title=title,
                h1=h1,
                first_paragraph=first_paragraph,
                page_content=page_content,
                screenshot_bytes=screenshot_bytes,
            )

        except TimeoutException:
            logger.error(f"  ✗ TIMEOUT за {time.time() - total_start:.2f} сек")
            logger.error("=" * 50)
            return ParsedPage(error="Превышено время ожидания загрузки страницы")

        except WebDriverException as e:
            error_msg = str(e)
            logger.error(f"  ✗ WebDriver ошибка: {error_msg[:200]}")
            logger.error("=" * 50)

            if "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                return ParsedPage(error="Не удалось найти сайт по указанному адресу")
            if "net::ERR_CONNECTION_REFUSED" in error_msg:
                return ParsedPage(error="Соединение отклонено сервером")
            if "net::ERR_CONNECTION_TIMED_OUT" in error_msg:
                return ParsedPage(error="Превышено время ожидания соединения")
            return ParsedPage(error=f"Ошибка браузера: {error_msg[:200]}")

        except Exception as e:
            logger.error(f"  ✗ Ошибка парсинга: {e}")
            logger.error("=" * 50)
            return ParsedPage(error=f"Ошибка при загрузке страницы: {str(e)[:200]}")

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"  Ошибка при закрытии браузера: {e}")

    async def parse_url(self, url: str) -> ParsedPage:
        """Асинхронный парсинг URL через Chrome"""
        original_url = url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            logger.info(f"  URL дополнен протоколом: {original_url} -> {url}")

        logger.info(f"🚀 Запуск парсинга через Selenium: {url}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._parse_sync, url)

    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Конвертировать скриншот в base64"""
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def close(self):
        """Закрыть executor"""
        logger.info("Закрытие Parser сервиса...")
        self._executor.shutdown(wait=False)
        logger.info("Parser сервис закрыт ✓")


logger.info("Создание глобального экземпляра Parser сервиса...")
parser_service = ParserService()
