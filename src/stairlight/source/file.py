import pathlib
import re
from typing import Iterator, Optional

from .. import config_key
from ..config import get_config_value
from .base import Template, TemplateSource, TemplateSourceType


class FileTemplate(Template):
    def __init__(
        self,
        mapping_config: dict,
        key: str,
        source_type: Optional[TemplateSourceType] = TemplateSourceType.FILE,
        bucket: Optional[str] = None,
        project: Optional[str] = None,
        default_table_prefix: Optional[str] = None,
    ):
        super().__init__(
            mapping_config=mapping_config,
            key=key,
            source_type=source_type,
            bucket=bucket,
            project=project,
            default_table_prefix=default_table_prefix,
        )
        self.uri = self.get_uri()

    def get_uri(self) -> str:
        """Get uri from file path

        Returns:
            str: uri
        """
        return str(pathlib.Path(self.key).resolve())

    def get_template_str(self) -> str:
        """Get template string that read from a file in local file system

        Returns:
            str: Template string
        """
        with open(self.key) as f:
            return f.read()


class FileTemplateSource(TemplateSource):
    def __init__(
        self, stairlight_config: dict, mapping_config: dict, source_attributes: dict
    ) -> None:
        super().__init__(
            stairlight_config=stairlight_config, mapping_config=mapping_config
        )
        self.source_attributes = source_attributes
        self.source_type = TemplateSourceType.FILE

    def search_templates_iter(self) -> Iterator[Template]:
        """Search SQL template files from local file system

        Args:
            source (dict): Source attributes of SQL template files

        Yields:
            Iterator[SQLTemplate]: SQL template file attributes
        """
        path = get_config_value(
            key=config_key.FILE_SYSTEM_PATH,
            target=self.source_attributes,
            fail_if_not_found=True,
            enable_logging=False,
        )
        default_table_prefix = get_config_value(
            key=config_key.DEFAULT_TABLE_PREFIX,
            target=self.source_attributes,
            fail_if_not_found=False,
            enable_logging=False,
        )
        regex = get_config_value(
            key=config_key.REGEX,
            target=self.source_attributes,
            fail_if_not_found=True,
            enable_logging=False,
        )

        path_obj = pathlib.Path(path)
        for p in path_obj.glob("**/*"):
            if (
                not re.fullmatch(
                    rf"{regex}",
                    str(p),
                )
            ) or self.is_excluded(source_type=self.source_type, key=str(p)):
                self.logger.debug(f"{str(p)} is skipped.")
                continue

            yield FileTemplate(
                mapping_config=self._mapping_config,
                key=str(p),
                source_type=self.source_type,
                default_table_prefix=default_table_prefix,
            )
