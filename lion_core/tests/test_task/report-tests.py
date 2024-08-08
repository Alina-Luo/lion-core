import pytest
from pydantic import Field
from typing import Type

from lion_core.exceptions import LionValueError
from lion_core.setting import LN_UNDEFINED
from lion_core.generic.form import Form
from lion_core.generic.pile import Pile
from lion_core.task.base import BaseTask
from lion_core.task.static_task import StaticTask
from lion_core.task.report import Report


# Helper function to create a sample Form
class SampleForm(Form):
    template_name: str = "sample_form"
    field1: str | None = Field(default=None)
    field2: int | None = Field(default=None)


# Test Report initialization
def test_report_init():
    report = Report()
    assert report.template_name == "default_report"
    assert isinstance(report.completed_tasks, Pile)
    assert report.completed_task_assignments == {}


# Test final_output property
def test_report_final_output():
    report = Report(final_output_fields=["field1", "field2"])
    report.add_field("field1", field_obj=Field(default=""))
    report.add_field("field2", field_obj=Field(default=0))
    report.field1 = "test"
    report.field2 = 42

    assert report.final_output == {"field1": "test", "field2": 42}

    # Test with non-existent field
    report.final_output_fields.append("non_existent")
    with pytest.raises(ValueError):
        _ = report.final_output


# Test work_fields property
def test_report_work_fields():
    report = Report()
    report.add_field("custom_field", field_obj=Field(default=""))
    report.custom_field = "test"

    assert "custom_field" in report.work_fields
    assert "template_name" not in report.work_fields


# Test get_incomplete_fields method
def test_report_get_incomplete_fields():
    report = Report()
    report.add_field("field1", field_obj=Field(default=None))
    report.add_field("field2", field_obj=Field(default=None))
    report.field1 = "test"

    assert "field2" in report.get_incomplete_fields()
    assert "field1" not in report.get_incomplete_fields()

    # Test with none_as_valid_value
    report.field2 = None
    assert "field2" not in report.get_incomplete_fields(none_as_valid_value=True)


# Test parse_assignment method
def test_report_parse_assignment():
    report = Report()
    report.add_field("field1", field_obj=Field(default=None))
    report.add_field("field2", field_obj=Field(default=None))

    assignment = report.parse_assignment(["field1"], ["field2"])
    assert assignment == "field1 -> field2"

    with pytest.raises(ValueError):
        report.parse_assignment(["non_existent"], ["field2"])


# Test create_task method
def test_report_create_task():
    report = Report()
    report.add_field("field1", field_obj=Field(default=None))
    report.add_field("field2", field_obj=Field(default=None))

    task = report.create_task(input_fields=["field1"], request_fields=["field2"])
    assert isinstance(task, StaticTask)
    assert task.assignment == "field1 -> field2"

    with pytest.raises(ValueError):
        report.create_task()  # No parameters provided

    with pytest.raises(ValueError):
        report.create_task(
            assignment="test", input_fields=["field1"]
        )  # Both assignment and fields provided


# Test save_completed_task method
def test_report_save_completed_task():
    report = Report()
    report.add_field("field1", field_obj=Field(default=None))
    report.add_field("field2", field_obj=Field(default=None))

    task = report.create_task(input_fields=["field1"], request_fields=["field2"])
    task.field2 = 42

    report.save_completed_task(task, update_results=True)
    assert len(report.completed_tasks) == 1
    assert report.field2 == 42

    # Test with incomplete task
    incomplete_task = report.create_task(
        input_fields=["field1"], request_fields=["field2"]
    )
    with pytest.raises(ValueError):
        report.save_completed_task(incomplete_task)


# Test from_form_template class method
def test_report_from_form_template():
    report = Report.from_form_template(SampleForm)
    assert report.template_name == "report_for_sample_form"
    assert "field1" in report.all_fields
    assert "field2" in report.all_fields

    with pytest.raises(LionValueError):
        Report.from_form_template(str)  # Invalid template class


# Test from_form class method
def test_report_from_form():
    sample_form = SampleForm(field1="test", field2=42)
    report = Report.from_form(sample_form)

    assert report.template_name == "report_for_sample_form"
    assert report.field1 == "test"
    assert report.field2 == 42

    with pytest.raises(LionValueError):
        Report.from_form("not a form")  # Invalid form instance


# Test edge cases
def test_report_edge_cases():
    report = Report()

    # Test with LN_UNDEFINED
    report.add_field("field1", field_obj=Field(default=LN_UNDEFINED))
    assert "field1" in report.get_incomplete_fields()

    # Test with empty lists
    assert report.parse_assignment([], []) == " -> "
