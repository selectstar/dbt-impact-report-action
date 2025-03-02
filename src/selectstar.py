import logging

import requests

from dataobjects import DbtModel, DownstreamElement, TableLinked, WarehouseLink
from exceptions import APIException
from settings import AppSettings

log = logging.getLogger(__name__)


class SelectStar:
    """
    Select Star API interface.
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {settings.get(AppSettings.SELECTSTAR_API_TOKEN)}",
                "User-Agent": "Select Star Dbt Impact Report",
            }
        )
        self.api_url = settings.get(AppSettings.SELECTSTAR_API_URL)
        self.datasource_guid = settings.get(AppSettings.SELECTSTAR_DATASOURCE_GUID)

    def __get_tables_guids(self, dbt_models: list[DbtModel]):
        """
        Populates the GUID for each given dbt_model using its filename
        :param dbt_models: list of dbt models to fetch its GUID
        """

        page_size = 10
        url = f"{self.api_url}/v1/tables/"

        for i in range(0, len(dbt_models), page_size):
            a_slice = dbt_models[i : i + page_size]
            slice_str = ",".join(
                dbt_model.project_relative_filepath for dbt_model in a_slice
            )
            log.info(
                f"  Fetching GUID for the models: '{slice_str}' {self.datasource_guid=}"
            )
            params = {
                "query": "{guid,extra,table_type}",
                "filenames": slice_str,
                "datasources": self.datasource_guid,
            }
            response = self.session.get(url, params=params)

            if response.status_code != 200:
                raise APIException(response=response)

            tables = response.json()["results"]

            for dbt_model in a_slice:
                for table in tables:
                    if dbt_model.filename in table["extra"]["path"]:
                        dbt_model.guid = table["guid"]
                        continue

    def __get_table(self, guid: str) -> dict:
        """
        Get the data for the given table GUID
        :param guid: table's guid
        :return: the data returned by the API
        """
        url = f"{self.api_url}/v1/tables/{guid}/"
        params = {
            "query": f"{{guid,name,data_type,database{{guid,name,data_source{{guid,name,type}}}},schema{{guid,name}}}}"
        }
        response = self.session.get(url, params=params)

        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise APIException(response=response)

        return response.json()

    def __get_warehouse_links(self, dbt_models: list[DbtModel]):
        """
        Get the warehouse-link for each given dbt model
        :param dbt_models: a list of dbt models
        """

        for model in dbt_models:
            if not model.guid:
                continue

            log.info(f"  Fetching warehouse links for {model.guid=} {model.filename=}")

            url = f"{self.api_url}/v1/dbt/warehouse-link/{model.guid}/"
            response = self.session.get(url)

            if response.status_code != 200:
                raise APIException(response=response)

            found_links = response.json()

            for link in found_links["results"]:
                warehouse_link = WarehouseLink(link)
                found_table = self.__get_table(warehouse_link.guid)
                if found_table:
                    warehouse_link.set_table(found_table)
                    model.warehouse_links.append(warehouse_link)
                else:
                    log.warning(
                        f"   A warehouse link was found, but the target DWH table was not found."
                        f" Was it removed/deactivated? Missing table guid = {warehouse_link.guid}"
                    )

    def __get_element_lineage(self, element: DbtModel | TableLinked):
        """
        Get the lineage for the given element
        :param element: a dbt model or a table linked (warehouse link)
        """
        url = f"{self.api_url}/v1/lineage/{element.guid}/"
        params = {
            "dbt_links": True,
            "direction": "right",
            "group_by_data_source": True,
            "include_borderline_edges": True,
            "looker_db_lineage": True,
            "looker_view_lineage": True,
            "max_depth": 1,
            "mode": "table",
            "mode_lineage": False,
            "tableau_table_lineage": True,
        }

        log.info(f"  Fetching lineage for {element.guid=}")

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise APIException(response=response)

        found_elements = response.json()["table_lineage"]

        for found_element in found_elements:
            if found_element.get("guid") != element.guid:
                element.downstream_elements.append(DownstreamElement(found_element))

    def __get_full_lineage(self, dbt_models: list[DbtModel]):
        """
        Get lineage for all dbt models and their related warehouse links
        :param dbt_models: list of dbt models
        """
        for model in dbt_models:
            if not model.guid:
                continue
            self.__get_element_lineage(model)
            for link in model.warehouse_links:
                self.__get_element_lineage(link.table)

    def __deduplicate_downstream(self, dbt_models: list[DbtModel]):
        """
        Checks both the dbt model downstream list and their warehouse link downstream list for duplicates between them,
         creating a single, unique, downstream.
        :param dbt_models: list of dbt models
        """
        for model in dbt_models:
            # we merge the downstream elements from the dbt model and its warehouse link
            all_downstream_elements = model.downstream_elements
            if model.warehouse_links:
                all_downstream_elements = (
                    all_downstream_elements
                    + model.warehouse_links[0].table.downstream_elements
                )

            # then we create a unique list of downstream elements
            unique_downstream_elements = {}

            # first we pick the dbt elements, they have priority over their links
            for downstream_element in all_downstream_elements:
                if (
                    downstream_element.guid not in unique_downstream_elements
                    and downstream_element.data_source_type == "dbt"
                ):
                    unique_downstream_elements[
                        downstream_element.guid
                    ] = downstream_element

            # second we pick the other data source type elements and check if the linked object
            # is already in the list previously populated by dbt elements
            for downstream_element in all_downstream_elements:
                if (
                    downstream_element.guid not in unique_downstream_elements
                    and downstream_element.data_source_type != "dbt"
                ):
                    is_unique = True
                    for linked_obj in downstream_element.linked_objects:
                        if linked_obj in unique_downstream_elements:
                            unique_downstream_elements[
                                linked_obj
                            ].linked_object_data_source_type = (
                                downstream_element.data_source_type
                            )
                            is_unique = False
                            break
                    if is_unique:
                        unique_downstream_elements[
                            downstream_element.guid
                        ] = downstream_element

            model.all_unique_downstream_elements = list(
                unique_downstream_elements.values()
            )

    def get_lineage(self, dbt_models: list[DbtModel]):
        """
        Fetch all the required data for the impact report
        :param dbt_models: list of the modified models
        :return: complete structure of models, tables and lineage
        """
        log.info(" Fetching the dbt models GUID")
        self.__get_tables_guids(dbt_models=dbt_models)
        log.info(" Fetching the dbt models warehouse links")
        self.__get_warehouse_links(dbt_models=dbt_models)
        log.info(" Fetching the dbt models full lineage")
        self.__get_full_lineage(dbt_models=dbt_models)
        log.info(" Deduplicate the downstream elements")
        self.__deduplicate_downstream(dbt_models=dbt_models)
        return dbt_models
