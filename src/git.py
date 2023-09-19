
import re
import requests

from enum import Enum
from string import Template

from exceptions import APIException


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

    def build_pull_request_files_url(self, repository: str, remote_id: str):
        return self.pull_request_link_template.substitute(
            {
                "host": self.host,
                "repository": repository,
                "remote_id": remote_id,
            }
        )

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


class Git:

    def __init__(self, token: str):
        self.token = token

    def get_changed_files(self, git_provider: GitProvider, repository: str, pull_request_id: str):
        url = git_provider.build_pull_request_files_url(repository=repository, remote_id=pull_request_id)

        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {git_provider.host}. Code {response.status_code}."
                               f" Message {response.content}")

        files = response.json()

        found_files = []

        for file in files:
            result = re.match(r"models/(\w)+/(\w+)+.sql", file.get("filename"), flags=re.IGNORECASE)
            if result:
                filename = file.get("filename").split("/")[-1]
                found_files.append((filename, file.get("status")))

        return found_files
