import enum
import os
import pathlib
import re
from logging import getLogger
from typing import Iterator, Optional

from google.cloud import storage
from jinja2 import BaseLoader, Environment, FileSystemLoader

logger = getLogger(__name__)


class SourceType(enum.Enum):
    """SQL template source type"""

    FS = "fs"
    GCS = "gcs"

    def __str__(self):
        return self.name


class SQLTemplate:
    """SQL template"""

    def __init__(
        self,
        map_config: dict,
        source_type: SourceType,
        file_path: str,
        bucket: Optional[str] = None,
        project: Optional[str] = None,
        default_table_prefix: Optional[str] = None,
        labels: Optional[dict] = None,
    ):
        """SQL template

        Args:
            map_config (dict): Mapping configuration
            source_type (SourceType): Source type
            file_path (str): SQL file path
            bucket (Optional[str], optional):
                Bucket name where SQL file saved.Defaults to None.
            project (Optional[str], optional):
                Project name where SQL file saved.Defaults to None.
            default_table_prefix (Optional[str], optional):
                If project or dataset that configured table have are omitted,
                it will be complement this prefix. Defaults to None.
        """
        self._map_config = map_config
        self.source_type = source_type
        self.file_path = file_path
        self.bucket = bucket
        self.project = project
        self.default_table_prefix = default_table_prefix
        self.uri = self.get_uri()

    def get_uri(self) -> str:
        """Get uri from file path

        Returns:
            str: uri
        """
        uri = ""
        if self.source_type == SourceType.FS:
            p = pathlib.Path(self.file_path)
            uri = str(p.resolve())
        elif self.source_type == SourceType.GCS:
            uri = f"gs://{self.bucket}/{self.file_path}"
        return uri

    def get_mapped_tables_iter(self) -> Iterator[dict]:
        """Get mapped tables as iterator

        Yields:
            Iterator[dict]: Mapped table
        """
        for mapping in self._map_config.get("mapping"):
            has_suffix = False
            if mapping.get("file_suffix"):
                has_suffix = self.file_path.endswith(mapping.get("file_suffix"))
            if has_suffix or self.uri == mapping.get("uri"):
                for table in mapping.get("tables"):
                    yield table

    def is_mapped(self) -> bool:
        """Check if the template is set to mapping configuration

        Returns:
            bool: Is set or not
        """
        result = False
        for _ in self.get_mapped_tables_iter():
            result = True
            break
        return result

    @staticmethod
    def get_jinja_params(template_str) -> list:
        """Get jinja parameters

        Args:
            template_str (str): File string

        Returns:
            list: Jinja parameters
        """
        jinja_expressions = "".join(
            re.findall("{{[^}]*}}", template_str, re.IGNORECASE)
        )
        return re.findall("[^{} ]+", jinja_expressions, re.IGNORECASE)

    def get_template_file_str(self) -> str:
        """Get file-strings that read from a template file

        Returns:
            str: File string
        """
        template_file_str = ""
        if self.source_type == SourceType.FS:
            template_file_str = self.get_template_file_str_fs()
        elif self.source_type == SourceType.GCS:
            template_file_str = self.get_template_file_str_gcs()
        return template_file_str

    def get_template_file_str_fs(self) -> str:
        """Get file string that read from a file in local file system

        Returns:
            str: File string
        """
        template_str = ""
        with open(self.file_path) as f:
            template_str = f.read()
        return template_str

    def get_template_file_str_gcs(self) -> str:
        """Get file string that read from a file in GCS

        Returns:
            str: File string
        """
        client = storage.Client(credentials=None, project=self.project)
        bucket = client.get_bucket(self.bucket)
        blob = bucket.blob(self.file_path)
        return blob.download_as_bytes().decode("utf-8")

    def render(self, params: dict) -> str:
        """Render SQL query string from a jinja template

        Args:
            params (dict): Jinja paramters

        Returns:
            str: SQL query string
        """
        query_str = ""
        if self.source_type == SourceType.FS:
            query_str = self.render_from_fs(params)
        elif self.source_type == SourceType.GCS:
            query_str = self.render_from_gcs(params)
        return query_str

    def render_from_fs(self, params: dict) -> str:
        """Render SQL query string from a jinja template on local file system

        Args:
            params (dict): Jinja paramters

        Returns:
            str: SQL query string
        """
        env = Environment(loader=FileSystemLoader(os.path.dirname(self.file_path)))
        jinja_template = env.get_template(os.path.basename(self.file_path))
        return jinja_template.render(params=params)

    def render_from_gcs(self, params: dict) -> str:
        """Render SQL query string from a jinja template on GCS

        Args:
            params (dict): Jinja paramters

        Returns:
            str: SQL query string
        """
        template_file_str = self.get_template_file_str_gcs()
        jinja_template = Environment(loader=BaseLoader()).from_string(template_file_str)
        return jinja_template.render(params=params)


