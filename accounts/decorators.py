from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
import logging

logger = logging.getLogger('accounts')

def engineer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f'Неавторизованный доступ к {view_func.__name__} с IP: {request.META.get("REMOTE_ADDR")}')
            return redirect('accounts:login')
        
        if not request.user.is_engineer():
            logger.warning(f'Попытка доступа не-инженера {request.user.username} к {view_func.__name__}')
            raise PermissionDenied("Доступ разрешен только инженерам")
        
        logger.info(f'Инженер {request.user.username} получил доступ к {view_func.__name__}')
        return view_func(request, *args, **kwargs)
    return wrapper

def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f'Неавторизованный доступ к {view_func.__name__} с IP: {request.META.get("REMOTE_ADDR")}')
            return redirect('accounts:login')
        
        if not request.user.is_manager():
            logger.warning(f'Попытка доступа не-менеджера {request.user.username} к {view_func.__name__}')
            raise PermissionDenied("Доступ разрешен только менеджерам")
        
        logger.info(f'Менеджер {request.user.username} получил доступ к {view_func.__name__}')
        return view_func(request, *args, **kwargs)
    return wrapper

def viewer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f'Неавторизованный доступ к {view_func.__name__} с IP: {request.META.get("REMOTE_ADDR")}')
            return redirect('accounts:login')
        
        if not request.user.is_viewer():
            logger.warning(f'Попытка доступа не-руководителя {request.user.username} к {view_func.__name__}')
            raise PermissionDenied("Доступ разрешен только руководителям и заказчикам")
        
        logger.info(f'Руководитель {request.user.username} получил доступ к {view_func.__name__}')
        return view_func(request, *args, **kwargs)
    return wrapper

# Декоратор для логирования действий
def log_user_action(action_description):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            result = view_func(request, *args, **kwargs)
            if request.user.is_authenticated:
                logger.info(f'Пользователь {request.user.username} ({request.user.role}): {action_description}')
            return result
        return wrapper
    return decorator