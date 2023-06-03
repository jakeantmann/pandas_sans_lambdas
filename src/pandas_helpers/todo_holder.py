

# %%
# TODO Incorporate series_dict
# TODO Remove prints

# TODO LATER:
# TODO Finish off the accessor-specific TODOs
# TODO Build each text part with a function
# TODO Put these functions, and the module writer, in a private helper file
# TODO Separate the testing functions from the text-writing functions

# TODO for cat: check add_categories, as_ordered, as_unordered, remove_categories, reorder_categories, set_categories - can any take a series?
# TODO for dt: check all methods except to_pydatetime
# TODO for sparse: check from_coo (param A)

# TODO Ignores private attrs (e.g. _constructor)
# TODO Ignores some dunder methods (e.g. __new__)
# TODO Add the ignored methods (incl dunders) to documentation

import inspect
import operator
import re

import itertools

import pandas as pd

# %% Classes and functions
def flatten_comprehension(source_list, func):
    return list(itertools.chain.from_iterable(func(i) for i in source_list))

def make_simple_property(property_name):
    return [
        f"    def {property_name}(self, DF):",
        f"        return self.__call__(DF).{property_name}",
        "",
    ]

def write_property_code(properties):
    return flatten_comprehension(properties, make_simple_property)


def make_col_test_method(method, param_to_test, params_with_self_with_default_args_str, param_names_str):
    params_str_DF = param_names_str.replace(param_to_test, f"{param_to_test}(DF)")

    return [
        f"    def {method}({params_with_self_with_default_args_str}):",
        f"        if is_col_test({param_to_test}):",
        f"            return CallCol(lambda DF: self.__call__(DF).{method}({params_str_DF}))",
        f"        else:",
        f"            return CallCol(lambda DF: self.__call__(DF).{method}({param_names_str}))",
        f"",
    ]


def make_simple_method(method, params_with_self_with_default_args_str, param_names_str):
    return [
        f"    def {method}({params_with_self_with_default_args_str}):",
        f"        return CallCol(lambda DF: self.__call__(DF).{method}({param_names_str}))",
        f"",
    ]


def write_indexer_class(indexer_name):
    return [
        f"class {indexer_name.capitalize()}Indexer:",
        f"    def __init__(self, func):",
        f"        self.func = func",

        f"    def __getitem__(self, *indexes):",
        f"        return CallCol(lambda DF: self.func(DF).{indexer_name}.__getitem__(*indexes))",
        f"",
    ]


def write_indexer(indexer_name):
    return [
        f"    @property",
        f"    def {indexer_name}(self):",
        f"        return {indexer_name.capitalize()}Indexer(self.__call__)",
        f"",
    ]


def make_code_helpers(series_object, method_name):
    params = inspect.signature(getattr(series_object, method_name)).parameters

    params_str = (
        ", "
        .join(params.keys())
        # .replace("'", "\"")
    )

    params_str = re.sub("([^*w])args", "\\1*args", params_str)
    params_str = re.sub("([^*])kwargs", "\\1**kwargs", params_str)
    params_str = re.sub("^args", "*args", params_str)
    params_str = re.sub("^kwargs", "**kwargs", params_str)

    default_params_str = (
        ", "
        .join(["self", *[str(value) for value in params.values()]])
        # .replace("'", "\"")
    )

    return default_params_str, params_str


def make_accessor_property_code(accessor):
    return [
        f"    @property",
        f"    def {accessor}(self):",
        f"        return {accessor.capitalize()}Accessor(self.__call__)",
        f"",
    ]

# %%
def find_attrs(series_dict):
    most_attrs = []

    for _, series in series_dict.items():
        most_attrs = most_attrs + [i for i in dir(series) if not i.startswith("_")]

    return sorted(set(most_attrs))

def find_attr_groups(attr_list, series, accessors = ["cat", "dt", "str", "sparse", "plot"]):
    attr_groups = {
        "accessors": accessors,
        "indexers": [],
        "methods": [],
        "properties": [],
    }

    for attr_string in attr_list:
        if attr_string in attr_groups["accessors"]:
            continue

        attr = getattr(series, attr_string)
        type_string = str(type(attr)).lower()

        if "indexing" in type_string:
            attr_groups["indexers"].append(attr_string)
        elif "method" in type_string:
            attr_groups["methods"].append(attr_string)
        elif callable(attr):
            raise Exception(f"The attr {attr_string} is not a method or an indexer")
        else:
            attr_groups["properties"].append(attr_string)
    return attr_groups

def write_regular_methods_code(obj, methods):
    output_code = []

    for method in methods:
        code_helpers = make_code_helpers(obj, method)
        if method == "ewm":
            code = make_col_test_method(method, "times", *code_helpers)
        elif method == "map":
            code = make_col_test_method(method, "arg", *code_helpers)
        elif method == "fillna":
            code = make_col_test_method(method, "value", *code_helpers)
        elif "other" in code_helpers[1]:
            code = make_col_test_method(method, "other", *code_helpers)
        else:
            code = make_simple_method(method, *code_helpers)
        output_code += code

    return output_code