class TemplateSource:
    """SQL template source"""

    def __init__(self, stairlight_config: dict, map_config: dict) -> None:
        """SQL template source

        Args:
            stairlight_config (dict): Stairlight configuration
            map_config (dict): Mapping configuration
        """
        self._stairlight_config = stairlight_config
        self._map_config = map_config

    def search_templates_iter(self) -> Iterator[SQLTemplate]:
        """Search SQL template files

        Yields:
            Iterator[SQLTemplate]: SQL template file attributes
        """
        for source in self._stairlight_config.get("include"):
            type = source.get("type")
            if type.casefold() == SourceType.FS.value:
                yield from self.search_templates_iter_from_fs(source)
            elif type.casefold() == SourceType.GCS.value:
                yield from self.search_templates_iter_from_gcs(source)

    def search_templates_iter_from_fs(self, source: dict) -> Iterator[SQLTemplate]:
        """Search SQL template files from local file system

        Args:
            source (dict): Source attributes of SQL template files

        Yields:
            Iterator[SQLTemplate]: SQL template file attributes
        """
        source_type = SourceType.FS
        path_obj = pathlib.Path(source.get("path"))
        for p in path_obj.glob("**/*"):
            if (
                not re.fullmatch(rf'{source.get("regex")}', str(p))
            ) or self.is_excluded(source_type=source_type, file_path=str(p)):
                logger.debug(f"{str(p)} is skipped.")
                continue
            yield SQLTemplate(
                map_config=self._map_config,
                source_type=source_type,
                file_path=str(p),
                default_table_prefix=source.get("default_table_prefix"),
            )

    def search_templates_iter_from_gcs(self, source: dict) -> Iterator[SQLTemplate]:
        """Search SQL template files from GCS

        Args:
            source (dict): Source attributes of SQL template files

        Yields:
            Iterator[SQLTemplate]: SQL template file attributes
        """
        source_type = SourceType.GCS
        project = source.get("project")
        client = storage.Client(credentials=None, project=project)
        bucket = source.get("bucket")
        blobs = client.list_blobs(bucket)
        for blob in blobs:
            if (
                not re.fullmatch(rf'{source.get("regex")}', blob.name)
            ) or self.is_excluded(source_type=source_type, file_path=blob.name):
                logger.debug(f"{blob.name} is skipped.")
                continue
            yield SQLTemplate(
                map_config=self._map_config,
                source_type=source_type,
                file_path=blob.name,
                project=project,
                bucket=bucket,
                default_table_prefix=source.get("default_table_prefix"),
            )

    def is_excluded(self, source_type: SourceType, file_path: str) -> bool:
        """Check if the specified file is out of scope

        Args:
            source_type (SourceType): SQL template source type
            file_path (str): SQL template file path

        Returns:
            bool: Return True if the specified file is out of scope
        """
        result = False
        exclude_list = self._stairlight_config.get("exclude")
        if not exclude_list:
            return result
        for exclude in exclude_list:
            if source_type.value == exclude.get("type") and re.search(
                rf'{exclude.get("regex")}', file_path
            ):
                result = True
                break
        return result
