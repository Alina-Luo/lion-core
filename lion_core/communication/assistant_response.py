from typing import Any
from lion_core.sys_util import SysUtil
from .message import RoledMessage, MessageRole


class AssistantResponse(RoledMessage):

    def __init__(
        self,
        assistant_response: dict,
        sender: str,
        recipient: str,
        **kwargs: Any,
    ):
        """
        Initializes the AssistantResponse.

        Args:
            assistant_response: The content of the assistant's response.
            sender: The sender of the response.
            recipient: The recipient of the response.
            **kwargs: Additional keyword arguments for the parent class.
        """
        super().__init__(
            role=MessageRole.ASSISTANT,
            sender=sender or "N/A",
            content={"assistant_response": assistant_response.get("content", "")},
            recipient=recipient,
            **kwargs,
        )

    def clone(self, **kwargs: Any) -> "AssistantResponse":
        """
        Creates a copy of the current AssistantResponse object.

        This method clones the current object, preserving its content.
        It also retains the original metadata, while allowing
        for the addition of new attributes through keyword arguments.

        Args:
            **kwargs: Optional keyword arguments for the cloned object.

        Returns:
            A new instance with the same content and additional kwargs.
        """
        content = {"content": SysUtil.copy(self.content["assistant_response"])}
        response_copy = AssistantResponse(assistant_response=content, **kwargs)
        response_copy.metadata.set("origin_ln_id", self.ln_id)
        return response_copy

    @property
    def chat_msg(self) -> dict | None:
        """Return message in chat representation."""
        try:
            return self._check_chat_msg()
        except:
            return None

    def _check_chat_msg(self) -> dict:
        """Check and return the chat message."""
        text_msg = super()._check_chat_msg()
        return text_msg

    @property
    def response(self) -> Any:
        """Return the assistant response content."""
        return self.content.get("assistant_response", None)


# File: lion_core/communication/assistant_response.py
