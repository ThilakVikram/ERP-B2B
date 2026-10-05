from enum import Enum


class SyncMode(str, Enum):
    """How a platform sync picks the integration rows it copies from. Neither mode deletes anything.

    normal: only rows not linked yet (their link to the app record is null).
    full: every row; refreshes the fields and links of records already created too.
    """

    NORMAL = "normal"
    FULL = "full"
