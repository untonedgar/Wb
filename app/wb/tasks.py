from celery import shared_task
from wb.utils.parser import ChromeDriverProvider, WildberriesParser, WildberriesProductParser, DjangoProductRepository
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),       # ловим любые ошибки
    retry_backoff=True,               # экспоненциальная задержка
    retry_kwargs={'max_retries': 3},  # максимум 3 попытки
)
def parse_wildberries_task(self, url):
    parser = None
    try:
        driver_provider = ChromeDriverProvider()
        product_parser = WildberriesProductParser()
        repository = DjangoProductRepository()
        WbParser = WildberriesParser(driver_provider, product_parser, repository)
        result = WbParser.parse(url)
        return result
    except Exception as e:
        logger.exception(f"Ошибка при парсинге WB: {e}")
        raise e  # Celery сам перезапустит задачу
    finally:
        if parser and hasattr(parser, 'driver'):
            parser.driver.quit()



