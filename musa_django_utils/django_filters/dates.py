from calendar import monthrange
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django_filters import Filter


class MonthYearFilter(Filter):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", _("Accepts mm-yyyy, multiple values may be separated by commas."))
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs

        try:
            filters = Q()
            parts = [v.strip() for v in value.split(",") if v.strip()]

            for part in parts:
                date_obj = datetime.strptime(part, "%m-%Y")
                start_date = datetime(date_obj.year, date_obj.month, 1)
                end_day = monthrange(date_obj.year, date_obj.month)[1]
                end_date = datetime(date_obj.year, date_obj.month, end_day, 23, 59, 59)

                filters |= Q(**{f'{self.field_name}__range': [start_date, end_date]})

            return qs.filter(filters)

        except ValueError:
            raise ValidationError(_("Invalid format. expected mm-yyyy (ex: 04-2025). or mm-yyyy,mm-yyyy (ex: 04-2025,05-2025)."))  # noqa
