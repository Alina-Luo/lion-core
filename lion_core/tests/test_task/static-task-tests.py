import pytest
from pydantic import Field, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import ValidationError
from typing import Any

from lion_core.setting import LN_UNDEFINED
from lion_core.exceptions import LionValueError
from lion_core.generic.form import Form
from lion_core.task.base import BaseTask
from lion_core.task.static_task import StaticTask


# Helper class for testing
class SampleForm(Form):
    field1: str | None = Field(default=None)
    field2: int | None = Field(default=None)


# Test StaticTask initialization
def test_static_task_init():
    task = StaticTask(assignment="field1 -> field2")
    assert task.input_fields == ["field1"]
    assert task.request_fields == ["field2"]

    with pytest.raises(AttributeError):
        StaticTask(assignment="field1 -> field2", input_fields=["field1"])

    with pytest.raises(AttributeError):
        StaticTask(assignment="field1 -> field2", task="Some task")

    with pytest.raises(ValidationError):
        StaticTask(assignment="-> field2")

    with pytest.raises(ValidationError):
        StaticTask(assignment="field1 ->")


# Test input and output field addition
def test_static_task_field_addition():
    task = StaticTask(assignment="field1, field2 -> field3")
    assert "field1" in task.all_fields
    assert "field2" in task.all_fields
    assert "field3" in task.all_fields


# Test field modification prevention
def test_static_task_field_modification():
    task = StaticTask(assignment="field1 -> field2")

    with pytest.raises(AttributeError):
        task.input_fields = ["new_field"]

    with pytest.raises(AttributeError):
        task.request_fields = ["new_field"]

    with pytest.raises(AttributeError):
        task.assignment = "new_assignment"


# Test fill_input_fields method
def test_static_task_fill_input_fields():
    form = SampleForm(field1="test", field2=42)
    task = StaticTask(assignment="field1, field2 -> field3")

    task.fill_input_fields(form)
    assert task.field1 == "test"
    assert task.field2 == 42

    task = StaticTask(assignment="field1, field2 -> field3", none_as_valid_value=True)
    task.fill_input_fields(form=None, field1=None, field2=None)
    assert task.field1 is None
    assert task.field2 is None


# Test fill_request_fields method
def test_static_task_fill_request_fields():
    form = SampleForm(field1="test", field2=42)
    task = StaticTask(assignment="field1 -> field2")

    task.fill_request_fields(form)
    assert task.field2 == 42

    task = StaticTask(assignment="field1 -> field2", none_as_valid_value=True)
    task.fill_request_fields(form=None, field2=None)
    assert task.field2 is None


# Test from_form class method
def test_static_task_from_form():
    form = SampleForm(field1="test", field2=42)
    task = StaticTask.from_form("field1 -> field2", form)

    assert task.field1 == "test"
    assert isinstance(task.all_fields["field2"], FieldInfo)

    with pytest.raises(LionValueError):
        StaticTask.from_form("field3 -> field4", form)  # Invalid fields

    # Test with form class instead of instance
    task = StaticTask.from_form("field1 -> field2", SampleForm, field1="class_test")
    assert task.field1 == "class_test"


# Test none_as_valid_value behavior
def test_static_task_none_as_valid_value():
    task = StaticTask(assignment="field1 -> field2", none_as_valid_value=True)
    task.field1 = None
    task.field2 = None
    assert task.completed

    task = StaticTask(assignment="field1 -> field2", none_as_valid_value=False)
    task.field1 = None
    task.field2 = None
    assert not task.completed


# Test update_field method
def test_static_task_update_field():
    task = StaticTask(assignment="field1 -> field2")
    task.update_field("field1", value="updated")
    assert task.field1 == "updated"
    assert task.init_input_kwargs["field1"] == "updated"


# Test with complex assignments
def test_static_task_complex_assignments():
    task = StaticTask(assignment="field1, field2, field3 -> output1, output2")
    assert len(task.input_fields) == 3
    assert len(task.request_fields) == 2


# Test error cases
def test_static_task_error_cases():
    with pytest.raises(AttributeError):
        StaticTask()  # No assignment provided

    with pytest.raises(ValidationError):
        StaticTask(assignment="invalid assignment")

    task = StaticTask(assignment="field1 -> field2")
    with pytest.raises(LionValueError):
        task.fill_input_fields("not a form")


# Performance test
def test_static_task_performance():
    import time

    start_time = time.time()
    for _ in range(1000):
        task = StaticTask(assignment="field1, field2 -> output")
        task.fill_input_fields(field1="test", field2=42)
    end_time = time.time()

    assert end_time - start_time < 1  # Should complete in less than 1 second


# Test with LN_UNDEFINED
def test_static_task_ln_undefined():
    task = StaticTask(assignment="field1 -> field2")
    assert getattr(task, "field1") is LN_UNDEFINED
    assert getattr(task, "field2") is LN_UNDEFINED

    task.field1 = "defined"
    assert task.init_input_kwargs["field1"] == "defined"


# Test inheritance and method override
def test_static_task_inheritance():
    class CustomStaticTask(StaticTask):
        def custom_method(self):
            return "custom"

    task = CustomStaticTask(assignment="field1 -> field2")
    assert task.custom_method() == "custom"
    assert isinstance(task, BaseTask)


# Test with various data types
def test_static_task_data_types():
    class ComplexForm(Form):
        string_field: str = Field(default="")
        int_field: int = Field(default=0)
        float_field: float = Field(default=0.0)
        bool_field: bool = Field(default=False)
        list_field: list = Field(default_factory=list)
        dict_field: dict = Field(default_factory=dict)
        output: str = Field(default_factory=str)

    task = StaticTask.from_form(
        "string_field, int_field, float_field, bool_field, list_field, dict_field -> output",
        ComplexForm,
    )
    assert isinstance(task.all_fields["string_field"], FieldInfo)
    assert isinstance(task.all_fields["int_field"], FieldInfo)
    assert isinstance(task.all_fields["float_field"], FieldInfo)
    assert isinstance(task.all_fields["bool_field"], FieldInfo)
    assert isinstance(task.all_fields["list_field"], FieldInfo)
    assert isinstance(task.all_fields["dict_field"], FieldInfo)
