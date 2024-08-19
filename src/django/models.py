from django.db.models import Model, QuerySet
from django.db.models.fields import BooleanField, DateTimeField
from django.utils import timezone


class BaseDeletedQueryset(QuerySet):

    def all(self):
        return self.filter(deleted=False)

    def delete(self):
        self.update(deleted=True, updated_at=timezone.now())

    def filter(self, *args, **kwargs):
        kwargs['deleted'] = False
        return super().filter(*args, **kwargs)


class BaseEnabledQueryset(QuerySet):

    def enabled(self):
        return self.all().filter(enabled=True)


class BaseEnabledDeletedQueryset(BaseDeletedQueryset, BaseEnabledQueryset):
    pass


class SoftDeleteModel(Model):
    deleted = BooleanField(default=False, db_index=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    objects = BaseDeletedQueryset.as_manager()

    def delete(self, *args, **kwargs):
        if 'hard_delete' in kwargs:
            super().delete(*args, **kwargs)

        self.deleted = True
        self.updated_at = timezone.now()
        self.save()

    class Meta:
        abstract = True
