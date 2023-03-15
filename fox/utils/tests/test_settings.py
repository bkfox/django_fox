from django.db import models

from ..settings import Settings


class SettingsSample(Settings):
    a = 24
    b = "42"
    _private = "yolo"


class SettingsSampleModel(SettingsSample, models.Model):
    a = models.IntegerField(default=24)
    b = models.CharField(max_length=4, default="42")

    class Meta:
        abstract = True


class ConfSample:
    conf = {"a": 12, "b": "24", "c": "none"}


def test_load():
    settings = SettingsSample().load("conf", ConfSample)
    assert isinstance(settings, SettingsSample)
    assert settings.a == ConfSample.conf["a"]


def test_update():
    settings = SettingsSample()
    settings.update(ConfSample.conf)
    assert settings.a == ConfSample.conf["a"]
    assert settings.b == ConfSample.conf["b"]
    assert getattr(settings, "c", None) is None


def test_get():
    settings = SettingsSample()
    assert settings.get("a") == SettingsSample.a
    assert settings.get("c") is None


def test_items():
    settings = SettingsSample()
    expect = {"a": settings.a, "b": settings.b}
    assert dict(settings.items()) == expect


def test_is_config_item():
    settings = SettingsSample()
    assert settings.is_config_item("_private", None) is False
    assert settings.is_config_item("key", ConfSample) is False
    assert settings.is_config_item("key", lambda x: x) is False
    assert settings.is_config_item("key", ConfSample()) is True
    assert settings.is_config_item("objects", None) is True


# def test_is_config_item_model():
#    settings = SettingsSampleModel()
#    assert settings.is_config_item("objects", None) is False
