
import logging

from settings import AppSettings, get_settings
from git import GitProvider
from selectstar import SelectStar
from report_printer import ReportPrinter

FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)


if __name__ == '__main__':

    log.info('Starting Dbt Impact Report by Select Star.')

    settings = get_settings()

    git_provider = GitProvider(settings.get(AppSettings.GIT_PROVIDER))

    log.info('Getting the list of changed models using GIT API.')

    git = git_provider.get_git_integration(settings)
    dbt_models = git.get_changed_files()

    log.info('Getting the lineage for each dbt model.')

    selectstar = SelectStar(settings=settings)
    selectstar.get_lineage(dbt_models=dbt_models)

    log.info('Creating the report.')

    printer = ReportPrinter(settings=settings)
    impact_report_body = printer.print(models=dbt_models)

    comment_id = git.insert_or_update_impact_report(body=impact_report_body)

    log.info('Dbt Impact Report has ended, bye!')
