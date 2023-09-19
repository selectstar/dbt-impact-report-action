
from settings import AppSettings, get_settings
from git import GitProvider, Git


if __name__ == '__main__':

    settings = get_settings()

    scm_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    scm_retriever = Git(token=settings.get(AppSettings.GIT_REPOSITORY_TOKEN))
    files = scm_retriever.get_changed_files(scm_provider=scm_provider,
                                            repository=settings.get(AppSettings.GIT_REPOSITORY),
                                            pull_request_id=settings.get(AppSettings.PULL_REQUEST_ID))

    for f in files:
        print(f)
