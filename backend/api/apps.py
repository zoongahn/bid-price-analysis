import atexit
from django.apps import AppConfig

from db_config.local import close_ssh_tunnel


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """ Django가 시작될 때 실행되는 코드 """
        # Django 종료 시 SSH 터널을 자동으로 닫음
        atexit.register(close_ssh_tunnel)