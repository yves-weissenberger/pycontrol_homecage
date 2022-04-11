from dataclasses import dataclass
from datetime import datetime
from enum import Enum


""" This modules provides classes to pass messages from data processors to
    the recipient log windows which then print them
"""


class MessageRecipient(Enum):
    system_overview_log: 1
    calibrate_dialog: 2


@dataclass
class message:

    text: str
    time: datetime
    time_str: str
    recipient: MessageRecipient
