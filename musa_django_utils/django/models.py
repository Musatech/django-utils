from django.db.models import Manager, Model, QuerySet
from django.db.models.fields import BooleanField, DateTimeField
from django.utils import timezone


class BaseDeletedManager(Manager):

    def all(self, deleted=False):
        return self.get_queryset().all(deleted)


class BaseDeletedQueryset(QuerySet):

    def all(self, deleted=False):
        if deleted is not None:
            self._filter_deleted = deleted
            return self.filter(deleted=deleted)
        return super().all()

    def delete(self):
        self.update(deleted=True, updated_at=timezone.now())

    def as_manager(cls):
        manager = BaseDeletedManager.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)


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
