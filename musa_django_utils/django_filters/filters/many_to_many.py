import re

from django import forms
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from django_filters.filters import Filter


class M2MCountFilter(Filter):
    """
    Accepts values like "2", "3+", "4-" and filters either a model field or an annotation.
    - If `annotation` is provided, it will annotate `annotated_field` before filtering.
    - Otherwise, it will filter directly on `field_name`.
    - `coerce` controls numeric type (int, Decimal, etc.).
    """
    _pattern = re.compile(r"^\s*(?P<num>\d+)\s*(?P<op>[+-])?\s*$")
    field_class = forms.RegexField

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", _("Accepts values like '2' for exact value, '3+' for 3 or more or '4-' "
                                         "for 4 or less."))
        kwargs.setdefault("regex", self._pattern)
        super().__init__(*args, **kwargs)

    def _parse(self, raw):
        """
        Returns (lookup, value) where lookup in {"exact","gte","lte"}.
        """
        if raw in (None, ""):
            return None, None

        # raw will be a string that matched the regex; extract groups again
        # (RegexField only guarantees it's valid; we still need the groups)
        m = self._pattern.match(str(raw))
        if not m:
            return None, None  # should not happen due to RegexField

        num = int(m.group("num"))  # e.g., int("3") or Decimal("3.5")
        op = m.group("op")
        if op == "+":
            return "gte", num
        if op == "-":
            return "lte", num
        return "exact", num  # no suffix → exact

    def filter(self, qs, value):
        lookup, num = self._parse(value)
        if lookup is None:
            return qs

        qs = qs.annotate(**{f'{self.field_name}_count': Count(f"{self.field_name}", distinct=True)})
        return qs.filter(**{f"{self.field_name}_count__{lookup}": num})
