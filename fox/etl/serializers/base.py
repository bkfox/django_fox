from rest_framework import serializers


class Schema(serializers.Serializer):
    def __init__(self, *args, pool=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pool is not None:
            self.context["pool"] = pool
