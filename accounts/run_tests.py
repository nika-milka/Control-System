#!/usr/bin/env python
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'construction_defects.settings'
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, failfast=False)
    
    # Запуск всех тестов
    failures = test_runner.run_tests([
        'accounts.tests',
        'accounts.integration_tests', 
        'accounts.user_stories_tests'
    ])
    
    sys.exit(bool(failures))