def write_indexer_class_code(indexer_list):
    return flatten_comprehension(indexer_list, write_indexer_class)

def write_indexer_code(indexer_list):
    return flatten_comprehension(indexer_list, write_indexer)

def write_accessor_code(accessor_list):
    return flatten_comprehension(accessor_list, make_accessor_property_code)

def get_methods_and_properties(obj, extra_attrs = []):
    attrs = [i for i in dir(obj) if not i.startswith("_")]
    attrs += extra_attrs

    methods = []
    properties = []

    for attr in attrs:
        if callable(getattr(obj, attr)):
            methods.append(attr)
        else:
            properties.append(attr)
    
    return methods, properties

def write_str_accessor_class_code(series_dict, accessor_name):
    obj = getattr(series_dict[accessor_name], accessor_name)
    methods, properties = get_methods_and_properties(obj)

    output_code = [
        f"class {accessor_name.capitalize()}Accessor(object):",
    ]

    output_code += write_property_code(properties)

    for method in methods:
        code_helpers = make_code_helpers(obj, method)

        if method == "cat":
            code = make_col_test_method(method, "others", *code_helpers)
        else:
            code = make_simple_method(method, *code_helpers)

        output_code += code
    
    return output_code

def write_accessor_class_code(series_dict, accessor_name, extra_attrs = []):
    obj = getattr(series_dict[accessor_name], accessor_name)
    methods, properties = get_methods_and_properties(obj, extra_attrs)

    output_code = [
        f"class {accessor_name.capitalize()}Accessor(object):",
    ]

    output_code += write_property_code(properties)
    for method in methods:
        output_code += make_simple_method(method, *make_code_helpers(obj, method))
    
    return output_code

def check_series_dunder_attrs(operator_dunder_attrs, series):
    exclusion_list = [
        "__concat__",
        "__iconcat__",
        "__ilshift__",
        "__imatmul__",
        "__index__",
        "__inv__",
        "__irshift__",
        "__lshift__",
        "__not__",
        "__rshift__",
    ]

    for attr in operator_dunder_attrs:
        if attr in exclusion_list:
            continue

        attr_type = type(getattr(operator, attr))

        if "builtin_function_or_method" not in str(attr_type):
            continue
        try:
            type(getattr(series, attr))
        except AttributeError:
            raise AttributeError(f"{attr} | {attr_type}")

def find_dunder_attr_groups(attrs, series):
    attr_groups = {
        "builtins": [],
        "methods": [],
        "properties": [],
    }    
    
    for attr in attrs:
        if attr == "__weakref__":
            continue

        attr_obj = getattr(series, attr)
        type_string = str(type(attr_obj))

        if "builtin" in type_string:
            attr_groups["builtins"].append(attr)
        elif attr == "__class__":
            attr_groups["methods"].append(attr)
        elif "method" in type_string:
            attr_groups["methods"].append(attr)
        elif callable(attr_obj):
            raise Exception(f"The callable attr {attr} is not a builtin or method")
        else:
            attr_groups["properties"].append(attr)
    
    return attr_groups

def write_dunder_methods_code(series, methods):
    methods_to_exclude = [
        "__init__",
        "__new__",
        "__copy__",
        "__deepcopy__",
        "__delattr__",
        "__delitem__",
        "__dir__",
        "__finalize__",
        "__getattr__",
        "__getattribute__",
        "__getitem__",
        "__getstate__",
        "__iter__",
        "__repr__",
        "__setattr__",
        "__setitem__",
        "__setstate__",
        "__sizeof__",
        "__str__",
        "__weakref__",
    ]
    
    output_code = []
    
    for method in methods:
        if method in methods_to_exclude:
            continue

        code_helpers = make_code_helpers(series, method)

        if method == "__class__":
            code = make_col_test_method(method, "data", *code_helpers)
        elif "other" in code_helpers[1]:
            code = make_col_test_method(method, "other", *code_helpers)
        else:
            code = make_simple_method(method, *code_helpers)

        output_code += code
    
    return output_code

def check_builtins(builtins):
    known_builtins = [
        '__format__',
        '__init_subclass__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__subclasshook__',
    ]

    for builtin_name in builtins:
        if builtin_name not in known_builtins:
            raise Exception(f"The builtin {builtin_name} is not accounted for.")

