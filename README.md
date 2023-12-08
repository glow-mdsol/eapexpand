# Expand an EAPX or QEA File

## Installation:

### Pre-requisites (EAPX)
1. Install mdbtools
    ```shell
    $ brew install mdbtools
    ```

### Install
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
* Convert the output location (general EAPX)
   * With an expanded EAPX file (see below)
       ```shell
       $ poetry run expand input/usdm output
       ``` 
   * With a QEA file
      ```shell
      $ poetry run expand input/usdm.qea output
      ```
* Convert the output location (USDM EAPX/QEA)
  * For the USDM content we can merge (depending on formatting issues, etc) the definitions/codelists from the CT
     ```shell
     $ poetry run expand --usdm --usdm-ct input/USDM_CT.xlsx input/usdm_main
     ```

## Output Types
### XLSX
A Excel formatted spreadsheet will be generated for the model, normalising the entities and attributes into a tabular format.

### LinkML
A LinkML formatted YAML file will be generated for the model (Still a WIP).


## Helpers

### Pulling a version of the CDISC USDM

To pull a version of the USDM EAP file (and CT)

It takes an optional argument to point at the branch; if not specified it will pull the `main` branch; for example to retrieve the current version for `sprint-9` run it as follows:
```
$ /bin/bash scripts/pull_usdm.bash sprint-9
```

### Expanding a EAPX file
Use the following script to expand an eapx file
    ```shell
    $ scripts/expand.bash USDM_UML.eapx usdm
    ```
It will generate a folder in the `input` directory named `usdm` with the expanded content (JSON files)


