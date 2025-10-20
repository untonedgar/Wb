import re
import os
import time
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from django.db import transaction
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from abc import ABC, abstractmethod

class IDriverProvider(ABC):
    """Интерфейс для настройки и предоставления WebDriver"""
    @abstractmethod
    def get_driver(self) -> webdriver.Chrome:
        pass


class IProductRepository(ABC):
    """Интерфейс для сохранения данных о товарах"""
    @abstractmethod
    def save(self, product_data: dict):
        pass


class IProductParser(ABC):
    """Интерфейс для парсинга товара"""
    @abstractmethod
    def parse_product(self, item):
        pass


# ===============================
# Реализация компонентов
# ===============================

class ChromeDriverProvider(IDriverProvider):
    """Настройка Chrome WebDriver"""

    def get_driver(self) -> webdriver.Chrome:
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-logging")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
            )

            chrome_driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")

            options.binary_location = chrome_bin
            service = Service(chrome_driver_path)

            driver = webdriver.Chrome(service=service, options=options)
            driver.get("about:blank")
            return driver

        except WebDriverException as e:
            print(f"[Ошибка инициализации драйвера] {str(e)}")
            raise


class DjangoProductRepository(IProductRepository):
    """Репозиторий для сохранения товаров в базу Django"""

    @transaction.atomic
    def save(self, product_data: dict):
        from wb.models import Product

        Product.objects.update_or_create(
            article=product_data['article'],
            defaults={
                'name': product_data['name'],
                'price': product_data['price'],
                'old_price': product_data['old_price'],
                'rating': product_data['rating'],
                'reviews': product_data['reviews_count']
            }
        )
        print(f"[Сохранено] {product_data['name'][:30]}...")


class WildberriesProductParser(IProductParser):
    """Парсер одного товара"""

    @staticmethod
    def _parse_numeric(text):
        if not text:
            return 0
        num_str = re.sub(r'[^\d,]', '', text).replace(',', '.')
        if not num_str:
            return 0
        return round(float(num_str), 2)

    def parse_product(self, item):
        try:
            item_id = item.get_attribute("data-nm-id")
            if not item_id:
                return None

            name = item.find_element(By.CSS_SELECTOR, ".product-card__name").text.strip() \
                if item.find_elements(By.CSS_SELECTOR, ".product-card__name") else "Нет названия"

            price = item.find_element(By.CSS_SELECTOR, ".price__lower-price").text.strip().replace(" ", "") \
                if item.find_elements(By.CSS_SELECTOR, ".price__lower-price") else "0"

            old_price = item.find_element(By.CSS_SELECTOR, "del").text.strip().replace(" ", "") \
                if item.find_elements(By.CSS_SELECTOR, "del") else None

            rating = item.find_element(By.CSS_SELECTOR, ".address-rate-mini").text.strip() \
                if item.find_elements(By.CSS_SELECTOR, ".address-rate-mini") else None

            reviews = item.find_element(By.CSS_SELECTOR, ".product-card__count").text.strip()[1:-1] \
                if item.find_elements(By.CSS_SELECTOR, ".product-card__count") else "0"

            return {
                'article': int(item_id),
                'name': name,
                'price': self._parse_numeric(price),
                'old_price': self._parse_numeric(old_price),
                'rating': self._parse_numeric(rating),
                'reviews_count': self._parse_numeric(reviews)
            }

        except Exception as e:
            print(f"[Ошибка парсинга] {str(e)[:100]}...")
            return None


# ===============================
# Основной парсер
# ===============================

class WildberriesParser:
    """Главный класс — управляет процессом парсинга"""

    def __init__(
        self,
        driver_provider: IDriverProvider = None,
        product_parser: IProductParser = None,
        repository: IProductRepository = None,
        max_products: int = 100
    ):
        self.driver_provider = driver_provider or ChromeDriverProvider()
        self.product_parser = product_parser or WildberriesProductParser()
        self.repository = repository or DjangoProductRepository()
        self.driver = self.driver_provider.get_driver()
        self.max_products = max_products
        self.parsed_ids = set()

    def _validate_driver(self):
        if not isinstance(self.driver, webdriver.Remote):
            print("WARNING: Invalid driver state. Reinitializing...")
            self.driver = self.driver_provider.get_driver()

    def parse(self, url):
        self._validate_driver()
        try:
            self.driver.get(url)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10

            while len(self.parsed_ids) < self.max_products and scroll_attempts < max_scroll_attempts:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card"))
                    )
                except TimeoutException:
                    print("No products found after waiting")
                    scroll_attempts += 1
                    continue

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                try:
                    load_more = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more, .show-more, .btn-more"))
                    )
                    load_more.click()
                    time.sleep(3)
                except:
                    pass

                items = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")
                new_items = [item for item in items if item.get_attribute("data-nm-id") not in self.parsed_ids]

                if new_items:
                    self._process_items(new_items)
                    scroll_attempts = 0
                else:
                    scroll_attempts += 1

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        except Exception as e:
            print(f"[Критическая ошибка] {str(e)}")
        finally:
            self.driver.quit()

    def _process_items(self, items):
        for item in items:
            product_data = self.product_parser.parse_product(item)
            if product_data and product_data['article'] not in self.parsed_ids:
                self.parsed_ids.add(product_data['article'])
                self.repository.save(product_data)



