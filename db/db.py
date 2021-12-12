import requests
import logging


class DB:
    URL = "https://manga-utils-server.herokuapp.com"
    logger = logging.getLogger("crawler.db.DB")

    @classmethod
    def put_manga(cls, file_id, metadata):
        assert isinstance(metadata, dict)
        assert isinstance(file_id, str)

        metadata["_id"] = file_id
        metadata["_meta"] = 1

        resp = requests.put(cls.URL + "/add_manga", json=metadata)

        message = resp.json()["message"]
        cls.logger.debug(f"Response --> {resp.status_code}: {message}")

        return file_id

    @classmethod
    def update_index(cls, index_element):
        assert isinstance(index_element, dict)

        resp = requests.patch(cls.URL + "/change_index", json=index_element)

        message = resp.json()["message"]
        cls.logger.debug(f"Response --> {resp.status_code}: {message}")