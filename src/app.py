
from settings import AppSettings, get_settings
from git import GitProvider, Git


if __name__ == '__main__':

    settings = get_settings()

    git_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    git = Git(token=settings.get(AppSettings.GIT_REPOSITORY_TOKEN))
    files = git.get_changed_files(git_provider=git_provider,
                                  repository=settings.get(AppSettings.GIT_REPOSITORY),
                                  pull_request_id=settings.get(AppSettings.PULL_REQUEST_ID))

    for f in files:
        print(f)
