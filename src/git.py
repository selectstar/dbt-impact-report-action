import logging
import re
from enum import Enum

import requests

from dataobjects import DbtModel
from exceptions import APIException
from settings import AppSettings

log = logging.getLogger(__name__)


class Git:

    comment_anchor = "<!-- ImpactReportIdentifier: select-star-dbt-impact-report -->"

    def __init__(self, settings: dict):
        self.settings = settings
        self.repository = self.settings.get(AppSettings.GIT_REPOSITORY)
        self.pull_request_id = self.settings.get(AppSettings.PULL_REQUEST_ID)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {settings.get(AppSettings.GIT_REPOSITORY_TOKEN)}",
                "User-Agent": "Select Star Dbt Impact Report",
            }
        )
        self.user: dict = (
            self.__get_authenticated_user()
            if not self.settings.get(AppSettings.GIT_CI)
            else None
        )

    def get_changed_files(self):
        """
        Gets a list of changed models based on the list of changed files of the informed pull request
        :return: changed models
        """
        url = self._get_change_files_url()

        response = self.session.get(url)

        if response.status_code != 200:
            raise APIException(response=response)

        files = response.json()

        if len(files) == 100:
            log.warning("Processing only the first 100 files on this pull request.")

        found_models = []

        for file in files:
            result = re.match(
                r"models/(\w)+/(\w+)+.sql", file.get("filename"), flags=re.IGNORECASE
            )
            if result:
                found_models.append(DbtModel(file))

        log.info(f"Found models: {[(f.filename, f.status) for f in found_models]}")

        return found_models

    def __get_impact_report_comment_id(self) -> dict | None:
        url = self._get_list_comments_url()

        response = self.session.get(url)

        if response.status_code != 200:
            raise APIException(response=response)

        comments = response.json()

        for comment in comments:
            if self.settings.get(AppSettings.GIT_CI):
                if comment["user"]["login"] == "github-actions[bot]":
                    return comment
            else:
                if comment["user"]["login"] == self.user["login"]:
                    return comment

    def __insert_impact_report(self, body: str) -> dict:
        url = self._get_list_comments_url()

        body = f"{self.comment_anchor}\n{body}"

        response = self.session.post(url, json={"body": body})

        return response.json()

    def __update_impact_report(self, comment_id: str, body: str):
        url = self._get_detail_comments_url(commend_id=comment_id)

        body = f"{self.comment_anchor}\n{body}"

        response = self.session.patch(url, json={"body": body})

        return response.json()

    def insert_or_update_impact_report(self, body) -> None:
        """
        Insert or Replace the current impact report
        :param body: the report to be placed inside the impact report comment
        """
        logging.info("Searching for previous impact report.")
        found_comment = self.__get_impact_report_comment_id()

        if found_comment:
            logging.info(
                f'Previous impact report found. id={found_comment["id"]}'
                f' url={found_comment["html_url"]}.'
            )
            self.__update_impact_report(comment_id=found_comment["id"], body=body)
            logging.info(
                f'Previous impact report updated. id={found_comment["id"]}'
                f' url={found_comment["html_url"]}.'
            )
        else:
            logging.info(f"Previous impact report not found, creating a new one.")
            new_comment = self.__insert_impact_report(body)
            logging.info(
                f'New impact report created. id={new_comment["id"]} url={new_comment["html_url"]}.'
            )

    def __get_authenticated_user(self) -> dict:
        url = self._get_git_user_url()

        response = self.session.get(url)

        if response.status_code != 200:
            raise APIException(response=response)

        return response.json()

    def _get_change_files_url(self) -> str:
        raise NotImplementedError

    def _get_list_comments_url(self) -> str:
        raise NotImplementedError

    def _get_git_user_url(self) -> str:
        raise NotImplementedError

    def _get_detail_comments_url(self, commend_id: str) -> str:
        raise NotImplementedError


class GitHub(Git):
    """
    GitHub Git Provider implementation.
    """

    def __init__(self, settings: dict):
        self.host = "api.github.com"
        super().__init__(settings=settings)

    def _get_change_files_url(self) -> str:
        url = f"https://{self.host}/repos/{self.repository}/pulls/{self.pull_request_id}/files?per_page=100"
        return url

    def _get_list_comments_url(self) -> str:
        url = f"https://{self.host}/repos/{self.repository}/issues/{self.pull_request_id}/comments"
        return url

    def _get_detail_comments_url(self, commend_id: str) -> str:
        url = (
            f"https://{self.host}/repos/{self.repository}/issues/comments/{commend_id}"
        )
        return url

    def _get_git_user_url(self) -> str:
        url = f"https://{self.host}/user"
        return url


class GitProvider(Enum):
    """
    Source Code Management Providers
    """

    def __new__(
        cls,
        value: str,
        git_cls: type[Git],
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.git_cls = git_cls

        return obj

    GitHub = ("github", GitHub)

    def get_git_integration(self, settings: dict):
        return self.git_cls(settings=settings)
