from json import JSONEncoder


class ReportObjectEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class ReportObject:
    def __init__(self, data: dict):
        self._raw_data = data
        self._extract_attributes(data=self._raw_data)

    def _extract_attributes(self, data: dict):
        raise NotImplementedError(
            "A BitBucket object must implement the attributes extraction from json response"
        )

    def __str__(self):
        return ReportObjectEncoder().encode(self)


class Popularity(ReportObject):
    def _extract_attributes(self, data: dict):
        self.popularity = data.get("popularity")
        self.count = data.get("query_count") or data.get("view_count") or 0
        self.users_count = data.get("user_count") or 0


class DownstreamElement(ReportObject):
    def _extract_attributes(self, data: dict):
        self.guid = data.get("guid")
        self.name = data.get("name")
        self.type = data.get("data_type") or "-"
        self.full_name = data.get("full_name")
        self.data_source_type = data.get("data_source_type")
        self.linked_objects = data.get("linked_objs") or []
        self.linked_object_data_source_type = None
        if data.get("popularity"):
            self.popularity = Popularity(data.get("popularity"))
        else:
            self.popularity = None

    def __str__(self):
        return f"{self.guid=} {self.name=} {self.full_name=} {self.data_source_type=} {{{self.popularity}}}"


class DataSource(ReportObject):
    def _extract_attributes(self, data: dict):
        self.guid = data.get("guid")
        self.name = data.get("name")
        self.type = data.get("type")


class DataBase(ReportObject):
    def _extract_attributes(self, data: dict):
        self.guid = data.get("guid")
        self.name = data.get("name")
        self.data_source = DataSource(data.get("data_source"))


class Schema(ReportObject):
    def _extract_attributes(self, data: dict):
        self.guid = data.get("guid")
        self.name = data.get("name")


class TableLinked(ReportObject):
    def _extract_attributes(self, data: dict):
        self.guid = data.get("guid")
        self.name = data.get("name")
        self.database = DataBase(data.get("database"))
        self.schema = Schema(data.get("schema"))
        self.downstream_elements = []


class WarehouseLink(ReportObject):
    def __init__(self, data: dict):
        super().__init__(data)
        self.table = None

    def _extract_attributes(self, data: dict):
        self.guid = data["warehouse_table"]["guid"]

    def set_table(self, data: dict):
        self.table = TableLinked(data=data)


class DbtModel(ReportObject):
    def __init__(self, data: dict, project_relative_filepath: str):
        super().__init__(data)
        self.project_relative_filepath = project_relative_filepath

    def _extract_attributes(self, data: dict):
        self.filepath = data.get("filename")
        self.filename = self.filepath.split("/")[-1]
        self.status = data.get("status")
        self.guid = None
        self.warehouse_links = []
        self.downstream_elements = []
        # my downstream elements + warehouse linked table downstream elements
        self.all_unique_downstream_elements = []
