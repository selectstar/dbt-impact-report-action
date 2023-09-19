
import os

from enum import Enum
from dotenv import load_dotenv


class AppSettings(Enum):
    SELECTSTAR_API_URL = "SELECTSTAR_API_URL"
    SELECTSTAR_API_TOKEN = "SELECTSTAR_API_TOKEN"
    SELECTSTAR_DATASOURCE_GUID = "SELECTSTAR_DATASOURCE_GUID"
    GIT_PROVIDER = "GIT_PROVIDER"
    GIT_REPOSITORY = "GIT_REPOSITORY"
    GIT_REPOSITORY_TOKEN = "GIT_REPOSITORY_TOKEN"
    PULL_REQUEST_ID = "PULL_REQUEST_ID"


def get_setting(setting: AppSettings, required: bool = True):
    a_setting = os.environ.get(setting.value)
    if required and not a_setting:
        raise KeyError(f"Required env var not found: {setting.name}")
    return a_setting


def get_settings():

    load_dotenv()

    settings = {
        AppSettings.SELECTSTAR_API_URL: get_setting(AppSettings.SELECTSTAR_API_URL),
        AppSettings.SELECTSTAR_API_TOKEN: get_setting(AppSettings.SELECTSTAR_API_TOKEN),
        AppSettings.SELECTSTAR_DATASOURCE_GUID: get_setting(AppSettings.SELECTSTAR_DATASOURCE_GUID),
        AppSettings.GIT_PROVIDER: get_setting(AppSettings.GIT_PROVIDER),
        AppSettings.GIT_REPOSITORY: get_setting(AppSettings.GIT_REPOSITORY),
        AppSettings.GIT_REPOSITORY_TOKEN: get_setting(AppSettings.GIT_REPOSITORY_TOKEN),
        AppSettings.PULL_REQUEST_ID: get_setting(AppSettings.PULL_REQUEST_ID),
    }

    return settings
