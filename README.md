- Приложения на Django, которое парсит товары из Wb.
- Поиск товаров из базы данных осуществляется через
ElasticSearch   
    
- Присутствует чат-поддержка, реализованная через  
Websocket:
   - пользователь может зайти в поддержку и написать менеджеру.
   - менеджер может открыть список чатов, открыть чат, закрыть чат
   - в настоящее время менеджер это суперюзер
   - реализовано уведомление на почту менеджера об обращении в поддержку
    
    
**Инструкция по запуску приложения:** 
    
1.git clone https://github.com/virus37161/Wb.git

2.создайте файл .env.dev в директории app
SECRET_KEY='секретный ключ Django'
ALLOWED_HOSTS=localhost 127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8001

POSTGRES_USER=django
POSTGRES_PASSWORD=password
POSTGRES_DB=wb
POSTGRES_PORT=5432

ES_HOST=http://elasticsearch:9200

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

EMAIL_HOST_USER = email, откуда будут приходить уведомления менеджеру (email.test)
EMAIL_HOST_PASSWORD = пароль для данного email  
DEFAULT_FROM_EMAIL = полностью email (email.test@yandex.ru)  
Вышеуказанный email вы можете создать через яндекс, иструкция ниже
https://yandex.ru/support/yandex-360/customers/mail/ru/mail-clients/others.html

3.Запускаем приложение docker compose up
Переходим по адресу http://localhost:8001/wb

- Чтобы создать админа, необходимо в контейнере app-1 создать   
пользователя admin (python manage.py createsuperuser)