"""Intentional missing or weak function annotations for Ruff's ANN rules."""

from typing import Any


def missing_parameter(value) -> str:
    return str(value)


def missing_varargs(*values) -> int:
    return len(values)


def missing_kwargs(**values) -> int:
    return len(values)


def missing_public_return(value: int):
    return value


def _missing_private_return(value: int):
    return value


class MissingMethodReturns:
    def __init__(self):
        self.value = 1

    @staticmethod
    def identity(value: int):
        return value

    @classmethod
    def create(cls):
        return cls()


def weak_parameter(value: Any) -> str:
    return str(value)
