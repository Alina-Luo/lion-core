import pytest
from pydantic import Field, ValidationError
from typing import Any, Literal

from lion_core.setting import LN_UNDEFINED
from lion_core.abc import MutableRecord
from lion_core.generic.component import Component
from lion_core.task.base import BaseTask  # Assuming the BaseTask is in base.py


# Helper function to create a BaseTask instance
def create_base_task(**kwargs):
    class TestTask(BaseTask):
        test_input: str | None = Field(default=None)
        test_request: str | None = Field(default=None)

    return TestTask(**kwargs)


# Test BaseTask initialization and basic properties
def test_base_task_init():
    task = create_base_task(assignment="Test assignment", task="Test task")
    assert task.assignment == "Test assignment"
    assert task.task == "Test task"
    assert task.input_fields == []
    assert task.request_fields == []


# Test setting attributes
def test_base_task_setattr():
    task = create_base_task()
    task.task = "New task"
    assert task.task == "New task"

    with pytest.raises(AttributeError) as exc_info:
        task.input_fields = ["new_field"]
    assert "Cannot directly assign to input/request fields" in str(exc_info.value)

    with pytest.raises(AttributeError) as exc_info:
        task.request_fields = ["new_field"]
    assert "Cannot directly assign to input/request fields" in str(exc_info.value)


# Test completed property
def test_base_task_completed():
    task = create_base_task(request_fields=["test_request"])

    # Check initial state
    assert not task.completed
    assert task.test_request is None

    # Set the request field and check completed status
    task.test_request = "Filled"
    assert (
        task.completed
    ), f"Task not completed. test_request value: {task.test_request}"

    # Additional checks
    assert (
        task.check_is_completed(handle_how="return_missing") is None
    ), f"Missing fields: {task.check_is_completed(handle_how='return_missing')}"

    task = create_base_task(request_fields=["test_request"])
    # Test with None and LN_UNDEFINED
    task.test_request = None
    assert not task.completed, "Task should not be completed when field is None"

    task.test_request = LN_UNDEFINED
    assert not task.completed, "Task should not be completed when field is LN_UNDEFINED"


# Test workable property
def test_base_task_workable():
    task = create_base_task(input_fields=["test_input"])
    assert not task.workable
    task.test_input = "Provided"
    assert task.workable


# Test work_fields property
def test_base_task_work_fields():
    task = create_base_task(
        input_fields=["test_input"],
        request_fields=["test_request"],
        test_input="Input",
        test_request="Request",
    )
    assert task.work_fields == {"test_input": "Input", "test_request": "Request"}


# Test check_is_completed method
def test_base_task_check_is_completed():
    task = create_base_task(request_fields=["test_request"])

    with pytest.raises(ValueError):
        task.check_is_completed()

    assert task.check_is_completed(handle_how="return_missing") == ["test_request"]

    task.test_request = "Filled"
    task.check_is_completed()
    assert task.has_processed


# Test check_is_workable method
def test_base_task_check_is_workable():
    task = create_base_task(input_fields=["test_input"])

    with pytest.raises(ValueError):
        task.check_is_workable()

    assert task.check_is_workable(handle_how="return_missing") == ["test_input"]

    task.test_input = "Provided"
    task.check_is_workable()


# Test instruction_dict property
def test_base_task_instruction_dict():
    task = create_base_task(
        task="Test task", request_fields=["test_request"], test_request="Request value"
    )
    instruction_dict = task.instruction_dict
    assert "context" in instruction_dict
    assert "instruction" in instruction_dict
    assert "requested_fields" in instruction_dict


# Test none_as_valid_value
def test_base_task_none_as_valid_value():
    task = create_base_task(
        input_fields=["test_input"],
        request_fields=["test_request"],
        none_as_valid_value=True,
    )
    task.test_input = None
    task.test_request = None
    assert task.workable
    assert task.completed


# Test with LN_UNDEFINED
def test_base_task_ln_undefined():
    task = create_base_task(
        input_fields=["test_input"],
        request_fields=["test_request"],
    )
    task.test_input = LN_UNDEFINED
    task.test_request = LN_UNDEFINED

    assert not task.workable
    assert not task.completed


# Test multiple input and request fields
def test_base_task_multiple_fields():
    class MultiFieldTask(BaseTask):
        input1: str | None = Field(default=None)
        input2: str | None = Field(default=None)
        request1: str | None = Field(default=None)
        request2: str | None = Field(default=None)

    task = MultiFieldTask(
        input_fields=["input1", "input2"], request_fields=["request1", "request2"]
    )
    assert not task.workable
    assert not task.completed

    task.input1 = "Value1"
    task.input2 = "Value2"
    assert task.workable
    assert not task.completed

    task.request1 = "Result1"
    task.request2 = "Result2"
    assert task.workable
    assert task.completed


# Test task description
def test_base_task_description():
    task = create_base_task(task_description="This is a test task")
    assert task.task_description == "This is a test task"


# Test has_processed flag
def test_base_task_has_processed():
    task = create_base_task(request_fields=["test_request"])
    assert not task.has_processed
    task.test_request = "Filled"
    task.check_is_completed()
    assert task.has_processed

    with pytest.raises(ValueError):
        task.check_is_workable()


# Test instruction_context property
def test_base_task_instruction_context():
    task = create_base_task(request_fields=["test_request"], test_request="Test value")
    context = task.instruction_context
    assert "test_request" in context
    assert "Test value" in context


# Test instruction_prompt property
def test_base_task_instruction_prompt():
    task = create_base_task(task="Test task", request_fields=["test_request"])
    prompt = task.instruction_prompt
    assert "Test task" in prompt
    assert "test_request" in prompt


# Test instruction_requested_fields property
def test_base_task_instruction_requested_fields():
    task = create_base_task(request_fields=["test_request"])
    requested_fields = task.instruction_requested_fields
    assert "test_request" in requested_fields


# Test empty input and request fields
def test_base_task_empty_fields():
    task = create_base_task()
    assert task.workable
    assert task.completed


# Test with all fields filled
def test_base_task_all_fields_filled():
    task = create_base_task(
        assignment="Test assignment",
        task="Test task",
        task_description="Test description",
        input_fields=["test_input"],
        request_fields=["test_request"],
        test_input="Input value",
        test_request="Request value",
    )
    assert task.workable
    assert task.completed
    assert task.assignment == "Test assignment"
    assert task.task == "Test task"
    assert task.task_description == "Test description"
    assert task.work_fields == {
        "test_input": "Input value",
        "test_request": "Request value",
    }
