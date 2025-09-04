from django.db.models import Manager, Model, QuerySet
from django.db.models.fields import BooleanField, DateTimeField
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.db import connection
from django.core.exceptions import ValidationError


class BaseDeletedManager(Manager):

    def all(self, deleted=False):
        return self.get_queryset().all(deleted)


class BaseDeletedQueryset(QuerySet):
    manager = BaseDeletedManager

    def all(self, deleted=False):
        if deleted is not None:
            return self.filter(deleted=deleted)
        return super().all()

    def delete(self, hard_delete=False):
        if hard_delete:
            return super().delete()
        self.update(deleted=True, updated_at=timezone.now())

    def as_manager(self):
        manager = self.manager.from_queryset(self)()
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


class TreeModelManager(models.Manager):
    """
    Custom manager for TreeModel that provides methods for traversing the tree structure.
    """
    def get_children(self, instance=None):
        """
        Returns all direct children of the instance.
        If instance is None, returns all root nodes (nodes without a parent).
        """
        if instance is None:
            return self.filter(parent__isnull=True)
        return self.filter(parent=instance)

    def get_descendants(self, instance):
        """
        Returns all descendants (children, grandchildren, etc.) of the instance.
        """
        if not instance.tree_id:
            return self.none()

        return self.filter(tree_id__startswith=f"{instance.tree_id}.").exclude(id=instance.id)

    def get_parent(self, instance, level=1):
        """
        Returns the parent of the instance at the specified level.
        level=1 returns the direct parent, level=2 returns the grandparent, etc.
        """
        if not instance.parent or level < 1:
            return None

        if level == 1:
            return instance.parent

        return self.get_parent(instance.parent, level-1)

    def get_ancestors(self, instance):
        """
        Returns all ancestors (parent, grandparent, etc.) of the instance.
        """
        if not instance.parent or not instance.tree_id:
            return self.none()

        # Extract all ancestor IDs from the tree_id
        ancestor_ids = instance.tree_id.split('.')
        # Remove the last ID (which is the instance's ID)
        ancestor_ids = ancestor_ids[:-1]

        if not ancestor_ids:
            return self.none()

        return self.filter(id__in=ancestor_ids)


class TreeModel(SoftDeleteModel):
    """
    Abstract model that implements a tree structure.
    Provides parent-child relationships and tree_id for efficient tree traversal.
    """
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children')
    tree_id = models.CharField(max_length=50, null=True, blank=False, db_index=True,
                               help_text="Hierarchical ID representing the tree structure")

    objects = TreeModelManager()

    def save(self, *args, **kwargs):
        # Get current value from DB if this is an existing instance
        old_values = None
        old_tree_id = None
        old_parent_id = None
        if self.pk:
            old_values = type(self).objects.filter(pk=self.pk).values("parent_id", "tree_id").first()
            old_tree_id = old_values.get("tree_id") if old_values else None
            old_parent_id = old_values.get("parent_id") if old_values else None

        # Prevent circular references: check if parent is one of the descendants
        if self.parent and self.pk:
            # If trying to set a descendant as parent
            if self.parent.tree_id and self.parent.tree_id.startswith(f"{self.tree_id}."):
                raise ValidationError("Cannot set a descendant as parent. This would create a circular reference.")

            # If trying to set self as parent
            if self.parent.pk == self.pk:
                raise ValidationError("Cannot set self as parent. This would create a circular reference.")

        # Always generate tree_id based on parent, regardless of whether it was set externally
        # For new instances, we need to save first to get the ID, then update tree_id
        is_new_instance = not self.pk

        # Save the instance first
        super().save(*args, **kwargs)

        # Generate tree_id based on parent
        if self.parent:
            # If parent.tree_id is None, use parent.id instead
            parent_id = self.parent.tree_id if self.parent.tree_id is not None else str(self.parent.id)
            new_tree_id = f"{parent_id}.{self.id}"
        else:
            new_tree_id = str(self.id)

        # If tree_id changed or it's a new instance, update it
        if new_tree_id != self.tree_id:
            # Update tree_id directly in the database to avoid recursive save
            type(self).objects.filter(pk=self.pk).update(tree_id=new_tree_id)
            # Update the instance's tree_id
            self.tree_id = new_tree_id

            # Update all descendants' tree_ids in a single operation if tree_id changed
            # Check if this is an existing instance and if the tree_id has changed
            if not is_new_instance and old_tree_id != self.tree_id:
                # If parent was added to a node that previously didn't have one
                # or if parent was changed, update descendants
                self.update_descendants_tree_ids(old_tree_id or str(self.id))

    def update_descendants_tree_ids(self, old_tree_id):
        """
        Updates all descendants' tree_ids in a single database operation.
        This is more efficient than updating each descendant individually.
        """
        model = type(self)

        # Find all descendants with the old tree_id prefix
        descendants = model.objects.filter(tree_id__startswith=f"{old_tree_id}.")

        # No descendants to update
        if not descendants.exists():
            return

        # Prepare the SQL query to update all descendants at once
        # This replaces the old tree_id prefix with the new one
        query = f"""
            UPDATE {model._meta.db_table}
            SET tree_id = CONCAT(%s, SUBSTRING(tree_id, %s))
            WHERE tree_id LIKE %s
        """

        # Execute the query with parameters:
        # 1. New prefix (self.tree_id)
        # 2. Length of old prefix + 1 (to include the dot)
        # 3. Pattern to match (old_tree_id.%)
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    self.tree_id,
                    len(old_tree_id) + 1,
                    f"{old_tree_id}.%"
                ]
            )

    class Meta:
        abstract = True