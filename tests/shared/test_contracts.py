"""Tests for the games.shared.contracts module."""

from __future__ import annotations

import pytest

from games.shared.contracts import (
    ContractViolation,
    invariant,
    postcondition,
    precondition,
    validate_non_negative,
    validate_not_none,
    validate_positive,
    validate_range,
)


class TestPrecondition:
    """Tests for the @precondition decorator."""

    def test_precondition_passes_when_check_is_true(self) -> None:
        """Precondition should allow execution when check passes."""

        @precondition(lambda x: x > 0, "x must be positive")
        def double(x: int) -> int:
            """Double a positive integer."""
            return x * 2

        assert double(5) == 10

    def test_precondition_raises_when_check_is_false(self) -> None:
        """Precondition should raise ContractViolation when check fails."""

        @precondition(lambda x: x > 0, "x must be positive")
        def double(x: int) -> int:
            """Double a positive integer."""
            return x * 2

        with pytest.raises(ContractViolation, match="x must be positive"):
            double(-1)

    def test_precondition_with_method(self) -> None:
        """Precondition should work with instance methods."""

        class Counter:
            """A simple counter with precondition."""

            def __init__(self) -> None:
                """Initialize counter at zero."""
                self.value = 0

            @precondition(lambda self, n: n >= 0, "n must be non-negative")
            def add(self, n: int) -> None:
                """Add n to the counter."""
                self.value += n

        c = Counter()
        c.add(5)
        assert c.value == 5

        with pytest.raises(ContractViolation):
            c.add(-1)

    def test_precondition_preserves_function_name(self) -> None:
        """Precondition should preserve the original function's name."""

        @precondition(lambda x: True, "always passes")
        def my_function(x: int) -> int:
            """A documented function."""
            return x

        assert my_function.__name__ == "my_function"

    def test_precondition_with_kwargs(self) -> None:
        """Precondition should work with keyword arguments."""

        @precondition(lambda x, y=0: y != 0, "y must not be zero")
        def divide(x: float, y: float = 0) -> float:
            """Divide x by y."""
            return x / y

        assert divide(10, y=2) == 5.0

        with pytest.raises(ContractViolation):
            divide(10, y=0)


class TestPostcondition:
    """Tests for the @postcondition decorator."""

    def test_postcondition_passes_when_result_is_valid(self) -> None:
        """Postcondition should allow return when check passes."""

        @postcondition(lambda result: result >= 0, "result must be non-negative")
        def absolute(x: int) -> int:
            """Return absolute value."""
            return abs(x)

        assert absolute(-5) == 5

    def test_postcondition_raises_when_result_is_invalid(self) -> None:
        """Postcondition should raise when result check fails."""

        @postcondition(lambda result: result > 0, "result must be positive")
        def negate(x: int) -> int:
            """Negate a number."""
            return -x

        with pytest.raises(ContractViolation, match="result must be positive"):
            negate(5)

    def test_postcondition_preserves_function_name(self) -> None:
        """Postcondition should preserve the original function's name."""

        @postcondition(lambda r: True, "always passes")
        def my_func(x: int) -> int:
            """A documented function."""
            return x

        assert my_func.__name__ == "my_func"

    def test_postcondition_with_none_return(self) -> None:
        """Postcondition should work with None return values."""

        @postcondition(lambda result: result is None, "must return None")
        def do_nothing() -> None:
            """Return nothing."""
            return None

        do_nothing()  # Should not raise


