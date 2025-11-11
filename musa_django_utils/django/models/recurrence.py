from datetime import date, timedelta

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator
from django.db import connection
from django.db.models import CheckConstraint, F, Model, Q, QuerySet, TextChoices
from django.db.models.expressions import RawSQL
from django.db.models.fields import BooleanField, CharField, DateField, PositiveSmallIntegerField


class RecurrenceKind(TextChoices):
    DATE = "date", "Date"
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    EVERY_NTH = "every_nth", "Every N days"
    MONTHLY_DAYS = "monthly_days", "Monthly (specific day of month)"
    MONTHLY_NTH = "monthly_nth", "Monthly (nth week and day of week)"


class RecurrenceQuerySet(QuerySet):
    """
    Custom QuerySet for Recurrence.
    """
    def on_day(self, day):
        return self.on_dates([day])

    def between_dates(self, start_date, end_date):
        delta = end_date - start_date
        return self.on_dates([start_date + timedelta(days=i) for i in range(delta.days + 1)])

    def on_dates(self, days: list[date]):
        """
        Filtra recorrências que ocorrem em qualquer uma das datas fornecidas.
        :param days: lista de datas (date)
        :return: QuerySet filtrado
        """
        values_clause = ",".join(["(%s)"] * len(days))
        table = self.model._meta.db_table
        exists_sql = f"""
        EXISTS (
            SELECT 1
            FROM (VALUES {values_clause}) AS d(occur_date)
            WHERE
                -- A data candidata precisa estar dentro da janela da recorrência
                d.occur_date BETWEEN {table}.start_date
                               AND COALESCE({table}.end_date, d.occur_date)
            AND (
                ({table}.kind = '{RecurrenceKind.DATE}' AND {table}.on_date = d.occur_date)
                OR ({table}.kind = '{RecurrenceKind.DAILY}')
                OR ({table}.kind = '{RecurrenceKind.EVERY_NTH}'
                    AND ((d.occur_date - {table}.start_date) %% {table}.repeat_every) = 0)
                OR ({table}.kind = '{RecurrenceKind.WEEKLY}'
                    AND {table}.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE)
                OR ({table}.kind = '{RecurrenceKind.MONTHLY_DAYS}'
                    AND {table}.month_days[EXTRACT(DAY FROM d.occur_date)::int] IS TRUE)
                OR ({table}.kind = '{RecurrenceKind.MONTHLY_NTH}'
                    AND {table}.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE
                    AND (((EXTRACT(DAY FROM d.occur_date)::int - 1) / 7) + 1) = {table}.nth)
                    AND {table}.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE)
            )
        )
        """
        return self.all().annotate(_matches=RawSQL(exists_sql, days, output_field=BooleanField()))\
                         .filter(_matches=True)

    def recurrence_dates(self, start_date, end_date):
        """
        return list of dates with at least one recurrence between start_date and end_date (inclusive).
        Requires PostgreSQL.
        """
        sql = f"""
        WITH params AS (
          SELECT %(start)s::date AS start_date, %(end)s::date AS end_date
        ),
        days AS (
          SELECT gs::date AS occur_date
          FROM params, generate_series(
              (SELECT start_date FROM params),
              (SELECT end_date   FROM params),
              interval '1 day'
          ) AS gs
        )
        SELECT DISTINCT d.occur_date
        FROM days d
        JOIN {self.model._meta.db_table} r
          ON d.occur_date BETWEEN r.start_date AND COALESCE(r.end_date, d.occur_date)
        WHERE
          (
            (r.kind = '{RecurrenceKind.DATE}' AND r.on_date = d.occur_date)
            OR (r.kind = '{RecurrenceKind.DAILY}')
            OR (r.kind = '{RecurrenceKind.EVERY_NTH}'
                AND r.repeat_every IS NOT NULL AND r.repeat_every >= 1
                AND ((d.occur_date - r.start_date) %% r.repeat_every) = 0)
            OR (r.kind = '{RecurrenceKind.WEEKLY}'
                AND r.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE)
            OR (r.kind = '{RecurrenceKind.MONTHLY_DAYS}'
                AND r.month_days[EXTRACT(DAY FROM d.occur_date)::int] IS TRUE)
            OR (r.kind = '{RecurrenceKind.MONTHLY_NTH}'
                AND r.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE
                AND (((EXTRACT(DAY FROM d.occur_date)::int - 1) / 7) + 1) = r.nth)
                AND r.week_days[EXTRACT(ISODOW FROM d.occur_date)::int] IS TRUE)
          )
        ORDER BY d.occur_date;
        """
        with connection.cursor() as cur:
            cur.execute(sql, {"start": start_date, "end": end_date})
            rows = cur.fetchall()

        return [r[0] for r in rows]


class Recurrence(Model):
    kind = CharField(max_length=16, choices=RecurrenceKind.choices, db_index=True)
    start_date = DateField(db_index=True)
    end_date = DateField(null=True, db_index=True)

    on_date = DateField(null=True)  # DATE
    repeat_every = PositiveSmallIntegerField(null=True)  # EVERY_NTH (Every N units, Ex: every 14 days)
    week_days = ArrayField(BooleanField(), size=7, null=True, default=list)  # WEEKLY, MONTHLY_NTH
    month_days = ArrayField(BooleanField(), size=31, null=True, default=list)  # MONTHLY_DAYS
    nth = PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(5)])  # MONTHLY_NTH (every nth week)

    objects = RecurrenceQuerySet.as_manager()

    class Meta:
        abstract = True
        constraints = [
            # end_date >= start_date
            CheckConstraint(
                check=Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="%(app_label)s_%(class)s_end_after_start",
            ),
        ]

    def __str__(self):
        base = f"{self.get_kind_display()} @{self.start_date}"
        if self.end_date:
            base += f"–{self.end_date}"
        return base
