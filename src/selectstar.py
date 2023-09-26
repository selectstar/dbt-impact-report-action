
import requests

from dataobjects import DbtModel, DownstreamElement, TableLinked, WarehouseLink
from exceptions import APIException
from settings import AppSettings


class SelectStar:
    """
    Select Star API interface.
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.headers = {'Authorization': f'Token {settings.get(AppSettings.SELECTSTAR_API_TOKEN)}'}
        self.host = settings.get(AppSettings.SELECTSTAR_API_URL)
        self.datasource_guid = settings.get(AppSettings.SELECTSTAR_DATASOURCE_GUID)

    def __get_tables_guids(self, dbt_models: list[DbtModel]):
        """
        Populates the GUID for each given dbt_model using its filename
        :param dbt_models: list of dbt models to fetch its GUID
        """

        page_size = 10

        for i in range(0, len(dbt_models), page_size):
            a_slice = dbt_models[i:i + page_size]
            slice_str = ",".join(dbt_model.filename for dbt_model in a_slice)
            url = f'{self.host}/v1/tables/?query=%7Bguid,extra%7D&filename={slice_str}&datasources={self.datasource_guid}'
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                raise APIException(f"Unexpected response. Host {self.host}. Code {response.status_code}."
                                   f" Message {response.content}")

            tables = response.json()["results"]

            for dbt_model in a_slice:
                for table in tables:
                    if dbt_model.filename in table['extra']['path']:
                        dbt_model.guid = table['guid']
                        continue

    def __get_table(self, guid: str) -> dict:
        """
        Get the data for the given table GUID
        :param guid: table's guid
        :return: the data returned by the API
        """
        url = f'{self.host}/v1/tables/{guid}/' \
              f'?query=%7Bguid,name,database%7Bguid,name,data_source%7Bguid,name,type%7D%7D,schema%7Bguid,name%7D%7D'
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {self.host}. Code {response.status_code}."
                               f" Message {response.content}")

        return response.json()

    def __get_warehouse_links(self, dbt_models: list[DbtModel]):
        """
        Get the warehouse-link for each given dbt model
        :param dbt_models: a list of dbt models
        """

        for model in dbt_models:
            url = f'{self.host}/v1/dbt/warehouse-link/{model.guid}/'
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                raise APIException(f"Unexpected response. Host {self.host}. Code {response.status_code}."
                                   f" Message {response.content}")

            found_links = response.json()

            for link in found_links:
                warehouse_link = WarehouseLink(link)
                warehouse_link.set_table(self.__get_table(warehouse_link.guid))
                model.warehouse_links.append(warehouse_link)

    def __get_element_lineage(self, element: DbtModel | TableLinked):
        """
        Get the lineage for the given element
        :param element: a dbt model or a table linked (warehouse link)
        """
        url = f'{self.host}/v1/lineage/{element.guid}/?dbt_links=true&direction=right&group_by_data_source=true' \
              f'&include_borderline_edges=true&looker_db_lineage=true&looker_view_lineage=true&max_depth=1&' \
              f'mode=table&mode_lineage=false&tableau_table_lineage=true'

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise APIException(f"Unexpected response. Host {self.host}. Code {response.status_code}."
                               f" Message {response.content}")

        found_elements = response.json().get("table_lineage")

        for found_element in found_elements:
            if found_element.get("guid") != element.guid:
                element.downstream_elements.append(DownstreamElement(found_element))

    def __get_full_lineage(self, dbt_models: list[DbtModel]):
        """
        Get lineage for all dbt models and their related warehouse links
        :param dbt_models: list of dbt models
        """
        for model in dbt_models:
            self.__get_element_lineage(model)
            for link in model.warehouse_links:
                self.__get_element_lineage(link.table)

    def get_lineage(self, dbt_models: list[DbtModel]):
        """
        Fetch all the required data for the impact report
        :param dbt_models: list of the modified models
        :return: complete structure of models, tables and lineage
        """
        self.__get_tables_guids(dbt_models=dbt_models)
        self.__get_warehouse_links(dbt_models=dbt_models)
        self.__get_full_lineage(dbt_models=dbt_models)
        return dbt_models