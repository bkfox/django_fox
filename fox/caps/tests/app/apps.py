from django.apps import AppConfig


class CapsTestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fox.caps.tests.app"
    label = "caps_test"
    url_prefix = "/caps/tests"
