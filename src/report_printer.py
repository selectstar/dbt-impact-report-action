
from operator import attrgetter

from dataobjects import DbtModel
from settings import AppSettings


class ReportPrinter:

    def __init__(self, settings: dict):
        self.settings = settings
        self.select_star_web_url = settings.get(AppSettings.SELECTSTAR_WEB_URL)

    def print(self, models: list[DbtModel]):
        """
        Creates the impact report
        :param models: a list of dbt models
        :return: the complete, final text of the report
        """

        elements: list[[int, str]] = []  # number of impacts per block + the block itself

        total_impact_number = 0

        for model in models:
            if model.guid:
                element_impact_number, model_text_body = self._print_model(model)
                total_impact_number = total_impact_number + element_impact_number
                elements.append((element_impact_number, model_text_body))
            else:
                model_text_body = self._print_model_not_found(model)
                elements.append((0, model_text_body))

        header = f"# <img src='{self.select_star_web_url}/images/logoSmall.svg' width='25' height='25'> " \
                 f"Select Star Impact Report\n" \
                 f"Total Potential Impact: {self.__decide_potential_impact_img_emoji(total_impact_number)} " \
                 f"**{total_impact_number}** direct downstream objects" \
                 f" for the **{len(models)}** changed dbt models.<br/><br/><br/>"

        # sort by impact number, descending
        elements.sort(reverse=True)

        # we use only the text of each element block
        body = "\n<br/>".join(element[1] for element in elements)

        return f"{header}{body}"

    @staticmethod
    def __decide_potential_impact_img_emoji(impact_number):
        return ':warning:' if impact_number > 0 else ':white_check_mark:'

    @staticmethod
    def _print_model_not_found(model: DbtModel) -> str:

        lines = [
            f'### - {model.filepath}\n',
            f'Model not found in Select Star database.',
        ]

        return "".join(lines)

    def _print_model(self, model: DbtModel) -> (int, str):
        """
        Creates the report of a single model
        :param model: a dbt model
        :return: the text of a single dbt model
        """

        lines = []

        model_url = f'{self.select_star_web_url}/tables/{model.guid}/overview'

        if model.warehouse_links:
            linked_table = model.warehouse_links[0].table
            linked_table_link = f'{self.select_star_web_url}/tables/{linked_table.guid}/overview'
            maps_to = f" links to [{linked_table.database.data_source.type}/{linked_table.database.name}/" \
                      f"{linked_table.schema.name}/{linked_table.name}]({linked_table_link})"
        else:
            maps_to = f" has no linked warehouse table"

        lines.append(f"<img src='{self.select_star_web_url}/icons/dbt.svg' width='15' height='15'> "
                     f"[{model.filepath.split('.')[0]}]({model_url}){maps_to}\n")

        total_impact_number = len(model.downstream_elements)
        if model.warehouse_links:
            total_impact_number = total_impact_number + len(model.warehouse_links[0].table.downstream_elements)

        if total_impact_number > 0:
            lines.append(f"Potential Impact: :warning: {total_impact_number} direct downstream objects.\n")
        else:
            lines.append(f"Potential Impact: :white_check_mark: No direct downstream objects.\n")

        if total_impact_number:
            lines.append("| # | Data Source Type | Object Type | Name |\n|--------|--------|--------|--------|\n")

            all_downstream_elements = model.downstream_elements
            if model.warehouse_links:
                all_downstream_elements = all_downstream_elements + model.warehouse_links[0].table.downstream_elements

            all_downstream_elements.sort(key=attrgetter('data_source_type'))
            all_downstream_elements.sort(key=attrgetter('type'))
            all_downstream_elements.sort(key=attrgetter('name'))

            for idx, model_element in enumerate(all_downstream_elements, start=1):
                obj_url = f'{self.select_star_web_url}/tables/{model_element.guid}/overview'
                lines.append(f"|{idx}"
                             f"|<img src='{self.select_star_web_url}/icons/{model_element.data_source_type}.svg'"
                             f" width='15' height='15'> {model_element.data_source_type}"
                             f"|{model_element.type}"
                             f"|[{model_element.name}]({obj_url})|\n")

        return total_impact_number, "".join(lines)
