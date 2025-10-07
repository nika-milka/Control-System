import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('accounts')

class SecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Логирование подозрительных запросов
        suspicious_headers = [
            'HTTP_USER_AGENT',
            'HTTP_REFERER', 
            'REMOTE_ADDR'
        ]
        
        log_data = {
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'path': request.path,
            'method': request.method,
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }
        
        # Проверка на SQL-инъекции в GET параметрах
        sql_keywords = ['union', 'select', 'insert', 'update', 'delete', 'drop', '--']
        for key, value in request.GET.items():
            if any(sql_keyword in str(value).lower() for sql_keyword in sql_keywords):
                logger.warning(f'Возможная SQL-инъекция от {log_data["ip"]}: {key}={value}')
        
        # Проверка на XSS в GET параметрах
        xss_patterns = ['<script>', 'javascript:', 'onload=', 'onerror=']
        for key, value in request.GET.items():
            if any(pattern in str(value).lower() for pattern in xss_patterns):
                logger.warning(f'Возможная XSS атака от {log_data["ip"]}: {key}={value}')
        
        logger.info(f'Запрос: {log_data}')

    def process_exception(self, request, exception):
        logger.error(f'Ошибка в запросе {request.path}: {exception}')