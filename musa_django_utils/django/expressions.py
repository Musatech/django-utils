from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Count, Subquery
from django.db.models.expressions import Func
from django.db.models.fields import IntegerField


class NoGroupMixin:
    """
        mixin used to prevent group by on sql output by django orm
    """

    def get_group_by_cols(self):
        return []


class SubqueryLazy(NoGroupMixin, Subquery):
    pass


class SubqueryMinMaxMixin:

    def as_sql(self, compiler, connection, template=None, **extra_context):
        if 'field' not in extra_context and 'field' not in self.extra:
            if hasattr(self, 'queryset') and len(self.queryset._fields) > 1:
                extra_context['field'] = self.queryset._fields[0]

            elif hasattr(self, 'field'):
                extra_context['field'] = self.field.name

            else:
                raise Exception('You must provide the field name, or have a single column')

        extra_context['min'] = extra_context.get('min') or self.extra.get('min')
        if extra_context.get('min'):
            template = 'GREATEST(' + self.template + ', %(min)s)'

        extra_context['max'] = extra_context.get('max') or self.extra.get('max')
        if extra_context.get('max'):
            template = 'LEAST(' + self.template + ', %(max)s)'

        extra_context['default'] = extra_context.get('default') or self.extra.get('default') or 0
        return super().as_sql(compiler, connection, template=template, **extra_context)


class SubquerySum(SubqueryMinMaxMixin, SubqueryLazy):
    template = '(SELECT COALESCE(SUM(%(field)s), %(default)s) FROM (%(subquery)s) _sum)'


class SubqueryCount(SubqueryMinMaxMixin, SubqueryLazy):
    template = '(SELECT COUNT(DISTINCT %(field)s) FROM (%(subquery)s) _count)'

    def __init__(self, *args, **kwargs) -> None:
        kwargs['output_field'] = kwargs.get('output_field', IntegerField())
        super().__init__(*args, **kwargs)


class SubqueryAvg(SubqueryMinMaxMixin, SubqueryLazy):
    template = '(SELECT COALESCE(AVG(%(field)s), %(default)s) FROM (%(subquery)s) _sum)'


class SubqueryArray(SubqueryLazy):
    template = 'ARRAY(%(subquery)s)'

    def __init__(self, *args, **kwargs) -> None:
        self.output_field = ArrayField(kwargs.get('output_field', JSONField()))
        super().__init__(*args, **kwargs)


class ExistsMoreThan(SubqueryLazy):
    template = '(SELECT COUNT(DISTINCT %(field)s) FROM (%(subquery)s) _count) %(operator)s %(value)s'

    def as_sql(self, compiler, connection, template=None, **extra_context):
        if 'field' not in extra_context and 'field' not in self.extra:
            if len(self.queryset._fields) > 1:
                raise Exception('You must provide the field name, or have a single column')
            extra_context['field'] = self.queryset._fields[0]

        if 'operator' not in extra_context and 'operator' not in self.extra:
            extra_context['operator'] = '>'

        if 'value' not in extra_context and 'value' not in self.extra:
            raise Exception('You must provide the value for comparison')

        return super().as_sql(compiler, connection, template=template, **extra_context)


class Array(Func):
    template = '%(function)s[%(expressions)s]'
    function = 'ARRAY'


class ArrayCat(Func):
    template = '%(function)s(%(expressions)s)'
    function = 'ARRAY_CAT'
    lookup_name = 'array_cat'


class FuncLazy(NoGroupMixin, Func):
    template = '%(expressions)s'


class CountLazy(NoGroupMixin, Count):
    pass
