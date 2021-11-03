import json


class TestProperty:
    def test_maps(self, stair_light):
        assert len(stair_light.maps) > 0

    def test_undefined_files(self, stair_light):
        file_keys = [
            undefined_file.get("template_file")
            for undefined_file in stair_light.undefined_files
        ]
        assert sorted(file_keys) == [
            "tests/sql/test_a.sql",
            "tests/sql/test_b.sql",
            "tests/sql/test_c.sql",
        ]


class TestSuccess:
    def test_all(self, stair_light):
        assert json.loads(stair_light.all()) == stair_light.maps

    def test_up(self, stair_light):
        result = stair_light.up(table_name="PROJECT_D.DATASET_E.TABLE_F")
        assert sorted(json.loads(result).keys()) == [
            "PROJECT_C.DATASET_C.TABLE_C",
            "PROJECT_J.DATASET_K.TABLE_L",
            "PROJECT_d.DATASET_d.TABLE_d",
        ]

    def test_down(self, stair_light):
        result = stair_light.down(table_name="PROJECT_C.DATASET_C.TABLE_C")
        assert sorted(json.loads(result).keys()) == [
            "PROJECT_D.DATASET_E.TABLE_F",
            "PROJECT_G.DATASET_H.TABLE_I",
        ]
