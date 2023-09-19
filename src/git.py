
import re
import requests

from enum import Enum
from string import Template

from exceptions import APIException
from settings import AppSettings, get_settings


class GitProvider(Enum):
    """
    Source Code Management Providers
    """

    def __new__(
        cls,
        value: str,
        host: str,
        pull_request_files_link_template: str,
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.host = host
        obj.pull_request_link_template = Template(pull_request_files_link_template)
        return obj

    GitHub = (
        "github",
        "api.github.com",
        "https://$host/repos/$repository/pulls/$remote_id/files",
    )
    BitBucket = (
        "bitbucket",
        "bitbucket.org",
        "https://$host/$repository/pull-requests/$remote_id",
    )

    def build_pull_request_files_url(self, repository: str, remote_id: str):
        return self.pull_request_link_template.substitute(
            {
                "host": self.host,
                "repository": repository,
                "remote_id": remote_id,
            }
        )

    def get_git_integration(self, settings: dict):
        return Git(git_provider=self, settings=settings)


class Git:

    def __init__(self, git_provider: GitProvider, settings: dict):
        self.settings = settings
        self.git_provider = git_provider
        self.token = get_settings().get(AppSettings.GIT_REPOSITORY_TOKEN)

    def get_changed_files(self, ):
        repository = self.settings.get(AppSettings.GIT_REPOSITORY)
        pull_request_id = self.settings.get(AppSettings.PULL_REQUEST_ID)

        url = self.git_provider.build_pull_request_files_url(repository=repository, remote_id=pull_request_id)

        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {self.git_provider.host}. Code {response.status_code}."
                               f" Message {response.content}")

        files = response.json()

        found_files = []

        for file in files:
            result = re.match(r"models/(\w)+/(\w+)+.sql", file.get("filename"), flags=re.IGNORECASE)
            if result:
                filename = file.get("filename").split("/")[-1]
                found_files.append((filename, file.get("status")))

        return found_files
