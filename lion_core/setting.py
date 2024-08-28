from datetime import timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self


class LionUndefinedType(str):
    def __init__(self) -> None:
        self.undefined = True

    def __bool__(self) -> Literal[False]:
        return False

    def __deepcopy__(self, memo) -> Self:
        # Ensure LN_UNDEFINED is universal
        return self

    def __repr__(self) -> Literal["LN_UNDEFINED"]:
        return "LN_UNDEFINED"

    __slots__ = ["undefined"]


LN_UNDEFINED = LionUndefinedType()


class SchemaModel(BaseModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    schema_version: int | float | str | None = Field(
        default=None, exclude=True
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)

    @classmethod
    def from_dict(cls, **data) -> Self:
        return cls(**data)

    @classmethod
    def schema_keys(cls) -> set:
        return set(cls.model_fields.keys())


class LionIDConfig(SchemaModel):
    n: int
    random_hyphen: bool
    num_hyphens: int
    hyphen_start_index: int
    hyphen_end_index: int
    prefix: str = "ln"
    postfix: str = ""


class TimedFuncCallConfig(SchemaModel):
    initial_delay: int = 0
    retry_default: str | LionUndefinedType = LN_UNDEFINED
    retry_timeout: int | None = None
    retry_timing: bool = False
    error_msg: str | None = None
    error_map: dict | None = None


class RetryConfig(SchemaModel):
    num_retries: int = 0
    initial_delay: int = 0
    retry_delay: int = 0
    backoff_factor: int = 1
    retry_default: str | LionUndefinedType = LN_UNDEFINED
    retry_timeout: int | None = None
    retry_timing: bool = False
    verbose_retry: bool = False
    error_msg: str | None = None
    error_map: dict | None = None


class BaseLionFields(str, Enum):
    LN_ID = "ln_id"
    TIMESTAMP = "timestamp"
    METADATA = "metadata"
    EXTRA_FIELDS = "extra_fields"
    CONTENT = "content"
    CREATED = "created"
    EMBEDDING = "embedding"


class PydanticSerializationConfig(SchemaModel):
    mode: str = "python"
    include: set | None = None
    exclude: set | None = None
    context: dict | None = None
    by_alias: bool = False
    exclude_unset: bool = False
    exclude_defaults: bool = False
    exclude_none: bool = False
    round_trip: bool = False
    warnings: bool = True
    serialize_as_any: bool = False


DEFAULT_LION_ID_CONFIG = LionIDConfig(
    n=42,
    random_hyphen=True,
    num_hyphens=4,
    hyphen_start_index=6,
    hyphen_end_index=-6,
    prefix="ln",
    postfix="",
)

DEFAULT_TIMED_FUNC_CALL_CONFIG = TimedFuncCallConfig(
    initial_delay=0,
    retry_default=LN_UNDEFINED,
    retry_timeout=None,
    retry_timing=False,
    error_msg=None,
    error_map=None,
)

DEFAULT_RETRY_CONFIG = RetryConfig(
    num_retries=0,
    initial_delay=0,
    retry_delay=0,
    backoff_factor=1,
    retry_default=LN_UNDEFINED,
    retry_timeout=None,
    retry_timing=False,
    verbose_retry=False,
    error_msg=None,
    error_map=None,
)


DEFAULT_TIMEZONE = timezone.utc
BASE_LION_FIELDS = set(BaseLionFields.__members__.values())

# File: lion_core/setting.py
