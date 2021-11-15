# StairLight

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![CI](https://github.com/tosh2230/stairlight/actions/workflows/ci.yml/badge.svg)](https://github.com/tosh2230/stairlight/actions/workflows/ci.yml)

StairLight is a table-level data lineage tool, detects table dependencies from 'Transform' SQL files such as plain SELECT, 'CREATE TABLE AS SELECT', 'CREATE VIEW AS SELECT'.

## Installation

```sh
# WIP...
$ pip install stairlight
```

## Getting Started

There are three steps to use.

```sh
# Step1: Initialize and set data location settings
$ stairlight init
'./stairlight.yaml' has created.
Please edit it to set your data sources.

# Step2: Map SQL files and tables
$ stairlight check
'./mapping_yyyyMMddhhmmss.yaml' has created.
Please map undefined tables and parameters, and append to your latest file.

# Step3: Get a table dependency map
$ stairlight
```

## Description

### Input

- SQL files
- Configuration files (YAML)
    - stairlight.yaml: SQL file locations and include/exclude files.
    - mapping.yaml: Mapping SQL files and tables.

### Output

- Dependency map file (JSON)

    ```json
    {
        "PROJECT_d.DATASET_e.TABLE_f": {
            "PROJECT_j.DATASET_k.TABLE_l": {
                "type": "fs",
                "file": "tests/sql/main/test_e.sql",
                "uri": "/foo/bar/stairlight/tests/sql/main/test_e.sql",
                "line": 1,
                "line_str": "SELECT * FROM PROJECT_j.DATASET_k.TABLE_l WHERE 1 = 1"
            },
            "PROJECT_g.DATASET_h.TABLE_i": {
                "type": "gcs",
                "file": "sql/test_b/test_b.sql",
                "uri": "gs://baz/sql/test_b/test_b.sql",
                "line": 23,
                "line_str": "    PROJECT_g.DATASET_h.TABLE_i AS b",
                "bucket": "stairlight"
            },
            "PROJECT_C.DATASET_C.TABLE_C": {
                "type": "gcs",
                "file": "sql/test_b/test_b.sql",
                "uri": "gs://baz/sql/test_b/test_b.sql",
                "line": 6,
                "line_str": "        PROJECT_C.DATASET_C.TABLE_C",
                "bucket": "stairlight"
            },
            "PROJECT_d.DATASET_d.TABLE_d": {
                "type": "gcs",
                "file": "sql/test_b/test_b.sql",
                "uri": "gs://baz/sql/test_b/test_b.sql",
                "line": 15,
                "line_str": "        PROJECT_d.DATASET_d.TABLE_d",
                "bucket": "stairlight"
            }
        },
        "PROJECT_j.DATASET_k.TABLE_l": {
            "PROJECT_d.DATASET_e.TABLE_f": {
                "type": "fs",
                "file": "tests/sql/main/test_d.sql",
                "uri": "/foo/bar/stairlight/tests/sql/main/test_d.sql",
                "line": 1,
                "line_str": "SELECT * FROM PROJECT_d.DATASET_e.TABLE_f WHERE 1 = 1"
            }
        },
        "PROJECT_d.DATASET_d.TABLE_d": {
            "PROJECT_e.DATASET_e.TABLE_e": {
                "type": "fs",
                "file": "tests/sql/main/test_f.sql",
                "uri": "/foo/bar/stairlight/tests/sql/main/test_f.sql",
                "line": 1,
                "line_str": "SELECT * FROM PROJECT_e.DATASET_e.TABLE_e WHERE 1 = 1"
            }
        },
    }
    ```

## Configuration

Config files used for unit test in CI can be found [here](https://github.com/tosh2230/stairlight/tree/main/config).

### stairlight.yaml

'stairlight.yaml' is for setting up StairLight itself.

It is responsible for specifying the destination of SQL files to be read, and for specifying the prefix of the mapping file.

SQL files can be read from the following storage.

- Local file system(with pathlib module)
- Google Cloud Storage

### mapping.yaml

'stairlight.yaml' is used to define the correspondence between SQL files and tables.

The `params` attribute allows you to reflect settings in [jinja](https://jinja.palletsprojects.com/) template variables embedded in SQL files.

Multiple settings in a SQL file using jinja template will be considered as a query with the number of settings defined. If multiple settings are applied to a SQL file using a jinja template, the file will be read as if there were the same number of files as the number of settings.

## Sub-command and options

```
$ stairlight --help
usage: stairlight [-h] [-c CONFIG] [-s SAVE | -l LOAD] {init,check,up,down} ...

A table-level data lineage tool, detects table dependencies from 'Transform' SQL files. Without positional
arguments, return a table dependency map as JSON format.

positional arguments:
  {init,check,up,down}
    init                create a new StairLight configuration file.
    check               create a new configuration file about undefined mappings.
    up                  return upstream ( table | SQL file ) list
    down                return downstream ( table | SQL file ) list

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        directory path contains StairLight configuration files.
  -s SAVE, --save SAVE  save results to a file
  -l LOAD, --load LOAD  load results from a file
```

### init

`init` creates a new StairLight configuration file.

```
$ stairlight init --help
usage: stairlight init [-h] [-c CONFIG] [-s SAVE | -l LOAD]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        directory path contains StairLight configuration files.
  -s SAVE, --save SAVE  save results to a file
  -l LOAD, --load LOAD  load results from a file
```

### check

`check` creates a new configuration file about undefined mappings.
The option specification is the same as `init`.

### up

`up` Outputs a list of tables or SQL files located upstream from the specified table.

- Recursive option(`-r` or `--recursive`) is set, StairLight will find upstream tables recursively and output as a list.
- Verbose option(`-v` or `--verbose`) is set, StairLight will add detailed information and output it as a dict.

```sh
$ stairlight up --help
usage: stairlight up [-h] [-c CONFIG] [-s SAVE | -l LOAD] -t TABLE [-o {table,file}] [-v] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        directory path contains StairLight configuration files.
  -s SAVE, --save SAVE  save results to a file
  -l LOAD, --load LOAD  load results from a file
  -t TABLE, --table TABLE
                        table name that StairLight searches for, can be specified multiple times.
  -o {table,file}, --output {table,file}
                        output type
  -v, --verbose         return verbose results
  -r, --recursive       search recursive
```

### down

`down` Outputs a list of tables or SQL files located downstream from the specified table.
The option specification is the same as `up`.
