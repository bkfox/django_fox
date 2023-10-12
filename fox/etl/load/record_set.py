from inspect import isclass

import pandas as pd

# from rest_framework import serializers


__all__ = ("RecordSet",)


class BaseRecord(type):
    def __new__(mcls, name, bases, attrs):
        attrs["Meta"] = mcls.get_meta_class(name, bases, attrs)
        cls = super(BaseRecord, mcls).__new__(name, bases, attrs)
        return cls

    @classmethod
    def get_meta(mcls, name, bases, attrs):
        meta = attrs.get("Meta")
        bases_meta = tuple(b.Meta for b in bases if isinstance(b, Record))
        if not meta:
            meta = type(name + "Meta", bases_meta, {})
        elif not isclass(meta):
            raise ValueError("Record's `Meta` attribute must be a class")
        else:
            meta.__bases__ = tuple(set(meta.__bases__) | set(bases_meta))

        mapping = {
            "label": name,
            "label_lower": name.lower(),
            "fields": tuple(
                attr for attr, val in attrs.items() if not callable(val)
            ),
        }

        for attr, value in mapping.items():
            if not getattr(meta, attr, None):
                setattr(meta, attr, value)
        return meta


class Record(metaclass=BaseRecord):
    """A Record is a class holding data providing fields attributes."""

    class Meta:
        label = ""
        label_lower = ""
        fields = tuple()


class RecordSet:
    """Dataframe container providing utils in order to add/store data."""

    df_class = pd.DataFrame
    """DataFrame to use as."""
    df = None
    """DataFrame holding data."""
    record_class = None
    """Django model to handle."""

    def __init__(
        self,
        df=None,
        columns=None,
        record_class=None,
        df_class=None,
        **df_kwargs
    ):
        if df is None:
            df_class = df_class or self.df_class
            df = self.df_class(columns=columns, **df_kwargs)
        self.df = df
        self.record_class = record_class

    @classmethod
    def from_serializer(cls, serializer_class, *args, columns=False, **kwargs):
        """Return RecordSet instance creating a dataframe based on the provided
        serializer's fields."""
        if not columns:
            columns = list(serializer_class._declared_fields.keys())
        return cls(*args, **kwargs)

    def reset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset pool items with the provided dataframe. Previous items are
        dropped.

        :param pd.DataFrame df: dataframe to set.
        :return current dataframe held by record set.
        """
        self.df = df
        return df

    def drop(self, *args, inplace=True, **kwargs):
        """Drop items from record set. Arguments are passd down to
        `pd.DataFrame.drop()` (inplace is True by default).

        :param *args: `pd.DataFrame.drop()`'s args.
        :param **kwargs: `pd.DataFrame.drop()`'s kwargs.
        :return current dataframe held by record set.
        """
        return self.df.drop(*args, inplace=inplace, **kwargs)

    def save(self, *args, **kwargs):
        """Save all df records to database."""
        return self.df.django.save(*args, **kwargs)

    def __repr__(self):
        return repr(self.df)
