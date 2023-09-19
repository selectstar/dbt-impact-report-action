
import os

from enum import Enum
from dotenv import load_dotenv


class AppSettings(Enum):

    def __new__(
        cls,
        value: str,
        required: str = True,
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.required = required
        return obj

    SELECTSTAR_API_URL = ("SELECTSTAR_API_URL", True)
    SELECTSTAR_API_TOKEN = ("SELECTSTAR_API_TOKEN", True)
    SELECTSTAR_DATASOURCE_GUID = ("SELECTSTAR_DATASOURCE_GUID", True)
    GIT_PROVIDER = ("GIT_PROVIDER", True)
    GIT_REPOSITORY = ("GIT_REPOSITORY", True)
    GIT_REPOSITORY_TOKEN = ("GIT_REPOSITORY_TOKEN", True)
    PULL_REQUEST_ID = ("PULL_REQUEST_ID", True)


def get_setting(setting: AppSettings):
    a_setting = os.environ.get(setting.value)
    if setting.required and not a_setting:
        raise KeyError(f"Required env var not found: {setting.name}")
    return a_setting


def get_settings():

    load_dotenv()

    settings = {setting: get_setting(setting) for setting in AppSettings}

    return settings
