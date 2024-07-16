"""Message module for the Lion framework's communication system."""

from enum import Enum
from typing import Any, Dict, List
from pydantic import Field
from lion_core.sys_util import SysUtil
from lion_core.generic import Component
from .mail import BaseMail


class MessageField(str, Enum):
    """Enum to store message fields for consistent referencing."""

    LION_ID = "lion_id"
    TIMESTAMP = "timestamp"
    ROLE = "role"
    SENDER = "sender"
    RECIPIENT = "recipient"
    CONTENT = "content"


class MessageRole(str, Enum):
    """Enum for possible roles a message can assume in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class RoledMessage(Component, BaseMail):
    """A base class representing a message with validators and properties."""

    role: MessageRole | None = Field(
        default=None,
        description="The role of the message in the conversation.",
        examples=["system", "user", "assistant"],
    )

    @property
    def image_content(self) -> List[Dict[str, Any]] | None:
        """Return image content if present in the message."""
        msg_ = self.chat_msg
        if isinstance(msg_, dict) and isinstance(msg_["content"], list):
            return [i for i in msg_["content"] if i["type"] == "image_url"]
        return None

    @property
    def chat_msg(self) -> Dict[str, Any] | None:
        """Return message in chat representation."""
        try:
            return self._check_chat_msg()
        except:
            return None

    def _check_chat_msg(self) -> Dict[str, Any]:
        """Validate and format the message for chat representation."""
        if self.role is None:
            raise ValueError("Message role not set")

        role = self.role.value if isinstance(self.role, Enum) else self.role
        if role not in [i.value for i in MessageRole]:
            raise ValueError(f"Invalid message role: {role}")

        content_dict = SysUtil.copy(self.content)

        if not content_dict.get("images", None):
            if len(content_dict) == 1:
                content_dict = str(list(content_dict.values())[0])
            else:
                content_dict = str(content_dict)

        return {"role": role, "content": content_dict}

    def __str__(self) -> str:
        """Provide a string representation of the message with content preview."""
        content_preview = (
            f"{str(self.content)[:75]}..."
            if len(str(self.content)) > 75
            else str(self.content)
        )
        return (
            f"Message(role={self.role}, sender={self.sender}, "
            f"content='{content_preview}')"
        )


# File: lion_core/communication/message.py
