
import logging
import re
import requests

from enum import Enum
from string import Template

from dataobjects import DbtModel
from exceptions import APIException
from settings import AppSettings


log = logging.getLogger(__name__)


class GitProvider(Enum):
    """
    Source Code Management Providers
    """

    def __new__(
        cls,
        value: str,
        host: str,
        pull_request_files_link_template: str,
        list_comments_link_template: str,
        detail_comments_link_template: str
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.host = host
        obj.pull_request_link_template = Template(pull_request_files_link_template)
        obj.list_comments_link_template = Template(list_comments_link_template)
        obj.detail_comments_link_template = Template(detail_comments_link_template)

        return obj

    GitHub = (
        "github",
        "api.github.com",
        "https://$host/repos/$repository/pulls/$pull_request_id/files?per_page=100",
        "https://$host/repos/$repository/issues/$pull_request_id/comments",
        "https://$host/repos/$repository/issues/comments/$comment_id"
    )
    BitBucket = (
        "bitbucket",
        "bitbucket.org",
        "https://$host/$repository/pull-requests/$pull_request_id",
        "https://$host/$repository/issues/$pull_request_id/comments",  # ?
        "https://$host/$repository/issues/comments/$comment_id"  # ?
    )

    def build_pull_request_files_url(self, repository: str, pull_request_id: str):
        return self.pull_request_link_template.substitute(
            {
                "host": self.host,
                "repository": repository,
                "pull_request_id": pull_request_id,
            }
        )

    def build_list_comments_url(self, repository: str, pull_request_id: str):
        return self.list_comments_link_template.substitute(
            {
                "host": self.host,
                "repository": repository,
                "pull_request_id": pull_request_id,
            }
        )

    def build_detail_comments_url(self, repository: str, comment_id: str):
        return self.detail_comments_link_template.substitute(
            {
                "host": self.host,
                "repository": repository,
                "comment_id": comment_id,
            }
        )

    def get_git_integration(self, settings: dict):
        return Git(git_provider=self, settings=settings)


class Git:

    comment_anchor = '<!-- ImpactReportIdentifier: select-star-dbt-impact-report -->'

    def __init__(self, git_provider: GitProvider, settings: dict):
        self.settings = settings
        self.git_provider = git_provider
        self.repository = self.settings.get(AppSettings.GIT_REPOSITORY)
        self.pull_request_id = self.settings.get(AppSettings.PULL_REQUEST_ID)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {settings.get(AppSettings.GIT_REPOSITORY_TOKEN)}',
            'User-Agent': 'Select Star Dbt Impact Report'
        })

    def get_changed_files(self):
        url = self.git_provider.build_pull_request_files_url(repository=self.repository,
                                                             pull_request_id=self.pull_request_id)

        response = self.session.get(url)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {self.git_provider.host}. Code {response.status_code}."
                               f" Message {response.content}")

        files = response.json()

        if len(files) == 100:
            log.warning("Processing only the first 100 files on this pull request.")

        found_models = []

        for file in files:
            result = re.match(r"models/(\w)+/(\w+)+.sql", file.get("filename"), flags=re.IGNORECASE)
            if result:
                found_models.append(DbtModel(file))

        log.info(f'Found models: {[(f.filename, f.status) for f in found_models]}')

        return found_models

    def __get_impact_report_comment_id(self) -> dict | None:
        url = self.git_provider.build_list_comments_url(repository=self.repository,
                                                        pull_request_id=self.pull_request_id)
        response = self.session.get(url)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {self.git_provider.host}. Code {response.status_code}."
                               f" Message {response.content}")

        comments = response.json()

        for comment in comments:
            if self.comment_anchor in comment.get('body'):
                return comment

    def __insert_impact_report(self, body:str) -> dict:
        url = self.git_provider.build_list_comments_url(repository=self.repository,
                                                        pull_request_id=self.pull_request_id)
        body = f'{self.comment_anchor}\n{body}'

        response = self.session.post(url, json={"body": body})

        return response.json()

    def __update_impact_report(self, comment_id: str, body: str):
        url = self.git_provider.build_detail_comments_url(repository=self.repository,
                                                          comment_id=comment_id)

        body = f'{self.comment_anchor}\n{body}'

        response = self.session.patch(url, json={"body": body})

        return response.json()

    def insert_or_update_impact_report(self, body):
        logging.info('Searching for previous impact report.')
        found_comment = self.__get_impact_report_comment_id()

        if found_comment:
            logging.info(f'Previous impact report found. id={found_comment["id"]}'
                         f' url={found_comment["html_url"]}.')
            self.__update_impact_report(comment_id=found_comment["id"], body=body)
            logging.info(f'Previous impact report updated. id={found_comment["id"]}'
                         f' url={found_comment["html_url"]}.')
        else:
            logging.info(f'Previous impact report not found, creating a new one.')
            new_comment = self.__insert_impact_report(body)
            logging.info(f'New impact report created. id={new_comment["id"]} url={new_comment["html_url"]}.')
