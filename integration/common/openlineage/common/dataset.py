# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Optional, Dict

from openlineage.common.models import DbTableSchema, DbColumn
from openlineage.client.facet import BaseFacet, DataSourceDatasetFacet, \
    DocumentationDatasetFacet, SchemaDatasetFacet, SchemaField
from openlineage.client.run import Dataset as OpenLineageDataset, InputDataset, OutputDataset


class Source:
    def __init__(
            self,
            scheme: Optional[str] = None,
            authority: Optional[str] = None,
            connection_url: Optional[str] = None,
            name: Optional[str] = None
    ):
        self.scheme = scheme
        self.authority = authority
        self._name = name
        self.connection_url = connection_url

        if (scheme or authority) and name:
            raise RuntimeError('scheme + authority and namespace are exclusive options')

    def __eq__(self, other):
        return self.name == other.name and \
               self.connection_url == other.connection_url

    def __repr__(self):
        authority = '//' + self.authority if self.authority else ''
        return f"Source({self.scheme!r}:{authority} - {self.connection_url!r})"

    @property
    def name(self) -> str:
        if self._name:
            return self._name
        if self.authority:
            return f'{self.scheme}://{self.authority}'
        return f'{self.scheme}'


class Field:
    def __init__(self, name: str, type: str,
                 tags: List[str] = None, description: str = None):
        self.name = name
        self.type = type
        self.tags = tags
        self.description = description

        if self.tags is None:
            self.tags = []

    @staticmethod
    def from_column(column: DbColumn):
        return Field(
            name=column.name,
            type=column.type,
            description=column.description
        )

    def __eq__(self, other):
        return self.name == other.name and \
               self.type == other.type and \
               self.tags == other.tags and \
               self.description == other.description

    def __repr__(self):
        return f"Field({self.name!r},{self.type!r}, \
                       {self.tags!r},{self.description!r})"


class Dataset:
    def __init__(
            self,
            source: Source,
            name: str, fields: List[Field] = None,
            description: Optional[str] = None,
            custom_facets: Dict[str, BaseFacet] = None,
            input_facets: Dict[str, BaseFacet] = None,
            output_facets: Dict[str, BaseFacet] = None
    ):
        if fields is None:
            fields = []
        if custom_facets is None:
            custom_facets = {}
        if input_facets is None:
            input_facets = {}
        if output_facets is None:
            output_facets = {}
        self.source = source
        self.name = name
        self.fields = fields
        self.description = description
        self.custom_facets = custom_facets
        self.input_facets = input_facets
        self.output_facets = output_facets

    @staticmethod
    def from_table(source: Source,
                   table_name: str,
                   schema_name: str = None,
                   database_name: str = None):
        return Dataset(
            name=Dataset._to_name(
                schema_name=schema_name,
                table_name=table_name,
                database_name=database_name
            ),
            source=source
        )

    @staticmethod
    def from_table_schema(
            source: Source,
            table_schema: DbTableSchema,
            database_name: str = None
    ):
        return Dataset(
            name=Dataset._to_name(
                schema_name=table_schema.schema_name,
                table_name=table_schema.table_name.name,
                database_name=database_name
            ),
            source=source,
            fields=[
                # We want to maintain column order using ordinal position.
                Field.from_column(column) for column in sorted(
                    table_schema.columns, key=lambda x: x.ordinal_position
                )
            ]
        )

    @staticmethod
    def _to_name(table_name: str, schema_name: str = None, database_name: str = None):
        # Prefix the table name with database and schema name using
        # the format: {database_name}.{table_schema}.{table_name}.
        name = [table_name]
        if schema_name is not None:
            name = [schema_name] + name
        if database_name is not None:
            name = [database_name] + name

        return ".".join(name)

    def __eq__(self, other):
        return self.source == other.source and \
               self.name == other.name and \
               self.fields == other.fields and \
               self.description == other.description

    def __repr__(self):
        return f"Dataset({self.source!r},{self.name!r}, \
                         {self.fields!r},{self.description!r})"

    def to_openlineage_dataset(self) -> OpenLineageDataset:
        facets = {
            "dataSource": DataSourceDatasetFacet(
                self.source.name,
                self.source.connection_url
            )
        }
        if self.description:
            facets.update({
                "documentation": DocumentationDatasetFacet(
                    description=self.description
                )
            })

        if self.fields is not None and len(self.fields):
            facets.update({
                "schema": SchemaDatasetFacet(
                    fields=[
                        SchemaField(field.name, field.type, field.description)
                        for field in self.fields
                    ]
                )
            })

        if self.custom_facets:
            facets.update(self.custom_facets)

        if len(self.input_facets):
            return InputDataset(
                namespace=self.source.name,
                name=self.name,
                facets=facets,
                inputFacets=self.input_facets
            )
        if len(self.output_facets):
            return OutputDataset(
                namespace=self.source.name,
                name=self.name,
                facets=facets,
                outputFacets=self.output_facets
            )

        return OpenLineageDataset(
            namespace=self.source.name,
            name=self.name,
            facets=facets
        )
