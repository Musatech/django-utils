from django.db.models import Manager, Model, QuerySet
from django.db.models.fields import DateTimeField
from django.utils import timezone


class SoftDeleteAtManager(Manager):

    def all(self, deleted=False):
        return self.get_queryset().all(deleted)


class SoftDeleteAtQueryset(QuerySet):
    manager = SoftDeleteAtManager

    def all(self, deleted=False):
        if deleted is not None:
            return self.filter(deleted_at__isnull=not deleted)
        return super().all()

    def delete(self, hard_delete=False):
        if hard_delete:
            return super().delete()
        self.update(deleted_at=timezone.now(), updated_at=timezone.now())

    def as_manager(self):
        manager = self.manager.from_queryset(self)()
        manager._built_with_as_manager = True
        return manager

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)


class SoftDeleteAtModel(Model):
    deleted_at = DateTimeField(null=True, db_index=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    objects = SoftDeleteAtQueryset.as_manager()

    @property
    def deleted(self):
        return self.deleted_at is not None

    def delete(self, hard_delete=False, *args, **kwargs):
        if hard_delete:
            return super().delete(*args, **kwargs)

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    class Meta:
        abstract = True
