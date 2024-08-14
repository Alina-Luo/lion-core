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

from typing import Any, Union

from lion_core.abc import BaseExecutor, Temporal, Observable
from lion_core.sys_utils import SysUtil

from lion_core.form.form import Form
from lion_core.imodel.imodel import iModel
from lion_core.rule.base import Rule
from lion_core.rule.default_rules._default import DEFAULT_RULES, DEFAULT_RULEORDER
from lion_core.rule.rulebook import RuleBook


class RuleProcessor(BaseExecutor, Temporal, Observable):

    def __init__(
        self,
        *,
        rulebook: RuleBook = None,
        fallback_structure_imodel: iModel = None,
        strict: bool = True,
    ):

        self.ln_id: str = SysUtil.id()
        self.timestamp: str = SysUtil.time(type_="timestamp")
        self.rulebook = rulebook or RuleBook()
        self.logs = []
        self.fallback_structure_imodel = fallback_structure_imodel
        self.strict = strict

    def create_json_structure(self, *args, **kwargs): ...

    async def process_field(
        self,
        field: str,
        value: Any,
        form: Form,
        *args,
        annotation=None,
        strict=None,
        use_annotation=True,
        **kwargs,
    ) -> Any:
        """
        Validate a specific field in a form.

        Args:
            field (str): The field to validate.
            value (Any): The value of the field.
            form (Form): The form containing the field.
            *args: Additional arguments.
            annotation (list[str], optional): Annotations for the field.
            strict (bool): Whether to enforce strict validation.
            use_annotation (bool): Whether to use annotations for validation.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The validated value.

        Raises:
            LionFieldError: If validation fails.
        """
        strict = strict if isinstance(strict, bool) else self.strict
        for rule in self.active_rules.values():
            try:
                if await rule.apply(
                    field,
                    value,
                    form,
                    *args,
                    annotation=annotation,
                    use_annotation=use_annotation,
                    **kwargs,
                ):
                    return await rule.invoke(field, value, form)
            except Exception as e:
                raise ValueError(f"Failed to validate {field}") from e

        if strict:
            error_message = (
                f"Failed to validate {field} because no rule applied. To return the "
                f"original value directly when no rule applies, set strict=False."
            )
            raise ValueError(error_message)

    async def process_response(
        self,
        form: Form,
        response: Union[dict, str],
        strict: bool = True,
        use_annotation: bool = True,
        fallback_structure_imodel: iModel = None,
    ) -> Form:
        """
        Validate a response for a given form.

        Args:
            form (Form): The form to validate against.
            response (dict | str): The response to validate.
            strict (bool): Whether to enforce strict validation.
            use_annotation (bool): Whether to use annotations for validation.

        Returns:
            Form: The validated form.

        Raises:
            ValueError: If the response format is invalid.
        """
        if isinstance(response, str):
            if len(form.request_fields) == 1:
                response = {form.request_fields[0]: response}
            else:
                try:
                    response = await fallback_structure_imodel.structure(response)
                except Exception as e:
                    raise ValueError(
                        "Response is a string, but form has multiple fields to be filled"
                    ) from e

        dict_ = {}
        for k, v in response.items():
            if k in form.request_fields:
                kwargs = form.validation_kwargs.get(k, {})
                _annotation = form._field_annotations[k]
                if (keys := form._get_field_attr(k, "choices", None)) is not None:
                    v = await self.process_field(
                        field=k,
                        value=v,
                        form=form,
                        annotation=_annotation,
                        strict=strict,
                        keys=keys,
                        use_annotation=use_annotation,
                        **kwargs,
                    )

                elif (_keys := form._get_field_attr(k, "keys", None)) is not None:

                    v = await self.process_field(
                        field=k,
                        value=v,
                        form=form,
                        annotation=_annotation,
                        strict=strict,
                        keys=_keys,
                        use_annotation=use_annotation,
                        **kwargs,
                    )

                else:
                    v = await self.process_field(
                        field=k,
                        value=v,
                        form=form,
                        annotation=_annotation,
                        strict=strict,
                        use_annotation=use_annotation,
                        **kwargs,
                    )
            dict_[k] = v
        form.fill(**dict_)
        return form