class TestInvariant:
    """Tests for the @invariant class decorator."""

    def test_invariant_passes_after_valid_mutation(self) -> None:
        """Invariant should pass when class state remains valid."""

        @invariant(lambda self: self.value >= 0, "value must be non-negative")
        class PositiveCounter:
            """A counter that must stay non-negative."""

            def __init__(self) -> None:
                """Initialize at zero."""
                self.value = 0

            def increment(self) -> None:
                """Increment by one."""
                self.value += 1

        c = PositiveCounter()
        c.increment()
        assert c.value == 1

    def test_invariant_raises_after_invalid_mutation(self) -> None:
        """Invariant should raise when class state becomes invalid."""

        @invariant(lambda self: self.value >= 0, "value must be non-negative")
        class PositiveCounter:
            """A counter that must stay non-negative."""

            def __init__(self) -> None:
                """Initialize at zero."""
                self.value = 0

            def decrement(self) -> None:
                """Decrement by one."""
                self.value -= 1

        c = PositiveCounter()
        with pytest.raises(ContractViolation, match="value must be non-negative"):
            c.decrement()

    def test_invariant_ignores_private_methods(self) -> None:
        """Invariant should not check after private method calls."""

        @invariant(lambda self: self.value >= 0, "value must be non-negative")
        class Flexible:
            """A class with private methods that can violate invariant."""

            def __init__(self) -> None:
                """Initialize at zero."""
                self.value = 0

            def _internal_set(self, v: int) -> None:
                """Set value without invariant check."""
                self.value = v

        f = Flexible()
        f._internal_set(-1)  # Should not raise — private method
        assert f.value == -1


class TestValidationUtilities:
    """Tests for standalone validation functions."""

    def test_validate_positive_passes(self) -> None:
        """validate_positive should pass for positive values."""
        validate_positive(1.0)
        validate_positive(0.001)
        validate_positive(1000)

    def test_validate_positive_fails_for_zero(self) -> None:
        """validate_positive should fail for zero."""
        with pytest.raises(ContractViolation, match="must be positive"):
            validate_positive(0)

    def test_validate_positive_fails_for_negative(self) -> None:
        """validate_positive should fail for negative values."""
        with pytest.raises(ContractViolation, match="must be positive"):
            validate_positive(-5.0, "delta_time")

    def test_validate_non_negative_passes(self) -> None:
        """validate_non_negative should pass for zero and positive."""
        validate_non_negative(0)
        validate_non_negative(1.0)

    def test_validate_non_negative_fails(self) -> None:
        """validate_non_negative should fail for negative values."""
        with pytest.raises(ContractViolation, match="must be non-negative"):
            validate_non_negative(-0.001, "health")

    def test_validate_range_passes(self) -> None:
        """validate_range should pass for values within range."""
        validate_range(5, 0, 10)
        validate_range(0, 0, 10)
        validate_range(10, 0, 10)

    def test_validate_range_fails_below(self) -> None:
        """validate_range should fail for values below minimum."""
        with pytest.raises(ContractViolation, match=r"must be in \[0, 10\]"):
            validate_range(-1, 0, 10, "level")

    def test_validate_range_fails_above(self) -> None:
        """validate_range should fail for values above maximum."""
        with pytest.raises(ContractViolation, match=r"must be in \[0, 10\]"):
            validate_range(11, 0, 10)

    def test_validate_not_none_passes(self) -> None:
        """validate_not_none should pass for non-None values."""
        validate_not_none(0)
        validate_not_none("")
        validate_not_none([])

    def test_validate_not_none_fails(self) -> None:
        """validate_not_none should fail for None."""
        with pytest.raises(ContractViolation, match="must not be None"):
            validate_not_none(None, "player")


class TestCombinedContracts:
    """Tests for combining multiple contract decorators."""

    def test_precondition_and_postcondition_together(self) -> None:
        """Both pre and postcondition should be checked."""

        @precondition(lambda x: x >= 0, "input must be non-negative")
        @postcondition(lambda result: result >= 0, "result must be non-negative")
        def square_root_floor(x: int) -> int:
            """Return integer square root."""
            return int(x**0.5)

        assert square_root_floor(16) == 4
        assert square_root_floor(0) == 0

        with pytest.raises(ContractViolation, match="input must be non-negative"):
            square_root_floor(-1)
