from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Manager, Model, QuerySet, Value
from django.db.models.functions import Replace
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _


class TreeModelManager(Manager):
    """
    Custom manager for TreeModel that provides methods for traversing the tree structure.
    """
    def get_ancestors(self, instance):
        """
        Returns all ancestors (parent, grandparent, etc.) of the instance.
        """
        if not instance.parent or not instance.tree_id:
            return self.none()

        # Extract all ancestor IDs from the tree_id without the instance's own ID
        return self.filter(id__in=instance.tree_id.split('.')[:-1])

    def get_descendants(self, instance):
        """
        Returns all descendants (children, grandchildren, etc.) of the instance.
        """
        if not instance.tree_id:
            return self.none()

        return self.filter(tree_id__startswith=f"{instance.tree_id}.").exclude(id=instance.id)

    def get_children(self, instance=None):
        """
        Returns all direct children of the instance.
        If instance is None, returns all root nodes (nodes without a parent).
        """
        if instance is None:
            return self.filter(parent__isnull=True)
        return self.filter(parent=instance)

    def get_parent(self, instance, level=1):
        """
        Returns the parent of the instance at the specified level.
        level=1 returns the direct parent, level=2 returns the grandparent, etc.
        """
        if not instance.parent or level < 1:
            return None

        id = instance.three_id.split('.')[-(level + 1)]
        return self.get(id=id)


class TreeModelQueryset(QuerySet):
    manager = TreeModelManager


class TreeModel(Model):
    """
    Abstract model that implements a tree structure.
    Provides parent-child relationships and tree_id for efficient tree traversal.
    """
    parent = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='children')
    tree_id = models.CharField(max_length=50, null=True, db_index=True,
                               help_text="Hierarchical ID representing the tree structure")

    objects = TreeModelQueryset.as_manager()

    TREE_SEP = '.'
    MAX_TREE_LEVEL = 99

    @property
    def tree_level(self):
        if self.tree_id is None:
            return 0
        return self.tree_id.count(self.TREE_SEP) - 1

    @property
    def ancestors_ids(self):
        if self.tree_id is None:
            return []
        return self.tree_id.strip(self.TREE_SEP).split(self.TREE_SEP)[:-1]

    def _generate_tree_id(self):
        """
        Generates the tree_id based on the parent's tree_id and the instance's ID.
        """
        aux = f"{self.pk}{self.TREE_SEP}"
        aux = f"{self.parent.tree_id}{aux}" if self.parent else f"{self.TREE_SEP}{aux}"
        if self.tree_level > self.MAX_TREE_LEVEL:
            raise ValidationError(_("Maximum tree level of {self.MAX_TREE_LEVEL} exceeded."))
        return aux

    @atomic
    def save(self, *args, **kwargs):
        if self.pk:
            # Update tree_id if parent changed
            old_values = type(self).objects.filter(pk=self.pk).values("parent_id", "tree_id").first()
            if self.parent_id != old_values.get("parent_id"):
                # Prevent circular references: check if parent is one of the descendants
                if f"{self.TREE_SEP}{self.pk}{self.TREE_SEP}" in self.parent.tree_id:
                    raise ValidationError(_("Cannot set a descendant as parent. This would create a circular reference."))

                # If trying to set self as parent
                if self.parent.pk == self.pk:
                    raise ValidationError(_("Cannot set self as parent. This would create a circular reference."))

                self.tree_id = self._generate_tree_id()
                type(self).objects\
                          .filter(tree_id__startswith=old_values['tree_id'])\
                          .update(tree_id=Replace(F('tree_id'), Value(old_values['tree_id']), Value(self.tree_id)))

        super().save(*args, **kwargs)
        if not self.tree_id:  # When creating, set tree_id after pk is available
            self.tree_id = self._generate_tree_id()
            self.save(update_fields=['tree_id'])

    class Meta:
        abstract = True
