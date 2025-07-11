import toml

from src.repositories import SearchIndexTypeRepository
from src.services.db import get_session

CONFIG_PATH = "/app/config.toml"
CONFIG = toml.load(CONFIG_PATH)
CORE_CONFIG = CONFIG.get("core", {})

NAME = CORE_CONFIG.get("NAME")
MODEL_LIST = CORE_CONFIG.get("MODEL_LIST")
DEFAULT_MODEL = CORE_CONFIG.get("DEFAULT_MODEL")


class CoreConfigUsecase:
    def __init__(self):
        self.search_index_type_repository = SearchIndexTypeRepository()

    def get_core_config(self):
        with get_session() as session:
            search_index_type_list = self.search_index_type_repository.find_all_ordered(
                session
            )
            SEARCH_INDEX_NAME_JP_LIST = [
                search_index_type.folder_name
                for search_index_type in search_index_type_list
            ]
            SEARCH_INDEX_NAME_ID_LIST = [
                search_index_type.id for search_index_type in search_index_type_list
            ]
            return {
                "NAME": NAME,
                "SEARCH_INDEX_NAME_JP_LIST": SEARCH_INDEX_NAME_JP_LIST,
                "SEARCH_INDEX_NAME_ID_LIST": SEARCH_INDEX_NAME_ID_LIST,
                "SEARCH_INDEX_AZURE_ID_LIST": SEARCH_INDEX_NAME_ID_LIST,
                "MODEL_LIST": MODEL_LIST,
                "DEFAULT_MODEL": DEFAULT_MODEL,
            }

    def get_core_name(self):
        return NAME
