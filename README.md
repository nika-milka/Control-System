# Система контроля строительных объектов

Веб-приложение для управления дефектами на строительных объектах.

## Функциональность

### Роли пользователей:
- **Инженеры** - регистрация дефектов, обновление информации
- **Менеджеры** - назначение задач, контроль сроков, формирование отчетов  
- **Руководители** - просмотр прогресса и отчетности

### Основные модули:
-  **Users/Auth** - регистрация, аутентификация, роли
-  **Projects** - управление строительными проектами
-  **Defects** - полный CRUD для дефектов
-  **Reports** - аналитика и отчетность
-  **Tasks** - управление задачами

##  Технологии

- **Backend**: Django 5.2, Python 3.12
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **База данных**: SQLite3
- **Безопасность**: CSRF, XSS защита, SQL-инъекции

##  Установка

```bash
# Клонирование репозитория
git clone (https://github.com/nika-milka/Control-System.git)
cd construction_defects

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install django

# Миграции базы данных
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
