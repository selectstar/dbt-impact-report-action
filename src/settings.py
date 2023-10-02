
import logging
import os

from enum import Enum
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class AppSettings(Enum):

    def __new__(
        cls,
        value: str,
        required: bool = True,
        printable: bool = False
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.required = required
        obj.printable = printable
        return obj

    SELECTSTAR_API_URL = ("SELECTSTAR_API_URL", True, True)
    SELECTSTAR_WEB_URL = ("SELECTSTAR_WEB_URL", True, True)
    SELECTSTAR_API_TOKEN = ("SELECTSTAR_API_TOKEN", True, False)
    SELECTSTAR_DATASOURCE_GUID = ("SELECTSTAR_DATASOURCE_GUID", True, True)
    GIT_PROVIDER = ("GIT_PROVIDER", True, True)
    GIT_REPOSITORY = ("GIT_REPOSITORY", True, True)
    GIT_REPOSITORY_TOKEN = ("GIT_REPOSITORY_TOKEN", True, False)
    PULL_REQUEST_ID = ("PULL_REQUEST_ID", True, True)


class SettingsManager:

    def __init__(self):
        self.settings: dict[AppSettings: str] = {}

    @staticmethod
    def __get_setting(setting: AppSettings):
        a_setting = os.environ.get(setting.value) or os.environ.get(f'INPUT_{setting.value}')
        if setting.required and not a_setting:
            raise KeyError(f"Required env var not found: {setting.name}")
        return a_setting

    def get_settings(self):
        if not self.settings:
            load_dotenv()
            self.settings = {setting: self.__get_setting(setting) for setting in AppSettings}
        return self.settings

    def print(self):
        if not self.settings:
            log.error("You need to load the settings before trying to print them.")

        log.info("These are the current values of the required settings")
        for k, v in self.settings.items():
            v_val = v if k.printable else '**HIDDEN**'
            log.info(f"   {k.name} = '{v_val}'")
