# Expand an EAPX

## Pre-requisites:
1. Install mdbtools
1. Install poetry
    ```shell
    curl -sSL https://install.python-poetry.org | python3 -
    ```
1. Install the environment
    ```shell
    $ poetry shell
    $ poetry install
    ```

## Running
1. Use the script to expand the files
```shell
$ scripts/expand.bash USDM_UML.eapx usdm
```
2. Convert the output location 
```
$ poetry run expand usdm output
``` 

