from django_filters.filters import BaseInFilter, CharFilter, DateFilter, NumberFilter, UUIDFilter


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CharInFilter(BaseInFilter, CharFilter):
    pass


class UUIDInFilter(BaseInFilter, UUIDFilter):
    pass


class DateInFilter(BaseInFilter, DateFilter):
    pass
