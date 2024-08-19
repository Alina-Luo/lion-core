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

from typing import Any
from typing_extensions import override

from lion_core.communication.message import (
    RoledMessage,
    MessageRole,
    MessageFlag,
)


class AssistantResponse(RoledMessage):
    """
    Represents a response from an assistant in the system.

    The `AssistantResponse` class encapsulates a response generated by an assistant,
    including the content of the response and information about the sender and recipient.

    Attributes:
        assistant_response (dict | MessageFlag): The content of the assistant's response, either as a dictionary or a MessageFlag.
        sender (Any | MessageFlag): The sender of the response, typically the assistant itself.
        recipient (Any | MessageFlag): The recipient of the response.
        protected_init_params (dict | None): Optional parameters for protected initialization.
    """

    @override
    def __init__(
        self,
        assistant_response: dict | MessageFlag,
        sender: Any | MessageFlag,
        recipient: Any | MessageFlag,
        protected_init_params: dict | None = None,
    ):
        """
        Initializes an AssistantResponse instance.

        Args:
            assistant_response (dict | MessageFlag): The content of the assistant's response.
            sender (Any | MessageFlag): The sender of the response, typically the assistant.
            recipient (Any | MessageFlag): The recipient of the response.
            protected_init_params (dict | None, optional): Optional parameters for protected initialization.
        """
        message_flags = [assistant_response, sender, recipient]

        if all(x == MessageFlag.MESSAGE_LOAD for x in message_flags):
            super().__init__(**protected_init_params)
            return

        if all(x == MessageFlag.MESSAGE_CLONE for x in message_flags):
            super().__init__(role=MessageRole.ASSISTANT)
            return

        super().__init__(
            role=MessageRole.ASSISTANT,
            sender=sender or "N/A",
            recipient=recipient,
        )
        if assistant_response:
            if isinstance(assistant_response, str):
                assistant_response = {"content": assistant_response}
            elif isinstance(assistant_response, dict):
                if not "content" in assistant_response:
                    a_ = {}
                    a_["content"] = assistant_response
                    assistant_response = a_
        else:
            assistant_response = {"content": ""}

        self.content["assistant_response"] = assistant_response.get("content", "")

    @property
    def response(self) -> Any:
        """
        Returns the assistant response content.

        This property retrieves the content of the assistant's response stored in the message.

        Returns:
            Any: The content of the assistant's response.
        """
        return self.content.get("assistant_response")


# File: lion_core/communication/assistant_response.py
