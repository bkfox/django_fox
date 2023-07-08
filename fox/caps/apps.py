from django.apps import AppConfig

__all__ = ("FoxCapsConfig",)


class FoxCapsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fox.caps"
    label = "fox_caps"
    # url_prefix = 'fox/caps'
