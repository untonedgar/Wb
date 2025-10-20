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

class WildberriesParser:

    def __init__(self):
        self.driver = None  # ✅ обязательно инициализируем
        self.parsed_ids = set()
        self.max_products = 100
        self._setup_driver()

    def _setup_driver(self):
        """Настройка Chrome WebDriver"""
        try:
            if self.driver is not None:
                self.driver.quit()

            options = Options()
            options.add_argument("--headless=new")  # ✅ исправлено (одно =)
            options.add_argument("--no-sandbox")  # обязательно в Docker
            options.add_argument("--disable-dev-shm-usage")  # важно для docker
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-logging")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36")

            chrome_driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")

            options.binary_location = chrome_bin  # <-- Важно!

            service = Service(chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get("about:blank")
            return True
        except WebDriverException as e:
            print(f"[Ошибка инициализации драйвера] {str(e)}")
            raise

    def _validate_driver(self):
        """Проверка состояния драйвера перед использованием"""
        if not isinstance(self.driver, webdriver.Remote):
            print("WARNING: Invalid driver state. Reinitializing...")
            if not self._setup_driver():
                raise RuntimeError("Failed to initialize WebDriver")

    @staticmethod
    def _parse_numeric(text):
        """Извлекает число из строки, убирая все нечисловые символы"""
        if not text:
            return 0

        num_str = re.sub(r'[^\d,]', '', text).replace(',', '.')

        if not num_str:
            return 0
        result = round(float(num_str), 2)
        return result

    def _parse_product(self, item):
        """Парсинг данных одного товара"""
        try:
            item_id = item.get_attribute("data-nm-id")
            if not item_id or item_id in self.parsed_ids:
                return None

            self.parsed_ids.add(item_id)

            # Основные данные
            name = item.find_element(By.CSS_SELECTOR, ".product-card__name").text.strip() if item.find_elements(
                        By.CSS_SELECTOR, ".product-card__name") else "Нет названия"

            price = item.find_element(By.CSS_SELECTOR, ".price__lower-price").text.strip().replace(" ",
                                                                                                   "") if item.find_elements(
                By.CSS_SELECTOR, ".price__lower-price") else "0"

            old_price = item.find_element(By.CSS_SELECTOR, "del").text.strip().replace(" ",
                                                                                       "") if item.find_elements(
                By.CSS_SELECTOR, "del") else None


            rating = item.find_element(By.CSS_SELECTOR, ".address-rate-mini").text.strip() if item.find_elements(
                By.CSS_SELECTOR, ".address-rate-mini") else None

            reviews = item.find_element(By.CSS_SELECTOR, ".product-card__count").text.strip()[1:-1]

            price = self._parse_numeric(price)
            old_price = self._parse_numeric(old_price)
            reviews = self._parse_numeric(reviews)
            rating = self._parse_numeric(rating)

            return {
                    'article': int(item_id),
                    'name': name,
                    'price': price,
                    'old_price': old_price,
                    'rating': rating,
                    'reviews_count': reviews or 0
                }

        except Exception as e:
            print(f"[Ошибка парсинга] {str(e)[:100]}...")
            return None

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
                # Прокрутка страницы
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )  # Ожидание подгрузки

                try:
                    load_more = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more, .show-more, .btn-more"))
                    )
                    load_more.click()
                    time.sleep(3)
                except:
                    pass

                # Парсинг товаров
                items = self.driver.find_elements(By.CSS_SELECTOR, ".product-card")

                new_items = [item for item in items if item.get_attribute("data-nm-id") not in self.parsed_ids]

                if new_items:
                    self._process_items(new_items)
                    scroll_attempts = 0
                else:
                    scroll_attempts += 1
                # Проверка окончания загрузки
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        except Exception as e:
            print(f"[Критическая ошибка] {str(e)}")
            if hasattr(e, 'screen'):
                with open('error.png', 'wb') as f:
                    f.write(e.screen)  # Вот здесь может быть проблема с байтами!
        finally:
            self.driver.quit()

    @transaction.atomic
    def _process_items(self, items):
        """Обработка и сохранение товаров"""
        for item in items:
            product_data = self._parse_product(item)
            if product_data:
                self._save_product(product_data)

    def _save_product(self, data):
        """Сохранение товара в базу"""
        from wb.models import Product  # Ленивый импорт

        Product.objects.update_or_create(
            article=data['article'],
            defaults={
                'name': data['name'],
                'price': data['price'],
                'old_price': data['old_price'],
                'rating': data['rating'],
                'reviews': data['reviews_count']
            }
        )
        print(f"[Сохранено] {data['name'][:30]}...")





