from operator import attrgetter

from dataobjects import DbtModel
from settings import AppSettings

HTML_FOR_WARNING_SIGN = "&#x26a0;&#xfe0f;"
HTML_FOR_WHITE_CHECK_MARK = "&#x2705;"


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

        elements: list[
            [int, str]
        ] = []  # number of impacts per block + the block itself

        total_impact_number = 0

        for model in models:
            if model.guid:
                element_impact_number, model_text_body = self._print_model(model)
                total_impact_number = total_impact_number + element_impact_number
                elements.append((element_impact_number, model_text_body))
            else:
                model_text_body = self._print_model_not_found(model)
                elements.append((0, model_text_body))

        header = (
            f"## <img src='{self.select_star_web_url}/icons/logo-ss-horizontal-white.svg' width='25' height='25' "
            f"align='center'> Select Star Impact Report\n"
            f"Total Potential Impact: {self.__decide_potential_impact_img_emoji(total_impact_number)} "
            f"**{total_impact_number}** direct downstream objects"
            f" for the **{len(models)}** changed dbt models.<br/><br/><br/>"
        )

        # sort by impact number, descending
        elements.sort(reverse=True)

        # we use only the text of each element block
        body = "\n<br/>".join(element[1] for element in elements)

        return f"{header}{body}"

    @staticmethod
    def __decide_potential_impact_img_emoji(impact_number):
        return HTML_FOR_WARNING_SIGN if impact_number > 0 else HTML_FOR_WHITE_CHECK_MARK

    def _print_model_not_found(self, model: DbtModel) -> str:
        lines = [
            f"<img src='{self.select_star_web_url}/icons/dbt.svg' width='15' height='15' align='center'> "
            f"{model.filepath.split('.')[0]}\n",
            f"Model not found in Select Star database. This model may be hidden or not ingested.",
        ]

        return "".join(lines)

    def _print_model(self, model: DbtModel) -> (int, str):
        """
        Creates the report of a single model.
        :param model: a dbt model
        :return: the text of a single dbt model
        """

        lines = []

        model_url = f"{self.select_star_web_url}/tables/{model.guid}/overview"

        if model.warehouse_links:
            linked_table = model.warehouse_links[0].table
            linked_table_link = (
                f"{self.select_star_web_url}/tables/{linked_table.guid}/overview"
            )
            maps_to = (
                f" links to [{linked_table.database.data_source.type}/{linked_table.database.name}/"
                f"{linked_table.schema.name}/{linked_table.name}]({linked_table_link})"
            )
        else:
            maps_to = f" has no linked warehouse table"

        lines.append(
            f"<img src='{self.select_star_web_url}/icons/dbt.svg' width='15' height='15' align='center'> "
            f"[{model.filepath.split('.')[0]}]({model_url}){maps_to}\n"
        )

        total_impact_number = len(model.downstream_elements)
        if model.warehouse_links:
            total_impact_number = total_impact_number + len(
                model.warehouse_links[0].table.downstream_elements
            )

        if total_impact_number > 0:
            lines.append(
                f"Potential Impact: {HTML_FOR_WARNING_SIGN} {total_impact_number} direct downstream objects.\n"
            )
        else:
            lines.append(
                f"Potential Impact: {HTML_FOR_WHITE_CHECK_MARK} No direct downstream objects.\n"
            )

        if total_impact_number:
            lines.append(
                "| # | Data Source Type | Object Type | Name |\n|--------|--------|--------|--------|\n"
            )

            all_downstream_elements = model.downstream_elements
            if model.warehouse_links:
                all_downstream_elements = (
                    all_downstream_elements
                    + model.warehouse_links[0].table.downstream_elements
                )

            all_downstream_elements.sort(
                key=attrgetter("data_source_type", "type", "name")
            )

            for idx, model_element in enumerate(all_downstream_elements, start=1):
                obj_url = (
                    f"{self.select_star_web_url}/tables/{model_element.guid}/overview"
                )
                lines.append(
                    f"|{idx}"
                    f"|{self._build_datasource_img_tag(model_element.data_source_type)}"
                    f" {model_element.data_source_type}"
                    f"|{model_element.type}"
                    f"|[{model_element.name}]({obj_url})|\n"
                )

        return total_impact_number, "".join(lines)

    def _build_datasource_img_tag(self, data_source_type: str):
        if data_source_type in [
            "snowflake",
            "mode",
            "bigquery",
            "tableau",
            "dbt",
            "periscope",
            "sigma",
            "metabase",
            "databricks",
            "glue",
        ]:
            icon = data_source_type
        elif data_source_type == "looker":
            icon = "iconLooker"
        elif data_source_type == "postgres":
            icon = "postgresql"
        elif data_source_type in ["redshift", "trial_redshift"]:
            icon = "redshift-instance"
        elif data_source_type == "aws_s3":
            icon = "S3"
        elif data_source_type == "power_bi":
            icon = "powerbi"
        else:
            icon = "database"

        return f"<img src='{self.select_star_web_url}/icons/{icon}.svg' width='15' height='15' align='center'>"
