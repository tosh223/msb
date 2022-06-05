import pytest

from src.stairlight import map_key
from src.stairlight.query import Query, solve_table_prefix


class TestSuccess:
    def test_parse_new_line(self):
        query_str = (
            "SELECT * FROM PROJECT_X.DATASET_X.TABLE_X \n"
            "INNER JOIN PROJECT_X.DATASET_X.TABLE_Y USING(ID)"
        )
        query = Query(query_str=query_str)
        results = []
        for result in query.detect_upstairs_attributes():
            results.append(result)
        assert results == [
            {
                map_key.TABLE_NAME: "PROJECT_X.DATASET_X.TABLE_X",
                map_key.LINE_NUMBER: 1,
                map_key.LINE_STRING: "SELECT * FROM PROJECT_X.DATASET_X.TABLE_X ",
            },
            {
                map_key.TABLE_NAME: "PROJECT_X.DATASET_X.TABLE_Y",
                map_key.LINE_NUMBER: 2,
                map_key.LINE_STRING: (
                    "INNER JOIN PROJECT_X.DATASET_X.TABLE_Y USING(ID)"
                ),
            },
        ]

    @pytest.mark.parametrize(
        "file, expected",
        [
            (
                "tests/sql/query/cte_one_line.sql",
                [
                    {
                        map_key.TABLE_NAME: "PROJECT_B.DATASET_B.TABLE_B",
                        map_key.LINE_NUMBER: 1,
                        map_key.LINE_STRING: (
                            "WITH c AS (SELECT test_id, col_c "
                            "FROM PROJECT_C.DATASET_C.TABLE_C WHERE 0 = 0),"
                            "d AS ("
                            "SELECT test_id, col_d "
                            "FROM PROJECT_d.DATASET_d.TABLE_d "
                            "WHERE 0 = 0) "
                            "SELECT * FROM PROJECT_B.DATASET_B.TABLE_B AS b "
                            "INNER JOIN c ON b.test_id = c.test_id "
                            "INNER JOIN d ON b.test_id = d.test_id WHERE 1 = 1"
                        ),
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_C.DATASET_C.TABLE_C",
                        map_key.LINE_NUMBER: 1,
                        map_key.LINE_STRING: (
                            "WITH c AS (SELECT test_id, col_c "
                            "FROM PROJECT_C.DATASET_C.TABLE_C WHERE 0 = 0),"
                            "d AS ("
                            "SELECT test_id, col_d "
                            "FROM PROJECT_d.DATASET_d.TABLE_d "
                            "WHERE 0 = 0) "
                            "SELECT * FROM PROJECT_B.DATASET_B.TABLE_B AS b "
                            "INNER JOIN c ON b.test_id = c.test_id "
                            "INNER JOIN d ON b.test_id = d.test_id WHERE 1 = 1"
                        ),
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_d.DATASET_d.TABLE_d",
                        map_key.LINE_NUMBER: 1,
                        map_key.LINE_STRING: (
                            "WITH c AS (SELECT test_id, col_c "
                            "FROM PROJECT_C.DATASET_C.TABLE_C WHERE 0 = 0),"
                            "d AS ("
                            "SELECT test_id, col_d "
                            "FROM PROJECT_d.DATASET_d.TABLE_d "
                            "WHERE 0 = 0) "
                            "SELECT * FROM PROJECT_B.DATASET_B.TABLE_B AS b "
                            "INNER JOIN c ON b.test_id = c.test_id "
                            "INNER JOIN d ON b.test_id = d.test_id WHERE 1 = 1"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/cte_multi_line.sql",
                [
                    {
                        map_key.TABLE_NAME: "PROJECT_B.DATASET_B.TABLE_B",
                        map_key.LINE_NUMBER: 23,
                        map_key.LINE_STRING: "    PROJECT_B.DATASET_B.TABLE_B AS b",
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_C.DATASET_C.TABLE_C",
                        map_key.LINE_NUMBER: 6,
                        map_key.LINE_STRING: "        PROJECT_C.DATASET_C.TABLE_C",
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_d.DATASET_d.TABLE_d",
                        map_key.LINE_NUMBER: 15,
                        map_key.LINE_STRING: "        PROJECT_d.DATASET_d.TABLE_d",
                    },
                ],
            ),
            (
                "tests/sql/query/nested_join.sql",
                [
                    {
                        map_key.TABLE_NAME: "PROJECT_B.DATASET_B.TABLE_B",
                        map_key.LINE_NUMBER: 4,
                        map_key.LINE_STRING: "    PROJECT_B.DATASET_B.TABLE_B AS b",
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_C.DATASET_C.TABLE_C",
                        map_key.LINE_NUMBER: 10,
                        map_key.LINE_STRING: "            PROJECT_C.DATASET_C.TABLE_C",
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_d.DATASET_d.TABLE_d",
                        map_key.LINE_NUMBER: 20,
                        map_key.LINE_STRING: (
                            "            PROJECT_d.DATASET_d.TABLE_d d"
                        ),
                    },
                    {
                        map_key.TABLE_NAME: "PROJECT_e.DATASET_e.TABLE_e",
                        map_key.LINE_NUMBER: 21,
                        map_key.LINE_STRING: (
                            "            LEFT OUTER JOIN PROJECT_e.DATASET_e.TABLE_e"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/union_same_table.sql",
                [
                    {
                        map_key.TABLE_NAME: (
                            "test_project.beam_streaming.taxirides_realtime"
                        ),
                        map_key.LINE_NUMBER: 6,
                        map_key.LINE_STRING: (
                            "    test_project.beam_streaming.taxirides_realtime"
                        ),
                    },
                    {
                        map_key.TABLE_NAME: (
                            "test_project.beam_streaming.taxirides_realtime"
                        ),
                        map_key.LINE_NUMBER: 15,
                        map_key.LINE_STRING: (
                            "    test_project.beam_streaming.taxirides_realtime"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/cte_multi_tables_01.sql",
                [
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_A",
                        map_key.LINE_NUMBER: 6,
                        map_key.LINE_STRING: "		project.dataset.table_test_A",
                    },
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_B",
                        map_key.LINE_NUMBER: 13,
                        map_key.LINE_STRING: "		project.dataset.table_test_B AS test_B",
                    },
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_C",
                        map_key.LINE_NUMBER: 19,
                        map_key.LINE_STRING: (
                            "FROM project.dataset.table_test_C AS test_C"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/cte_multi_tables_02.sql",
                [
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_A",
                        map_key.LINE_NUMBER: 6,
                        map_key.LINE_STRING: (
                            "		project.dataset.table_test_A -- table_test_B"
                        ),
                    },
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_B",
                        map_key.LINE_NUMBER: 12,
                        map_key.LINE_STRING: "		project.dataset.table_test_B AS test_B",
                    },
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_C",
                        map_key.LINE_NUMBER: 19,
                        map_key.LINE_STRING: "		project.dataset.table_test_C AS test_C",
                    },
                    {
                        map_key.TABLE_NAME: "project.dataset.table_test_D",
                        map_key.LINE_NUMBER: 26,
                        map_key.LINE_STRING: (
                            "FROM project.dataset.table_test_D AS test_D"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/backtick_each_elements.sql",
                [
                    {
                        map_key.TABLE_NAME: "dummy.dummy.my_first_dbt_model",
                        map_key.LINE_NUMBER: 4,
                        map_key.LINE_STRING: (
                            "from `dummy`.`dummy`.`my_first_dbt_model`"
                        ),
                    },
                ],
            ),
            (
                "tests/sql/query/backtick_whole_element.sql",
                [
                    {
                        map_key.TABLE_NAME: "dummy.dummy.my_first_dbt_model",
                        map_key.LINE_NUMBER: 4,
                        map_key.LINE_STRING: "from `dummy.dummy.my_first_dbt_model`",
                    },
                ],
            ),
        ],
    )
    def test_detect_upstairs_attributes(self, file, expected):
        with open(file) as f:
            query_str = f.read()
        query = Query(query_str=query_str)
        actual = []
        for result in query.detect_upstairs_attributes():
            actual.append(result)
        assert actual == expected

    @pytest.mark.parametrize(
        "table, default_table_prefix, expected",
        [
            ("DATASET_d.TABLE_d", "PROJECT_A", "PROJECT_A.DATASET_d.TABLE_d"),
            ("TABLE_d", "PROJECT_A.DATASET_A", "PROJECT_A.DATASET_A.TABLE_d"),
            ("PROJECT_d.DATASET_d.TABLE_d", "PROJECT_A", "PROJECT_d.DATASET_d.TABLE_d"),
        ],
    )
    def test_solve_table_prefix(
        self,
        table: str,
        default_table_prefix: str,
        expected: str,
    ):
        actual = solve_table_prefix(
            table=table, default_table_prefix=default_table_prefix
        )
        assert actual == expected
