
import logging

from settings import AppSettings, get_settings
from git import GitProvider
from selectstar import SelectStar


FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)


if __name__ == '__main__':

    log.info('Starting Dbt Impact Report by Select Star.')

    settings = get_settings()

    git_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    git = git_provider.get_git_integration(settings)
    dbt_models = git.get_changed_files()

    selectstar = SelectStar(settings=settings)
    selectstar.get_lineage(dbt_models=dbt_models)

    impact_report_body = "THIS IS THE IMPACT REPORT!!"

    comment_id = git.insert_or_update_impact_report(body=impact_report_body)

    for m in dbt_models:
        print(m)

    log.info('Dbt Impact Report has ended, bye!')
