from src.stairlight.stairlight import (
    ResponseType,
    SearchDirection,
    StairLight,
    is_cyclic,
)


class TestResponseType:
    def test_table(self):
        type_table = ResponseType.TABLE
        assert str(type_table) == "TABLE"

    def test_file(self):
        type_file = ResponseType.FILE
        assert str(type_file) == "FILE"


class TestSearchDirection:
    def test_up(self):
        direction = SearchDirection.UP
        assert str(direction) == "UP"

    def test_down(self):
        direction = SearchDirection.DOWN
        assert str(direction) == "DOWN"


class TestProperty:
    def test_mapped(self, stairlight):
        assert len(stairlight.mapped) > 0

    def test_unmapped(self, stairlight):
        file_keys = [
            unmapped_file.get("template_file") for unmapped_file in stairlight.unmapped
        ]
        assert len(file_keys) > 0


class TestSuccess:
    def test_init(self, stairlight, stairlight_template):
        assert (
            stairlight.init(prefix=stairlight_template)
            == f"./config/{stairlight_template}.yaml"
        )

    def test_check(self, stairlight, mapping_template):
        assert stairlight.check(prefix=mapping_template).startswith(
            f"./config/{mapping_template}"
        )

    def test_check_on_load(self, stairlight):
        stairlight_load = StairLight(
            config_dir="./config", load_file=stairlight.save_file
        )
        assert stairlight_load.check() is None

    def test_up_next(self, stairlight):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = stairlight.up(table_name=table_name, recursive=False, verbose=False)
        assert sorted(result) == [
            "PROJECT_C.DATASET_C.TABLE_C",
            "PROJECT_J.DATASET_K.TABLE_L",
            "PROJECT_d.DATASET_d.TABLE_d",
        ]

    def test_up_recursive_verbose(self, stairlight):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = stairlight.up(table_name=table_name, recursive=True, verbose=True)
        assert sorted(
            result[table_name]["upstairs"]["PROJECT_J.DATASET_K.TABLE_L"][
                "upstairs"
            ].keys()
        ) == [
            "PROJECT_P.DATASET_Q.TABLE_R",
            "PROJECT_S.DATASET_T.TABLE_U",
            "PROJECT_V.DATASET_W.TABLE_X",
        ]

    def test_up_recursive_plain_table(self, stairlight):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = stairlight.up(
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

    def test_up_recursive_plain_file(self, stairlight, tests_dir):
        table_name = "PROJECT_D.DATASET_E.TABLE_F"
        result = stairlight.up(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.FILE.value,
        )
        assert sorted(result) == [
            f"{tests_dir}/sql/main/test_b.sql",
            f"{tests_dir}/sql/main/test_c.sql",
            f"{tests_dir}/sql/main/test_f.sql",
        ]

    def test_down_next(self, stairlight):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = stairlight.down(table_name=table_name, recursive=False, verbose=False)
        assert sorted(result) == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
            "PROJECT_d.DATASET_e.TABLE_f",
        ]

    def test_down_recursive_verbose(self, stairlight):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = stairlight.down(table_name=table_name, recursive=True, verbose=True)
        assert sorted(
            result[table_name]["downstairs"]["PROJECT_d.DATASET_e.TABLE_f"][
                "downstairs"
            ].keys()
        ) == [
            "PROJECT_j.DATASET_k.TABLE_l",
        ]

    def test_down_recursive_plain_table(self, stairlight):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = stairlight.down(
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

    def test_down_recursive_plain_file(self, stairlight, tests_dir):
        table_name = "PROJECT_C.DATASET_C.TABLE_C"
        result = stairlight.down(
            table_name=table_name,
            recursive=True,
            verbose=False,
            response_type=ResponseType.FILE.value,
        )
        assert sorted(result) == [
            f"{tests_dir}/sql/main/test_b.sql",
            f"{tests_dir}/sql/main/test_d.sql",
            "gs://stairlight/sql/test_b/test_b.sql",
        ]

    def test_get_relative_map_up(self, stairlight):
        table_name = "PROJECT_d.DATASET_d.TABLE_d"
        result = stairlight.get_relative_map(
            table_name=table_name, direction=SearchDirection.UP
        )
        assert "PROJECT_e.DATASET_e.TABLE_e" in result

    def test_get_relative_map_down(self, stairlight):
        table_name = "PROJECT_A.DATASET_A.TABLE_A"
        result = stairlight.get_relative_map(
            table_name=table_name, direction=SearchDirection.DOWN
        )
        assert "PROJECT_A.DATASET_B.TABLE_C" in result

    def test_get_tables_by_labels_single(self, stairlight):
        targets = ["test:b"]
        result = stairlight.get_tables_by_labels(targets=targets)
        assert result == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
            "PROJECT_d.DATASET_e.TABLE_f",
        ]

    def test_get_tables_by_labels_double(self, stairlight):
        targets = ["test:b", "source:gcs"]
        result = stairlight.get_tables_by_labels(targets=targets)
        assert result == ["PROJECT_d.DATASET_e.TABLE_f"]

    def test_is_target_found_true(self, stairlight):
        targets = ["test:a", "group:c"]
        labels = {"test": "a", "category": "b", "group": "c"}
        assert stairlight.is_target_found(targets=targets, labels=labels)

    def test_is_target_found_false(self, stairlight):
        targets = ["test:a", "category:b", "group:c", "app:d"]
        labels = {"test": "a", "category": "b", "group": "c"}
        assert not stairlight.is_target_found(targets=targets, labels=labels)


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
