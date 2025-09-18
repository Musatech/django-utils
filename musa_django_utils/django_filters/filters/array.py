from django_filters.filters import ChoiceFilter, MultipleChoiceFilter


class ArrayMixin:

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'contains')
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:  # Even though not a noop, no point filtering if empty.
            return qs

        if self.is_noop(qs, value):
            return qs

        value = value if isinstance(value, list) else [value]
        qs = self.get_method(qs)(**self.get_filter_predicate(value))
        return qs.distinct() if self.distinct else qs


class ArrayChoiceFilter(ArrayMixin, ChoiceFilter):
    pass


class ArrayMultipleChoiceFilter(ArrayMixin, MultipleChoiceFilter):
    pass
