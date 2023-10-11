from requests import Response


class APIException(Exception):
    def __init__(self, response: Response):
        super().__init__(
            f"Unexpected response. URL {response.url}. Code {response.status_code}."
            f" Message {response.content}"
        )
