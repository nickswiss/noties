import time

from typing import List, Optional, Mapping, Dict

from pydantic import BaseModel

DEFAULT_VANITY_URL = "n/a"


def dynamodb_timestamp_factory():
    return int(time.time())


class Email(BaseModel):
    from_address: str
    from_address_full: str
    subject_line: str


class EmailHistory(BaseModel):
    email: str = "Anonymous"
    emails: List[Email] = []
    watch_expiration: int = 0
    notify_from_addresses: List[str] = []
