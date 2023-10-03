
import json
import logging
import os

from enum import Enum
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class AppSettings(Enum):

    def __new__(
        cls,
        value: str,
        printable: bool = False
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.printable = printable
        return obj

    SELECTSTAR_API_URL = ("SELECTSTAR_API_URL", True)
    SELECTSTAR_WEB_URL = ("SELECTSTAR_WEB_URL", True)
    SELECTSTAR_API_TOKEN = ("SELECTSTAR_API_TOKEN", False)
    SELECTSTAR_DATASOURCE_GUID = ("SELECTSTAR_DATASOURCE_GUID", True)
    GIT_PROVIDER = ("GIT_PROVIDER", True)
    GIT_CI = ("GIT_CI", True)
    GIT_REPOSITORY = ("GIT_REPOSITORY", True)
    GIT_REPOSITORY_TOKEN = ("GIT_REPOSITORY_TOKEN", False)
    PULL_REQUEST_ID = ("PULL_REQUEST_ID", True)


class SettingsManager:

    def __init__(self):
        self.settings: dict[AppSettings: str] = {}

    def get_settings(self):
        if not self.settings:
            load_dotenv()

            self.settings = {setting: self.__get_setting_from_environ(setting) for setting in AppSettings}

            self.settings[AppSettings.GIT_CI] = self.settings.get(AppSettings.GIT_CI) not in ["false", "False"]

            if self.settings.get(AppSettings.GIT_CI):
                if self.settings[AppSettings.GIT_PROVIDER] == 'github':
                    self.settings = self.settings | self.__get_settings_from_github()
                else:
                    raise KeyError(f"Unknown git provider: {self.settings[AppSettings.GIT_PROVIDER]}")

            self.__validate_settings()

        return self.settings

    @staticmethod
    def __get_setting_from_environ(setting: AppSettings):
        return os.environ.get(setting.value) or os.environ.get(f'INPUT_{setting.value}')

    @staticmethod
    def __get_settings_from_github() -> dict[AppSettings: str]:
        log.info("Loading GitHub vars")
        git_settings = {}
        try:
            env_filepath = os.environ["GITHUB_EVENT_PATH"]
            with open(env_filepath) as env_file:
                git_env = json.load(env_file)
                git_settings[AppSettings.GIT_REPOSITORY] = git_env["repository"]["full_name"]
                git_settings[AppSettings.PULL_REQUEST_ID] = git_env["number"]
            return git_settings
        except Exception as exc:
            raise Exception(exc, 'Are you sure this is running inside GitHub workflow? Env var GIT_CI is set as True')

    def __validate_settings(self):
        for setting in AppSettings:
            if self.settings.get(setting) is None:
                raise KeyError(f"Required env var not found: {setting.name}")

    def print(self):
        if not self.settings:
            log.error("You need to load the settings before trying to print them.")

        log.info("These are the current values of the required settings")
        for k, v in self.settings.items():
            v_val = v if k.printable else '**HIDDEN**'
            log.info(f"   {k.name} = '{v_val}'")
