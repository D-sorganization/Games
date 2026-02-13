"""Design by Contract (DbC) decorators for the Games framework.

Provides reusable decorators for preconditions, postconditions,
and class invariants to enforce runtime correctness contracts
across game modules.

Usage:
    from games.shared.contracts import precondition, postcondition, invariant

    @precondition(lambda self, dt: dt > 0, "dt must be positive")
    def update(self, dt: float) -> None:
        ...

    @postcondition(lambda result: result >= 0, "health must be non-negative")
    def take_damage(self, amount: int) -> int:
        ...
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class ContractViolation(Exception):
    """Raised when a contract is violated.

    This covers preconditions, postconditions, and invariants.
    """


def precondition(
    check: Callable[..., bool],
    message: str = "Precondition violated",
) -> Callable[..., Any]:
    """Decorator that enforces a precondition before a function executes.

    Args:
        check: A callable that receives the same arguments as the decorated
            function and returns True if the precondition holds.
        message: Human-readable description of the contract.

    Returns:
        Decorator function.

    Raises:
        ContractViolation: If the precondition check returns False.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not check(*args, **kwargs):
                raise ContractViolation(
                    f"Precondition failed for {func.__qualname__}: {message}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def postcondition(
    check: Callable[..., bool],
    message: str = "Postcondition violated",
) -> Callable[..., Any]:
    """Decorator that enforces a postcondition on a function's return value.

    Args:
        check: A callable that receives the return value and returns True
            if the postcondition holds.
        message: Human-readable description of the contract.

    Returns:
        Decorator function.

    Raises:
        ContractViolation: If the postcondition check returns False.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if not check(result):
                raise ContractViolation(
                    f"Postcondition failed for {func.__qualname__}: {message}"
                )
            return result

        return wrapper

    return decorator


def invariant(
    check: Callable[..., bool],
    message: str = "Invariant violated",
) -> Callable[..., Any]:
    """Class decorator that enforces an invariant after each public method call.

    The invariant check receives the instance (self) and must return True
    if the invariant holds. It is checked after every public method
    (methods not starting with '_') completes.

    Args:
        check: A callable that receives self and returns True if valid.
        message: Human-readable description of the invariant.

    Returns:
        Class decorator function.
    """

    def class_decorator(cls: type) -> type:
        for attr_name in list(vars(cls)):
            if attr_name.startswith("_"):
                continue
            attr = getattr(cls, attr_name)
            if not callable(attr):
                continue

            original = attr

            @functools.wraps(original)
            def wrapped(
                *args: Any,
                _orig: Any = original,
                **kwargs: Any,
            ) -> Any:
                result = _orig(*args, **kwargs)
                instance = args[0] if args else None
                if instance is not None and not check(instance):
                    raise ContractViolation(
                        f"Invariant failed after {_orig.__qualname__}: {message}"
                    )
                return result

            setattr(cls, attr_name, wrapped)

        return cls

    return class_decorator


def validate_positive(value: float, name: str = "value") -> None:
    """Validate that a numeric value is positive.

    Args:
        value: The value to check.
        name: Name of the parameter for error messages.

    Raises:
        ContractViolation: If value is not positive.
    """
    if value <= 0:
        raise ContractViolation(f"{name} must be positive, got {value}")


def validate_non_negative(value: float, name: str = "value") -> None:
    """Validate that a numeric value is non-negative.

    Args:
        value: The value to check.
        name: Name of the parameter for error messages.

    Raises:
        ContractViolation: If value is negative.
    """
    if value < 0:
        raise ContractViolation(f"{name} must be non-negative, got {value}")


def validate_range(
    value: float,
    min_val: float,
    max_val: float,
    name: str = "value",
) -> None:
    """Validate that a numeric value falls within a range.

    Args:
        value: The value to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        name: Name of the parameter for error messages.

    Raises:
        ContractViolation: If value is outside the range.
    """
    if value < min_val or value > max_val:
        raise ContractViolation(
            f"{name} must be in [{min_val}, {max_val}], got {value}"
        )


def validate_not_none(value: Any, name: str = "value") -> None:
    """Validate that a value is not None.

    Args:
        value: The value to check.
        name: Name of the parameter for error messages.

    Raises:
        ContractViolation: If value is None.
    """
    if value is None:
        raise ContractViolation(f"{name} must not be None")
