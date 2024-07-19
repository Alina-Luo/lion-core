from datetime import timezone


class LionUndefined:

    def __init__(self):
        self.undefined = True

    def __bool__(self):
        return False

    __slots__ = ["undefined"]


LN_UNDEFINED = LionUndefined()
UNDEFINED = [None, LN_UNDEFINED]


LION_ID_CONFIG = {
    "n": 28,
    "random_hyphen": True,
    "num_hyphens": 4,
    "hyphen_start_index": 6,
    "hyphen_end_index": 24,
    "prefix": "ln",
}


BASE_LION_FIELDS = [
    "ln_id",
    "timestamp",
    "metadata",
    "extra_fields",
    "content",
    "created",
    "embedding",
]

TIME_CONFIG = {
    "tz": timezone.utc,
}


SERILIATION_CONFIG = {
    "mode": "python",
    "include": None,
    "exclude": None,
    "context": None,
    "by_alias": False,
    "exclude_unset": False,
    "exclude_defaults": False,
    "exclude_none": False,
    "round_trip": False,
    "warnings": True,  #  bool | Literal['none', 'warn', 'error']
    "serialize_as_any": False,
}


# File: lion_core/setting.py
