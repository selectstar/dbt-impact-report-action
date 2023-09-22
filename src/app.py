
from settings import AppSettings, get_settings
from git import GitProvider
from selectstar import SelectStar


if __name__ == '__main__':

    settings = get_settings()

    git_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    git = git_provider.get_git_integration(settings)
    dbt_models = git.get_changed_files()

    selectstar = SelectStar(settings=settings)
    selectstar.get_lineage(dbt_models=dbt_models)

    for m in dbt_models:
        print(m)
