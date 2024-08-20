from hashlib import md5
from json import dumps

from django.core.serializers.json import DjangoJSONEncoder

from rest_framework.fields import CharField
from rest_framework.serializers import Serializer


class Md5VersionSerializer(Serializer):
    hash_id = CharField(required=False, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['hash_id'] = md5(dumps(data, cls=DjangoJSONEncoder).encode()).hexdigest()
        return data

    class Meta:
        abstract = True
