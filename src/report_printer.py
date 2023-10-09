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
        elements: list[str] = []

        total_impact_number = 0

        for model in models:
            if model.guid:
                element_impact_number, model_text_body = self._print_model(model)
                total_impact_number = total_impact_number + element_impact_number
                elements.append(model_text_body)
            else:
                model_text_body = self._print_model_not_found(model)
                elements.append(model_text_body)

        header = (
            f"# Select Star Impact Report\n\n"
            f"### Total Potential Impact: {total_impact_number} direct downstream objects for the {len(models)}"
            f" changed dbt models\n\n"
        )

        body = "\n".join(elements)

        return f"{header}{body}"

    @staticmethod
    def _print_model_not_found(model: DbtModel) -> str:

        lines = [
            f"### - {model.filepath}\n",
            f"Model not found in Select Star database.",
        ]

        return "".join(lines)

    def _print_model(self, model: DbtModel) -> (int, str):
        """
        Creates the report of a single model
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
                f" maps to [{linked_table.database.data_source.type}/{linked_table.database.name}/"
                f"{linked_table.schema.name}/{linked_table.name}]({linked_table_link})"
            )
        else:
            maps_to = f" has no mapped warehouse table"

        lines.append(f"### - {model.filepath}\n")
        lines.append(f"[{model.filename.split('.')[0]}]({model_url}){maps_to}\n")

        total_impact_number = len(model.downstream_elements)
        if model.warehouse_links:
            total_impact_number = total_impact_number + len(
                model.warehouse_links[0].table.downstream_elements
            )

        lines.append(
            f"Potential Impact: {total_impact_number} direct downstream objects.\n"
        )

        if total_impact_number:
            lines.append(
                "| Source | Object Type | Name |\n|--------|--------|--------|\n"
            )

            for model_element in model.downstream_elements:
                obj_url = (
                    f"{self.select_star_web_url}/tables/{model_element.guid}/overview"
                )
                lines.append(
                    f"|{model_element.data_source_type}"
                    f"|{model_element.type}"
                    f"|[{model_element.name}]({obj_url})|\n"
                )

            if model.warehouse_links:
                linked_table = model.warehouse_links[0].table

                for linked_table_element in linked_table.downstream_elements:
                    obj_url = (
                        f"{self.select_star_web_url}/link/{linked_table_element.guid}"
                    )
                    lines.append(
                        "|".join(
                            [
                                "",
                                linked_table_element.data_source_type,
                                linked_table_element.type,
                                f"[{linked_table_element.name}]({obj_url})",
                                "",
                            ]
                        )
                        + "\n"
                    )

        return total_impact_number, "".join(lines)
