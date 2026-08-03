import inspect

import pytest

from pystitia import (
    PostConditionError,
    PreConditionError,
    contracts,
    setTestMode,
)


@pytest.fixture(autouse=True)
def test_mode():
    setTestMode(True)
    yield
    setTestMode(True)


# ---------------------------------------------------------------------------
# functools.wraps metadata preservation
# ---------------------------------------------------------------------------

def test_preserves_name():
    @contracts()
    def square_root(x):
        """Compute the square root of x."""
        return x ** 0.5

    assert square_root.__name__ == "square_root"


def test_preserves_docstring():
    @contracts()
    def square_root(x):
        """Compute the square root of x."""
        return x ** 0.5

    assert square_root.__doc__ == "Compute the square root of x."


def test_preserves_module():
    @contracts()
    def square_root(x):
        return x ** 0.5

    assert square_root.__module__ == __name__


def test_preserves_qualname():
    class Foo:
        @contracts()
        def bar(self):
            return 1

    assert Foo.bar.__qualname__.endswith("Foo.bar")


def test_exposes_wrapped():
    def square_root(x):
        return x ** 0.5

    decorated = contracts()(square_root)
    assert decorated.__wrapped__ is square_root


def test_signature_matches_original():
    @contracts()
    def square_root(x, y=2):
        return x ** (1 / y)

    sig = inspect.signature(square_root)
    assert list(sig.parameters) == ["x", "y"]
    assert sig.parameters["y"].default == 2


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------

def test_precondition_pass():
    @contracts(preconditions=[lambda x: x > 0])
    def square_root(x):
        return x ** 0.5

    assert square_root(16) == 4.0


def test_precondition_fail_raises():
    @contracts(preconditions=[lambda x: x > 0])
    def square_root(x):
        return x ** 0.5

    with pytest.raises(PreConditionError):
        square_root(-5)


def test_multiple_stacked_preconditions_all_checked():
    calls = []

    def cond_a(x):
        calls.append("a")
        return x > 0

    def cond_b(x):
        calls.append("b")
        return x < 100

    @contracts(preconditions=[cond_a, cond_b])
    def identity(x):
        return x

    assert identity(5) == 5
    assert calls == ["a", "b"]


def test_precondition_failure_reports_failed_index():
    @contracts(preconditions=[lambda x: x > 0, lambda x: x < 10])
    def identity(x):
        return x

    with pytest.raises(PreConditionError) as excinfo:
        identity(20)
    assert "identity" in str(excinfo.value)
    assert "1" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Postconditions
# ---------------------------------------------------------------------------

def test_postcondition_pass():
    @contracts(postconditions=[lambda __return__: __return__ > 0])
    def square_root(x):
        return x ** 0.5

    assert square_root(16) == 4.0


def test_postcondition_fail_raises():
    @contracts(postconditions=[lambda __return__: __return__ > 100])
    def square_root(x):
        return x ** 0.5

    with pytest.raises(PostConditionError):
        square_root(16)


def test_multiple_stacked_postconditions_all_checked():
    calls = []

    def cond_a(__return__):
        calls.append("a")
        return __return__ > 0

    def cond_b(__return__):
        calls.append("b")
        return __return__ < 100

    @contracts(postconditions=[cond_a, cond_b])
    def identity(x):
        return x

    assert identity(5) == 5
    assert calls == ["a", "b"]


def test_postcondition_failure_reports_failed_index():
    @contracts(postconditions=[lambda __return__: __return__ > 0, lambda __return__: __return__ < 10])
    def identity(x):
        return x

    with pytest.raises(PostConditionError) as excinfo:
        identity(20)
    assert "identity" in str(excinfo.value)
    assert "1" in str(excinfo.value)


def test_postcondition_old_value_access():
    @contracts(postconditions=[lambda __return__, amount: __return__ == __old__.balance - amount])
    def withdraw(balance, amount):
        return balance - amount

    assert withdraw(100, 30) == 70


def test_postcondition_id_immutability_check():
    @contracts(postconditions=[lambda data: id(data) == __id__.data])
    def append_item(data, item):
        data.append(item)
        return data

    assert append_item([1, 2], 3) == [1, 2, 3]


# ---------------------------------------------------------------------------
# setTestMode
# ---------------------------------------------------------------------------

def test_setTestMode_false_bypasses_precondition_checks():
    @contracts(preconditions=[lambda x: x > 0])
    def identity(x):
        return x

    setTestMode(False)
    try:
        assert identity(-5) == -5
    finally:
        setTestMode(True)


# ---------------------------------------------------------------------------
# Keyword-argument support
# ---------------------------------------------------------------------------

def test_call_with_positional_args():
    @contracts(preconditions=[lambda balance, amount: amount > 0])
    def withdraw(balance, amount):
        return balance - amount

    assert withdraw(100, 30) == 70


def test_call_with_keyword_args():
    @contracts(preconditions=[lambda balance, amount: amount > 0])
    def withdraw(balance, amount):
        return balance - amount

    assert withdraw(balance=100, amount=30) == 70


def test_call_with_mixed_args():
    @contracts(preconditions=[lambda balance, amount: amount > 0])
    def withdraw(balance, amount):
        return balance - amount

    assert withdraw(100, amount=30) == 70


def test_call_with_keyword_args_uses_default_value():
    @contracts(preconditions=[lambda x, y: y > 0])
    def power(x, y=2):
        return x ** y

    assert power(x=3) == 9
    assert power(x=3, y=3) == 27


def test_postcondition_old_value_with_keyword_call():
    @contracts(postconditions=[lambda __return__, amount: __return__ == __old__.balance - amount])
    def withdraw(balance, amount):
        return balance - amount

    assert withdraw(balance=100, amount=30) == 70


def test_precondition_failure_with_keyword_call():
    @contracts(preconditions=[lambda amount: amount > 0])
    def withdraw(balance, amount):
        return balance - amount

    with pytest.raises(PreConditionError):
        withdraw(balance=100, amount=-30)
