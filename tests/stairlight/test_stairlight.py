from src.stairlight import map_key
from src.stairlight.stairlight import (
    ResponseType,
    SearchDirection,
    StairLight,
    is_cyclic,
)


class TestResponseType:
    def test_table(self):
        assert ResponseType.TABLE.value == "table"

    def test_file(self):
        assert ResponseType.FILE.value == "file"


class TestSearchDirection:
    def test_up(self):
        assert SearchDirection.UP.value == "Upstairs"

    def test_down(self):
        assert SearchDirection.DOWN.value == "Downstairs"


class TestStairLight:
    stairlight = StairLight(config_dir="./config")
    stairlight.create_map()

    def test_has_stairlight_config(self):
        assert self.stairlight.has_stairlight_config()

    def test_mapped(self):
        assert self.stairlight.mapped

    def test_unmapped(self):
        file_keys = [
            unmapped_file.get(map_key.TEMPLATE)
            for unmapped_file in self.stairlight.unmapped
        ]
        assert file_keys

    def test_init(self, stairlight_template):
        assert (
            self.stairlight.init(prefix=stairlight_template)
            == f"./config/{stairlight_template}.yaml"
        )

    def test_check(self, mapping_template):
        assert self.stairlight.check(prefix=mapping_template).startswith(
            f"./config/{mapping_template}"
        )

    def test_up_next(self):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = self.stairlight.up(
            table_name=table_name, recursive=False, verbose=False
        )
        assert sorted(result) == [
            "PROJECT_C.DATASET_C.TABLE_C",
            "PROJECT_J.DATASET_K.TABLE_L",
            "PROJECT_d.DATASET_d.TABLE_d",
        ]

    def test_up_recursive_verbose(self):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = self.stairlight.up(table_name=table_name, recursive=True, verbose=True)
        assert sorted(
            result[table_name][SearchDirection.UP.value]["PROJECT_J.DATASET_K.TABLE_L"][
                SearchDirection.UP.value
            ].keys()
        ) == [
            "PROJECT_P.DATASET_Q.TABLE_R",
            "PROJECT_S.DATASET_T.TABLE_U",
            "PROJECT_V.DATASET_W.TABLE_X",
        ]

    def test_up_recursive_plain_table(self):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = self.stairlight.up(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.TABLE.value,
        )
        assert sorted(result) == [
            "PROJECT_C.DATASET_C.TABLE_C",
            "PROJECT_J.DATASET_K.TABLE_L",
            "PROJECT_P.DATASET_Q.TABLE_R",
            "PROJECT_S.DATASET_T.TABLE_U",
            "PROJECT_V.DATASET_W.TABLE_X",
            "PROJECT_d.DATASET_d.TABLE_d",
            "PROJECT_e.DATASET_e.TABLE_e",
        ]

    def test_up_recursive_plain_file(self, tests_dir: str):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = self.stairlight.up(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.FILE.value,
        )
        assert sorted(result) == [
            f"{tests_dir}/sql/main/cte_multi_line.sql",
            f"{tests_dir}/sql/main/cte_multi_line_params.sql",
            f"{tests_dir}/sql/main/one_line_3.sql",
        ]

    def test_down_next(self):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = self.stairlight.down(
            table_name=table_name, recursive=False, verbose=False
        )
        assert sorted(result) == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
            "PROJECT_d.DATASET_e.TABLE_f",
        ]

    def test_down_recursive_verbose(self):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = self.stairlight.down(
            table_name=table_name, recursive=True, verbose=True
        )
        assert sorted(
            result[table_name][SearchDirection.DOWN.value][
                "PROJECT_d.DATASET_e.TABLE_f"
            ][SearchDirection.DOWN.value].keys()
        ) == [
            "PROJECT_j.DATASET_k.TABLE_l",
        ]

    def test_down_recursive_plain_table(self):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = self.stairlight.down(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.TABLE.value,
        )
        assert sorted(result) == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
            "PROJECT_d.DATASET_e.TABLE_f",
            "PROJECT_j.DATASET_k.TABLE_l",
        ]

    def test_down_recursive_plain_file(self, tests_dir: str):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = self.stairlight.down(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.FILE.value,
        )
        assert sorted(result) == [
            f"{tests_dir}/sql/main/cte_multi_line.sql",
            f"{tests_dir}/sql/main/one_line_1.sql",
            "gs://stairlight/sql/cte/cte_multi_line.sql",
        ]

    def test_get_relative_map_up(self):
        table_name = "PROJECT_d.DATASET_d.TABLE_d"
        result = self.stairlight.get_relative_map(
            table_name=table_name, direction=SearchDirection.UP
        )
        assert "PROJECT_e.DATASET_e.TABLE_e" in result

    def test_get_relative_map_down(self):
        table_name = "PROJECT_A.DATASET_A.TABLE_A"
        result = self.stairlight.get_relative_map(
            table_name=table_name, direction=SearchDirection.DOWN
        )
        assert "PROJECT_A.DATASET_B.TABLE_C" in result

    def test_get_tables_by_labels_single(self):
        targets = ["Test:b"]
        result = self.stairlight.get_tables_by_labels(targets=targets)
        assert result == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
            "PROJECT_d.DATASET_e.TABLE_f",
        ]

    def test_get_tables_by_labels_double(self):
        targets = ["Test:b", "Source:gcs"]
        result = self.stairlight.get_tables_by_labels(targets=targets)
        assert result == ["PROJECT_d.DATASET_e.TABLE_f"]

    def test_is_target_found_true(self):
        targets = ["test:a", "group:c"]
        labels = {"test": "a", "category": "b", "group": "c"}
        assert self.stairlight.is_target_found(targets=targets, labels=labels)

    def test_is_target_found_false(self):
        targets = ["test:a", "category:b", "group:c", "app:d"]
        labels = {"test": "a", "category": "b", "group": "c"}
        assert not self.stairlight.is_target_found(targets=targets, labels=labels)

    def test_check_on_load(self, stairlight_save: StairLight):
        stairlight_load = StairLight(
            config_dir="./config", load_files=[stairlight_save.save_file]
        )
        assert stairlight_load.check() is None

    def test_multiple_load_and_save(self, stairlight_load_and_save: StairLight):
        actual: dict = stairlight_load_and_save.load_map_fs(
            stairlight_load_and_save.save_file
        )
        expected: dict = stairlight_load_and_save.load_map_fs(
            "tests/results/merged.json"
        )

        assert actual == expected


class TestIsCyclic:
    def test_a(self):
        node_list = [1, 2, 1, 2, 1, 2, 1, 2]
        assert is_cyclic(node_list)

    def test_b(self):
        node_list = [1, 2, 3, 2, 3, 2, 3]
        assert is_cyclic(node_list)

    def test_c(self):
        node_list = [1, 2, 3, 4, 5, 3, 4, 5]
        assert is_cyclic(node_list)

    def test_d(self):
        node_list = [1, 2, 3, 4, 5, 1, 2, 3, 4]
        assert is_cyclic(node_list)

    def test_e(self):
        node_list = [1, 2, 3, 4, 5]
        assert not is_cyclic(node_list)

    def test_f(self):
        node_list = [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_J.DATASET_K.TABLE_L",
            "PROJECT_P.DATASET_Q.TABLE_R",
            "PROJECT_S.DATASET_T.TABLE_U",
            "PROJECT_V.DATASET_W.TABLE_X",
            "PROJECT_C.DATASET_C.TABLE_C",
            "PROJECT_d.DATASET_d.TABLE_d",
            "PROJECT_J.DATASET_K.TABLE_L",
        ]
        assert is_cyclic(node_list)
