"""Test core Col functionality."""

# %% Imports
from contextlib import nullcontext as does_not_raise

import pandas as pd
import pytest

from pandas_helpers.helpers import BaseCol, CallCol, Col, _is_col_test, _decide_if_call

# %% Data
df = pd.DataFrame(dict(a=[1,2,3], b=[4,5,6]))
df2 = pd.DataFrame({tuple([1,2,3]): [1,2,3]})

# %% Test _is_col_test
@pytest.mark.parametrize(
    "obj,expectation",
    [
        (Col("a"), True),
        (1, False),
        (df["a"], False),
        (None, False),
    ],
)
def test_is_col_test(obj, expectation):
    """Test _is_col_test."""
    assert _is_col_test(obj) == expectation


@pytest.mark.parametrize(
    "args,expectation",
    [
        ((1,), does_not_raise()),
        ((df["a"],), does_not_raise()),
        ((Col("a"),), does_not_raise()),
        (tuple(), pytest.raises(TypeError)),
        ((1,2), pytest.raises(TypeError)),
        ((Col("a"),Col("b")), pytest.raises(TypeError)),
    ],
)
def test_is_col_test_errors(args, expectation):
    """Test _is_col_test errors."""
    with expectation:
        _is_col_test(*args)

# %% Test _decide_if_call
@pytest.mark.parametrize(
    "obj1,obj2,expectation",
    [
        (Col("a"), df, pd.Series),
    ],
)
def test_decide_if_call(obj1, obj2, expectation):
    """Test _decide_if_call."""
    assert isinstance(_decide_if_call(obj1, obj2), expectation)

@pytest.mark.parametrize(
    "arg1,arg2,expectation",
    [
        (Col("a"), df, does_not_raise()),        
        (Col((1, 2, 3)), df2, does_not_raise()),        
        (Col("ABC"), df, pytest.raises(KeyError)),
        (Col("a"), df["a"], pytest.raises(KeyError)),
        (Col("a"), 1, pytest.raises(TypeError)),        
    ],
)
def test_decide_if_call_errors(arg1, arg2, expectation):
    """Test _decide_if_call errors."""
    with expectation:
        _decide_if_call(arg1, arg2)