# %% Write non-dunder methods, properties and classes
series_dict = {
    "plot": pd.Series([1, 2, 3], name="beep"),
    "cat": pd.Series(pd.Categorical(['c', 'b', 'c'])),
    "dt": pd.Series(pd.date_range("2000-01-01", periods=3, freq="ns")),
    "str": pd.Series(list("abc"), dtype="string"),
    "sparse": pd.Series(pd.arrays.SparseArray([0, 0, 1, 1, 1], fill_value=0)),
}

attr_groups = find_attr_groups(find_attrs(series_dict), series_dict["plot"])

##### %% Dunders
integer_series = series_dict["plot"]

operator_dunder_attrs = sorted([i for i in dir(operator) if i.startswith("__")])
series_dunder_attrs = sorted([i for i in dir(integer_series) if i.startswith("__")])

# %% Check that all operator dunders are series dunders, except the exclusion list
check_series_dunder_attrs(operator_dunder_attrs, integer_series)

# %% Find dunder attr groups
dunder_attr_groups = find_dunder_attr_groups(series_dunder_attrs, integer_series)
check_builtins(dunder_attr_groups["builtins"])


# %%
output = [
    "\"\"\"Auto-generated dunder method col implementation\"\"\"",
    "",
    "# %% Imports",
    "from abc import abstractmethod",
    "from dataclasses import dataclass",
    "from typing import Any, Callable, Literal, Hashable",
    "import re",
    "",
    "import numpy as np",
    "import numpy.typing as npt",
    "",
    "import pandas as pd",
    "from pandas import Series, DataFrame",
    "from pandas.core.indexers.objects import BaseIndexer",
    "from pandas._typing import (",
    "    AggFuncType,",
    "    AlignJoin,",
    "    AnyAll,",
    "    AnyArrayLike,",
    "    Axis,",
    "    AxisInt,",
    "    BaseOffset,",
    "    CompressionOptions,",
    "    CorrelationMethod,",
    "    DataFrame,",
    "    DropKeep,",
    "    Dtype,",
    "    DtypeArg,",
    "    DtypeBackend,",
    "    ExtensionArray,",
    "    FilePath,",
    "    FillnaOptions,",
    "    FloatFormatType,",
    "    FormattersType,",
    "    Frequency,",
    "    HDFStore,",
    "    IgnoreRaise,",
    "    IndexKeyFunc,",
    "    IndexLabel,",
    "    IntervalClosedType,",
    "    IO,",
    "    JSONSerializable,",
    "    Level,",
    "    Mapping,",
    "    NaPosition,",
    "    NumpySorter,",
    "    NumpyValueArrayLike,",
    "    QuantileInterpolation,",
    "    RandomState,",
    "    Renamer,",
    "    Scalar,",
    "    Sequence,",
    "    SortKind,",
    "    StorageOptions,",
    "    Suffixes,",
    "    TimeAmbiguous,",
    "    TimedeltaConvertibleTypes,",
    "    TimeNonexistent,",
    "    TimestampConvertibleTypes,",
    "    ValueKeyFunc,",
    "    WriteBuffer,",
    ")",
    "from pandas._libs import lib",
    "",
    "bool_t = bool",
    "",
    "# %% Classes and functions",
    "def is_col_test(obj):",
    "    return hasattr(obj, \"_is_col\")",
    "",
    "@dataclass",
    "class Col(BaseCol):",
    "    col_name: Any",
    "    ",
    "    def __call__(self, DF):",
    "        return DF[self.col_name]",
    "",
    "@dataclass",
    "class CallCol(BaseCol):",
    "    fn: Callable",
    "    ",
    "    def __call__(self, DF):",
    "        return self.fn(DF)",
    "",
    *write_indexer_class_code(attr_groups["indexers"]),
    *write_str_accessor_class_code(series_dict, "str"),
    *write_accessor_class_code(series_dict, "cat"),
    *write_accessor_class_code(series_dict, "dt"),
    *write_accessor_class_code(series_dict, "sparse"),
    *write_accessor_class_code(series_dict, "plot", extra_attrs = ["__call__"]),
    "class BaseCol(object):",
    "    _is_col = True",
    "",
    "    @abstractmethod",
    "    def __call__(self, df):",
    "        pass",
    "",
    *write_property_code(dunder_attr_groups["properties"]),
    *write_accessor_code(attr_groups["accessors"]),
    *write_property_code(attr_groups["properties"]),
    *write_indexer_code(attr_groups["indexers"]),
    *write_dunder_methods_code(integer_series, dunder_attr_groups["methods"]),
    *write_regular_methods_code(integer_series, attr_groups["methods"]),
]

# %%
output = [re.sub("Literal\[\((.+?)\)\]", "Literal[\\1]", i) for i in output]
output = [i.replace("<no_default>", "lib.no_default") for i in output]
output = [i.replace("<class 'dict'>", "dict") for i in output]

# %%
with open("./src/pandas_helpers/dunder_methods_autogen_full.py", "w") as f:
    f.write("\n".join(output))

# %%

# %%
