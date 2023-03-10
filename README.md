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
    ```shell
    $ poetry run expand input/usdm output
    ``` 

For the USDM content we can merge (depending on formatting issues, etc) the definitions/codelists from the CT
```shell
$ poetry run expand --usdm --usdm-ct input/USDM_CT.xlsx input/usdm_main
```


## Pulling a version of the USDM

There's a helper script to pull a version of the USDM EAP file (and CT)

It takes an optional argument to point at the branch; if not specified it will pull the `main` branch; for example to retrieve the current version for `sprint-9` run it as follows:
```
$ /bin/bash scripts/pull_usdm.bash sprint-9
```

