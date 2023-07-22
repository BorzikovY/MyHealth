import re
from datetime import timedelta
from typing import Callable

from rest_framework.filters import BaseFilterBackend
import coreapi


class duration(timedelta):
    def __new__(cls, string, **kwargs):
        data = enumerate(reversed((string.split(":"))))
        validated_data = map(lambda val: int(val[1]) * 60**val[0], data)
        return super(duration, cls).__new__(cls, seconds=sum(validated_data))


class ProgramFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        difficulty = coreapi.Field(
            name='difficulty',
            location='query',
            required=False,
            type='string'
        )
        weeks = coreapi.Field(
            name='weeks',
            location='query',
            required=False,
            type='string'
        )
        return [difficulty, weeks]


class NutritionFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        program_id = coreapi.Field(
            name='program_id',
            location='query',
            required=True,
            type='string'
        )
        dosages = coreapi.Field(
            name='dosages',
            location='query',
            required=False,
            type='string'
        )
        use = coreapi.Field(
            name='use',
            location='query',
            required=False,
            type='string'
        )
        contraindications = coreapi.Field(
            name='contraindications',
            location='query',
            required=False,
            type='string'
        )
        return [program_id, dosages, use, contraindications]


class TrainingFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        program_id = coreapi.Field(
            name='program_id',
            location='query',
            required=True,
            type='string'
        )
        difficulty = coreapi.Field(
            name='difficulty',
            location='query',
            required=False,
            type='string'
        )
        approach_time = coreapi.Field(
            name='time',
            location='query',
            required=False,
            type='string'
        )
        return [program_id, difficulty, approach_time]


class ExerciseFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        training_id = coreapi.Field(
            name='training_id',
            location='query',
            required=True,
            type='string'
        )
        return [training_id,]


class DataFilter:

    EXP_FORMAT = r"(?:[<>]=?|=)"
    FILTER_EXP = {
        "<": "__gt__",
        "<=": "__ge__",
        ">": "__lt__",
        ">=": "__le__",
        "=": "__eq__"
    }
    PATTERNS = {
        float: r'([0-9]*[.])?[0-9]+',
        int: r'[-]?[0-9]+',
        duration: r'[0-9]+:[0-5][0-9]',
        str: r'.*'
    }

    @classmethod
    def filter(
            cls, string: str | None, data_class
    ) -> Callable:
        if string is not None:
            value_match, op_match = (
                re.search(cls.PATTERNS[data_class], string),
                re.search(cls.EXP_FORMAT, string)
            )
            if value_match and op_match:
                op, value = (
                    cls.FILTER_EXP[op_match.group(0)],
                    data_class(value_match.group(0))
                )
                return getattr(value, op)
        return lambda val: True
