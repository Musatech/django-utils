from typing import Any

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class WordsCountValidator:
    def __init__(self, words, operation='min', allow_null=False, allow_blank=False):
        assert operation in ('min', 'max', 'exact'), "operation must be 'min', 'max', or 'exact'."
        if not isinstance(words, int) or words < 1:
            raise ValueError("words must be a positive integer.")
        self.words = words
        self.operation = operation
        self.allow_null = allow_null
        self.allow_blank = allow_blank

    def __call__(self, value):
        if value is None and self.allow_null:
            return
        if value == "" and self.allow_blank:
            return

        if self.operation == 'min' and len(value.strip().split()) < self.words:
            raise ValidationError(
                _(f"Value must have at least {self.words} words.")
            )
        elif self.operation == 'max' and len(value.strip().split()) > self.words:
            raise ValidationError(
                _(f"Value must have no more than {self.words} words.")
            )
        elif self.operation == 'exact' and len(value.strip().split()) != self.words:
            raise ValidationError(
                _(f"Value must have exactly {self.words} words.")
            )


@deconstructible
class WordLengthValidator:
    def __init__(self, length, operation='min', allow_null=False, allow_blank=False):
        assert operation in ('min', 'max', 'exact'), "operation must be 'min', 'max', or 'exact'."
        if not isinstance(length, int) or length < 1:
            raise ValueError("length must be a positive integer.")
        self.length = length
        self.operation = operation
        self.allow_null = allow_null
        self.allow_blank = allow_blank

    def __call__(self, value):
        if value is None and self.allow_null:
            return
        if value == "" and self.allow_blank:
            return

        for word in value.strip().split():
            if self.operation == 'min' and len(word) < self.length:
                raise ValidationError(
                    _(f"Each word must be at least {self.length} characters long.")
                )
            elif self.operation == 'max' and len(word) > self.length:
                raise ValidationError(
                    _(f"Each word must be no more than {self.length} characters long.")
                )
            elif self.operation == 'exact' and len(word) != self.length:
                raise ValidationError(
                    _(f"Each word must be exactly {self.length} characters long.")
                )


@deconstructible
class RepeatedWordsValidator:
    def __init__(self, scope='global', allow_null=False, allow_blank=False):
        assert scope in ('global', 'sequential'), "scope must be 'global' or 'sequential'."
        self.scope = scope
        self.allow_null = allow_null
        self.allow_blank = allow_blank

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.scope == 'global':
            if args[0] is None and self.allow_null:
                return
            if args[0] == "" and self.allow_blank:
                return
            words = args[0].strip().split()
            seen = set()
            for word in words:
                if word in seen:
                    raise ValidationError(
                        _("Value must not contain repeated words.")
                    )
                seen.add(word)
        elif self.scope == 'sequential':
            words = args[0].strip().split()
            for i in range(1, len(words)):
                if words[i] == words[i - 1]:
                    raise ValidationError(
                        _("Value must not contain sequentially repeated words.")
                    )


@deconstructible
class AlphabeticWordsValidator:
    def __init__(self, allow_null=False, allow_blank=False):
        self.allow_null = allow_null
        self.allow_blank = allow_blank

    def __call__(self, value):
        if value is None and self.allow_null:
            return
        if value == "" and self.allow_blank:
            return
        for word in value.strip().split():
            if not word.isalpha():
                raise ValidationError(
                    _("Each word must contain only alphabetic characters.")
                )


class NameValidator:
    def __init__(self, allow_null=False, allow_blank=False):
        self.validators = [
            AlphabeticWordsValidator(allow_null=allow_null, allow_blank=allow_blank),
            WordsCountValidator(2, operation='min', allow_null=allow_null, allow_blank=allow_blank),
            RepeatedWordsValidator(scope='sequential', allow_null=allow_null, allow_blank=allow_blank)
        ]

    def __call__(self, value):
        for validator in self.validators:
            validator(value)
