
from settings import AppSettings, get_settings
from git import GitProvider


if __name__ == '__main__':

    settings = get_settings()

    git_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    git = git_provider.get_git_integration(settings)
    files = git.get_changed_files()

    for f in files:
        print(f)
