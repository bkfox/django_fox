from django.apps import AppConfig


class EtlTestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fox.etl.tests.app"
    label = "etl_tests"
    url_prefix = "/etl/tests"
