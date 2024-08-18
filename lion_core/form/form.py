"""
Copyright 2024 HaiyangLi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""Form class extending BaseTaskForm with additional functionality."""

import inspect

from typing import Any, Literal, Type
from typing_extensions import override

from pydantic import Field, model_validator
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from lion_core.generic.component import T
from lion_core.setting import LN_UNDEFINED
from lion_core.sys_utils import SysUtil
from lion_core.exceptions import LionValueError
from lion_core.generic.note import Note
from lion_core.form.base import BaseForm
from lion_core.form.utils import get_input_output_fields, ERR_MAP


class Form(BaseForm):
    """
    Base task form class extending BaseForm with task-specific functionality.

    Introduces concepts of input fields, request fields, and task-related
    attributes for a comprehensive task-based form framework.

    Key concepts:
    - input_fields: Fields needed to obtain the request fields.
    - request_fields: Fields to be filled by an intelligent process.
    - output_fields: Fields for presentation, may include all, some, or no
      request fields. Can be conditionally modified if not strict.
    """

    strict: bool = Field(
        default=False,
        description="If True, form fields and assignment are immutable.",
        frozen=True,
    )
    guidance: str | dict[str, Any] | None = Field(
        default=None,
        description="High-level task guidance, optimizable by AI.",
    )
    input_fields: list[str] = Field(
        default_factory=list,
        description="Fields required to obtain the requested fields.",
    )
    request_fields: list[str] = Field(
        default_factory=list,
        description="Fields to be filled by an intelligent process.",
    )
    task: Any = Field(
        default_factory=str,
        description="Work to be done, including custom instructions.",
    )
    task_description: str | None = Field(
        default_factory=str,
        description="Detailed description of the task",
    )
    init_input_kwargs: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def check_is_completed(
        self,
        handle_how: Literal["return_missing", "raise"] = "raise",
    ) -> list[str] | None:
        if self.strict and self.has_processed:
            return
        return super().check_is_completed(handle_how)

    @model_validator(mode="before")
    @classmethod
    def check_input_output_list_omitted(cls, data: Any) -> dict[str, Any]:
        """
        Validate the input data before model creation.

        Args:
            data: Input data for model creation.

        Returns:
            Validated and processed input data.

        Raises:
            ValueError: If input data is invalid.
        """

        if isinstance(data, Note):
            data = data.to_dict()

        if not isinstance(data, dict):
            raise ERR_MAP["type", "not_dict"](data)

        if not data.get("assignment", None):
            raise ERR_MAP["assignment", "no_assignment"]

        if "input_fields" in data:
            raise ERR_MAP["assignment", "explcit_input"]

        if "request_fields" in data:
            raise ERR_MAP["assignment", "explcit_request"]

        if "task" in data:
            raise ERR_MAP["assignment", "explicit_task"]

        input_fields, request_fields = get_input_output_fields(data.get("assignment"))

        if not input_fields or input_fields == [""]:
            raise ERR_MAP["assignment", "missing_input"]

        elif not request_fields or request_fields == [""]:
            raise ERR_MAP["assignment", "missing_request"]

        data["input_fields"] = input_fields
        data["request_fields"] = request_fields
        data["output_fields"] = data.get("output_fields", request_fields)
        data["init_input_kwargs"] = {}
        data["strict"] = data.get("strict", False)

        for in_ in data["input_fields"]:
            data["init_input_kwargs"][in_] = (
                data.pop(in_, LN_UNDEFINED)
                if in_ not in cls.model_fields
                else data.get(in_, LN_UNDEFINED)
            )

        return data

    @model_validator(mode="after")
    def check_input_output_fields(self) -> "Form":
        """
        Validate and process input and output fields after model creation.

        Returns:
            The validated Form instance.
        """
        for i in self.input_fields:
            if i in self.model_fields:
                self.init_input_kwargs[i] = getattr(self, i)
            else:
                self.add_field(
                    field_name=i, value=self.init_input_kwargs.get(i, LN_UNDEFINED)
                )

        for i in self.request_fields:
            if i not in self.all_fields:
                self.add_field(field_name=i)

        return self

    @override
    @property
    def work_fields(self) -> list[str]:
        """Return a list of all fields involved in the task."""
        return self.input_fields + self.request_fields

    @override
    @property
    def required_fields(self) -> list[str]:
        """Return a list of all unique required fields."""
        return list(set(self.input_fields + self.request_fields + self.output_fields))

    @property
    def validation_kwargs(self):
        return {
            i: self.field_getattr(i, "validation_kwargs", {}) for i in self.work_fields
        }

    @property
    def instruction_dict(self) -> dict[str, Any]:
        """Return a dictionary with task instruction information."""
        return {
            "context": self.instruction_context,
            "instruction": self.instruction_prompt,
            "request_fields": self.instruction_request_fields,
        }

    @property
    def instruction_context(self) -> str:
        """Generate a description of the form's input fields."""

        a = self.all_fields

        context = f"### Input Fields:\n"
        for idx, i in enumerate(self.input_fields):
            context += f"Input No.{idx+1}: {i}\n"
            if getattr(a[i], "description", None):
                context += f"  - description: {a[i].description}.\n"
            context += f"  - value: {getattr(self, i)}.\n"
        return context

    @property
    def instruction_prompt(self) -> str:
        """Generate a task instruction prompt for the form."""

        a = self.all_fields
        prompt = ""
        if "guidance" in a:
            prompt += f"### Overall Guidance:\n{getattr(self, "guidance")}.\n"

        prompt += "### Task Instructions:\n"
        prompt += f"1. Provided Input Fields: {', '.join(self.input_fields)}.\n"
        prompt += f"2. Requested Output Fields: {', '.join(self.request_fields)}.\n"
        prompt += f"3. Your task:\n{self.task}.\n"

        return prompt

    @property
    def instruction_request_fields(self) -> dict[str, str]:
        """Get descriptions of the form's requested fields."""

        a = self.all_fields

        context = f"### Output Fields:\n"
        for idx, i in enumerate(self.request_fields):
            context += f"Input No.{idx+1}: {i}\n"
            if getattr(a[i], "description", None):
                context += f"  - description: {a[i].description}.\n"
            if getattr(a[i], "examples", None):
                context += f"  - examples: {a[i].examples}.\n"

        return context

    @override
    def update_field(
        self,
        field_name: str,
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs: Any,
    ) -> None:
        """
        Update a field in the form.

        Extends the base update_field method to also update
        the init_input_kwargs dictionary.
        """
        super().update_field(
            field_name=field_name,
            value=value,
            annotation=annotation,
            field_obj=field_obj,
            **kwargs,
        )
        self._fill_init_input_kwargs(field_name)

    @override
    def __setattr__(self, field_name: str, value: Any) -> None:
        """
        Set an attribute of the form.

        Extends the base __setattr__ method to enforce strictness
        and update the init_input_kwargs dictionary.
        """
        if self.strict and field_name in {
            "assignment",
            "input_fields",
            "request_fields",
        }:
            raise ERR_MAP["assignment", "strict"](field_name)

        if field_name in {"input_fields", "request_fields"}:
            raise ERR_MAP["field", "modify_input_request_list"]

        if field_name in {"init_input_kwargs"}:
            raise ERR_MAP["field", "modify_restricted"](field_name)

        super().__setattr__(field_name, value)
        self._fill_init_input_kwargs(field_name)

    def _fill_init_input_kwargs(self, field_name):
        if field_name in self.input_fields:
            self.init_input_kwargs[field_name] = getattr(self, field_name)

    def check_is_workable(
        self,
        handle_how: Literal["raise", "return_missing"] = "raise",
    ) -> list[str] | None:
        """
        Check if all input fields are filled and the form is workable.

        Args:
            handle_how: How to handle missing inputs.

        Returns:
            List of missing inputs if handle_how is "return_missing",
            None otherwise.

        Raises:
            ValueError: If input fields are missing and handle_how is "raise".
        """
        if self.strict and self.has_processed:
            raise ERR_MAP["assignment", "strict_processed"]

        missing_inputs = []
        invalid_values = [LN_UNDEFINED, PydanticUndefined]
        if not self.none_as_valid_value:
            invalid_values.append(None)

        for i in self.input_fields:
            if getattr(self, i) in invalid_values:
                missing_inputs.append(i)

        if missing_inputs:
            if handle_how == "raise":
                raise ERR_MAP["assignment", "incomplete_input"](missing_inputs)
            elif handle_how == "return_missing":
                return missing_inputs

    def is_completed(self) -> bool:
        try:
            self.check_is_completed(handle_how="raise")
            return True
        except Exception:
            return False

    def is_workable(self) -> bool:
        try:
            self.check_is_workable(handle_how="raise")
            return True
        except Exception:
            return False

    def to_dict(self, *, valid_only=False):
        _dict = super().to_dict()
        if not valid_only:
            return _dict

        disallow_values = [LN_UNDEFINED, PydanticUndefined]
        if not self.none_as_valid_value:
            disallow_values.append(None)
        return {k: v for k, v in _dict.items() if v not in disallow_values}

    @override
    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> T:
        input_data = SysUtil.copy(data)

        input_data.pop("lion_class", None)
        input_data.pop("input_fields", None)
        input_data.pop("request_fields", None)
        task = input_data.pop("task", "")

        extra_fields = {}
        for k, v in list(input_data.items()):
            if k not in cls.model_fields:
                extra_fields[k] = input_data.pop(k)
        obj = cls.model_validate(input_data, **kwargs)
        obj.task = task
        for k, v in extra_fields.items():
            obj.update_field(field_name=k, value=v)

        metadata = SysUtil.copy(data.get("metadata", {}))
        last_updated = metadata.get("last_updated", None)
        if last_updated is not None:
            obj.metadata.set(["last_updated"], last_updated)
        else:
            obj.metadata.pop(["last_updated"], None)
        return obj

    def fill_input_fields(
        self,
        form: BaseForm | Any = None,
        **value_kwargs,
    ):
        if form is not None and not isinstance(form, BaseForm):
            raise ERR_MAP["type", "not_form_instance"](form)

        for i in self.input_fields:
            if self.none_as_valid_value:
                if getattr(self, i) is not LN_UNDEFINED:
                    continue
                value = value_kwargs.get(i, LN_UNDEFINED)
                if value is LN_UNDEFINED:
                    value = SysUtil.copy(getattr(form, i, LN_UNDEFINED))
                if value is not LN_UNDEFINED:
                    setattr(self, i, value)
            else:
                if getattr(self, i) in [LN_UNDEFINED, None]:
                    value = value_kwargs.get(i)
                    if value in [LN_UNDEFINED, None]:
                        value = SysUtil.copy(getattr(form, i, LN_UNDEFINED))
                    if value not in [LN_UNDEFINED, None]:
                        setattr(self, i, value)

    def fill_request_fields(
        self,
        form: BaseForm = None,
        **value_kwargs,
    ):
        if form is not None and not isinstance(form, BaseForm):
            raise ERR_MAP["type", "not_form_instance"](form)

        for i in self.request_fields:
            if self.none_as_valid_value:
                if getattr(self, i) is not LN_UNDEFINED:
                    continue
                value = value_kwargs.get(i, LN_UNDEFINED)
                if value is LN_UNDEFINED:
                    value = SysUtil.copy(getattr(form, i, LN_UNDEFINED))
                if value is not LN_UNDEFINED:
                    setattr(self, i, value)
            else:
                if getattr(self, i) in [LN_UNDEFINED, None]:
                    value = value_kwargs.get(i)
                    if value in [LN_UNDEFINED, None]:
                        value = SysUtil.copy(getattr(form, i, LN_UNDEFINED))
                    if value not in [LN_UNDEFINED, None]:
                        setattr(self, i, value)

    @classmethod
    def from_form(
        cls,
        form: BaseForm | Type[BaseForm],
        guidance: str | dict[str, Any] | None = None,
        assignment: str | None = None,
        strict: bool = False,
        task_description: str | None = None,
        fill_inputs: bool = True,
        none_as_valid_value: bool = False,
        output_fields: list[str] | None = None,
        same_form_output_fields: bool = False,
        **input_value_kwargs,
    ):
        if inspect.isclass(form):
            if not issubclass(form, BaseForm):
                raise ERR_MAP["type", "not_form_class"](form)
            form_fields = form.model_fields
        else:
            if not isinstance(form, BaseForm):
                raise ERR_MAP["type", "not_form_instance"](form)
            form_fields = form.all_fields

        if same_form_output_fields:
            if output_fields:
                raise LionValueError(
                    "Cannot provide output_fields and "
                    "same_form_output_fields at the same time."
                )
            output_fields = SysUtil.copy(form.output_fields)

        if not assignment:
            if not getattr(form, "assignment", None):
                raise ERR_MAP["assignment", "no_assignment"]
            assignment = form.assignment

        obj = cls(
            guidance=guidance or getattr(form, "guidance", None),
            assignment=assignment,
            task_description=task_description
            or getattr(
                form,
                "task_description",
                "",
            ),
            none_as_valid_value=none_as_valid_value
            or getattr(form, "none_as_valid_value", False),
            strict=strict or getattr(form, "strict", False),
            output_fields=output_fields,
        )

        for i in obj.work_fields:
            if i not in form_fields:
                raise ERR_MAP["assignment", "invalid_assignment"](i)
            obj.update_field(i, field_obj=form_fields[i])

        if fill_inputs:
            if inspect.isclass(form):
                obj.fill_input_fields(**input_value_kwargs)
            else:
                obj.fill_input_fields(form=form, **input_value_kwargs)

        return obj

    def remove_request_from_output(self):
        for i in self.request_fields:
            if i in self.output_fields:
                self.output_fields.remove(i)

    def _append_to_one(
        self,
        field_name: str,
        field_type: Literal["input", "output", "request"],
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs,
    ):
        if self.strict and field_type in {"input", "request"}:
            raise ERR_MAP["assignment", "strict"](field_type)

        config = {
            "field_name": field_name,
            "value": value,
            "annotation": annotation,
            "field_obj": field_obj,
            **kwargs,
        }

        match field_type:
            case "input":
                if field_name not in self.input_fields:
                    self.input_fields.append(field_name)
                if field_name not in self.assignment:
                    self.assignment = f"{field_name}, " + self.assignment

            case "request":
                if field_name not in self.request_fields:
                    self.request_fields.append(field_name)
                    config.pop("value")
                if field_name not in self.assignment:
                    self.assignment += f", {field_name}"

            case "output":
                if field_name not in self.output_fields:
                    self.output_fields.append(field_name)

            case _:
                raise LionValueError(f"Invalid field type {field_type}")

        if any([
            value is not LN_UNDEFINED,
            annotation is not LN_UNDEFINED,
            field_obj is not LN_UNDEFINED,
            bool(kwargs)
        ]) or field_name not in self.all_fields:
            self.update_field(**config)


    def append_to_input(
        self,
        field_name: str,
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs,
    ) -> None:
        try:
            self._append_to_one(
                field_name=field_name,
                field_type="input",
                value=value,
                annotation=annotation,
                field_obj=field_obj,
                **kwargs,
            )
        except Exception as e:
            raise ERR_MAP["field", "error"](
                f"Failed to append {field_name} to input fields."
            ) from e

    def append_to_output(
        self,
        field_name: str,
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs,
    ) -> None:

        try:
            self._append_to_one(
                field_name=field_name,
                field_type="output",
                value=value,
                annotation=annotation,
                field_obj=field_obj,
                **kwargs,
            )
        except Exception as e:
            raise ERR_MAP["field", "error"](
                f"Failed to append {field_name} to output fields."
            ) from e

    def append_to_request(
        self,
        field_name: str,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs,
    ) -> None:
        if "value" in kwargs:
            raise LionValueError("Cannot provide value to request fields.")
        try:
            self._append_to_one(
                field_name=field_name,
                field_type="request",
                annotation=annotation,
                field_obj=field_obj,
                **kwargs,
            )
        except Exception as e:
            raise ERR_MAP["field", "error"](
                f"Failed to append {field_name} to request fields."
            ) from e


__all__ = ["Form"]
