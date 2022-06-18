import os
from dataclasses import asdict
from logging import getLogger
from typing import Any, Dict, Iterator, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine.row import Row

from ..config import MappingConfig, MappingConfigMappingTable, StairlightConfig
from ..config_key import StairlightConfigKey
from ..template import Template, TemplateSource, TemplateSourceType
from .config import StairlightConfigIncludeRedash

logger = getLogger(__name__)


class RedashTemplate(Template):
    def __init__(
        self,
        mapping_config: MappingConfig,
        query_id: int,
        query_name: str,
        query_str: str = "",
        data_source_name: str = "",
    ):
        super().__init__(
            mapping_config=mapping_config,
            key=str(query_id),
            source_type=TemplateSourceType.REDASH,
        )
        self.query_id = query_id
        self.query_str = query_str
        self.uri = query_name
        self.data_source_name = data_source_name

    def find_mapped_table_attributes(self) -> Iterator[MappingConfigMappingTable]:
        """Get mapped tables as iterator

        Yields:
            Iterator[dict]: Mapped table attributes
        """
        mapping: Any
        for mapping in self._mapping_config.get_mapping():
            if mapping.TemplateSourceType != self.source_type.value:
                continue

            if (
                mapping.DataSourceName == self.data_source_name
                and mapping.QueryId == self.query_id
            ):
                for table_attributes in mapping.get_table():
                    yield table_attributes
                break

    def get_template_str(self) -> str:
        """Get template string that read from Redash
        Returns:
            str: Template string
        """
        return self.query_str


class RedashTemplateSource(TemplateSource):
    def __init__(
        self,
        stairlight_config: StairlightConfig,
        mapping_config: MappingConfig,
        include: StairlightConfigIncludeRedash,
    ) -> None:
        super().__init__(
            stairlight_config=stairlight_config,
            mapping_config=mapping_config,
        )
        self._include = include
        self.where_clause: List[str] = []
        self.conditions: Dict[str, Any] = self.make_conditions()

    def make_conditions(self) -> Dict[str, Any]:
        query_ids = self._include.QueryIds
        return {
            StairlightConfigKey.Redash.DATA_SOURCE_NAME: {
                "key": StairlightConfigKey.Redash.DATA_SOURCE_NAME,
                "query": "data_sources.name = :data_source",
                "parameters": self._include.DataSourceName,
            },
            StairlightConfigKey.Redash.QUERY_IDS: {
                "key": StairlightConfigKey.Redash.QUERY_IDS,
                "query": "queries.id IN :query_ids",
                "parameters": (tuple(query_ids) if query_ids else None),
            },
        }

    def search_templates(self) -> Iterator[Template]:
        results = self.get_queries_from_redash()
        for result in results:
            yield RedashTemplate(
                mapping_config=self._mapping_config,
                query_id=result[0],
                query_name=result[1],
                query_str=result[2],
                data_source_name=result[3],
            )

    def get_queries_from_redash(self) -> List[Row]:
        sql_file_name = "sql/redash_queries.sql"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        query_text = text(
            self.build_query_string(path=f"{current_dir}/{sql_file_name}")
        )

        data_source_condition: Dict[str, Any] = self.conditions.get(
            StairlightConfigKey.Redash.DATA_SOURCE_NAME, {}
        )
        query_ids_condition: Dict[str, Any] = self.conditions.get(
            StairlightConfigKey.Redash.QUERY_IDS, {}
        )
        connection_str = self.get_connection_str()
        engine = create_engine(connection_str)
        queries = engine.execute(
            query_text,
            data_source=data_source_condition.get("parameters", ""),
            query_ids=query_ids_condition.get("parameters", []),
        ).fetchall()

        return queries

    def build_query_string(self, path: str) -> str:
        base_query_string = self.read_query_from_file(path=path)
        for condition in self.conditions.values():
            if condition["key"] in asdict(self._include).keys():
                self.where_clause.append(condition["query"])
        return base_query_string + "WHERE " + " AND ".join(self.where_clause)

    def read_query_from_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def get_connection_str(self) -> str:
        environment_variable_name = self._include.DatabaseUrlEnvironmentVariable
        connection_str = os.environ.get(environment_variable_name, "")
        if not connection_str:
            logger.error(f"{environment_variable_name} is not found.")
        return connection_str
