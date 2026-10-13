# EAPExpand Project - AI Coding Agent Instructions

## Project Purpose
EAPExpand extracts UML models from Enterprise Architect files (.eapx/.qea) and generates schema outputs (LinkML, Prisma, SHACL). Primary use case is processing CDISC USDM (Unified Study Data Model) definitions from CDISC DDF-RA repository.

## Architecture Overview

### Data Flow Pipeline
1. **Input**: Enterprise Architect files (.eapx = Access MDB, .qea = SQLite3)
2. **Expansion**: Extract tables to JSON files using `mdbtools` (for .eapx) or direct SQLite queries
3. **Loading**: Parse JSON into Python dataclasses ([src/eapexpand/models/eap.py](src/eapexpand/models/eap.py))
4. **Rendering**: Generate schema outputs (LinkML/Prisma/SHACL) via [src/eapexpand/render/](src/eapexpand/render/)

### Core Components
- **`src/eapexpand/models/`**: Dataclass representations of EA entities (Package, Class, Enumeration, Attribute, Connector)
- **`src/eapexpand/loader.py`**: Loads expanded JSON, builds object graph with relationships (generalizations, specializations, connectors)
- **`src/eapexpand/unpkt.py`**: General EA file processor
- **`src/eapexpand/usdm_unpkt.py`**: USDM-specific processor with CT (Controlled Terminology) enrichment
- **`src/eapexpand/render/`**: Schema generators for different output formats

### Key Patterns

#### Two Processing Modes
1. **General mode** (`expand`): Process any EA file → Excel workbook output
2. **USDM mode** (`expand --usdm` or `load_usdm`): Process CDISC USDM with CT enrichment → LinkML/Pydantic

#### File Type Detection
```python
# .eapx files: Access MDB format, requires mdbtools extraction
# .qea files: SQLite3 format, direct query via sqlite_loader.py
Path(source).is_file() → load_from_file()  # Direct SQLite
Path(source).is_dir() → load_expanded_dir()  # Pre-expanded JSON
```

#### Object Graph Construction
Classes build bidirectional relationships in [src/eapexpand/models/loader.py](src/eapexpand/models/loader.py):
- Generalizations (inheritance): `Connector.connector_type == "Generalization"`
- Specializations: Inverse of generalizations
- Classifiers: Attributes reference classes via `classifier_id`
- Package hierarchy: `parent_id` links create tree structure

## Critical Developer Workflows

### Environment Setup
```bash
# Install mdbtools (macOS only, for .eapx files)
brew install mdbtools

# Create environment and install dependencies
poetry shell && poetry install
```

### Running Conversions

**USDM Version Processing** (preferred):
```bash
# Requires: input/{version}/{version}_USDM_UML.qea and {version}_USDM_CT.xlsx
poetry run load_usdm v3.13.0
# Outputs to: output/release-{major}-{minor}/USDM_v{version}.yaml
```

**General Processing**:
```bash
# With pre-expanded directory
poetry run expand input/usdm output

# With .qea file directly
poetry run expand input/usdm.qea output --linkml

# USDM with CT enrichment
poetry run expand --usdm --usdm-ct input/USDM_CT.xlsx input/usdm_main
```

**Pull USDM from CDISC Repository**:
```bash
# Fetches .qea and _CT.xlsx files
bash scripts/pull_usdm.bash sprint-9  # Specify branch (default: main)
```

**Generate Pydantic Models from LinkML**:
```bash
poetry run gen-pydantic --meta AUTO --template-dir ./docs/pydantic_templates \
  output/release-4-0/USDM_v4.0.0.yaml > output/python/usdm_model_v4_0_0.py
```

### Testing
```bash
poetry run pytest
# Fixtures in test/fixtures/, conftest.py provides ct_file fixture
```

## Project-Specific Conventions

### USDM CT Enrichment
USDM Controlled Terminology Excel files ([src/eapexpand/usdm_unpkt.py](src/eapexpand/usdm_unpkt.py)):
- **DDF Entities&Attributes** sheet: Definitions, NCI C-codes, synonyms
- **DDF valid value sets** sheet: Codelists (enumerations) with C-codes
- Auto-injects `id` attribute for all entities (required by USDM standard)
- Requires `.env` with `CDISC_LIBRARY_API_TOKEN` for CT API access

### LinkML Generation Specifics
In [src/eapexpand/render/render_linkml.py](src/eapexpand/render/render_linkml.py):
- Entry point class is `Message` (tree_root) containing `study: Study`
- Enumerations map to LinkML PermissibleValues
- Inheritance handled via `is_a` (single) and `mixins` (multiple)
- Identifier attributes: Look for `name in IDENTIFIER_TYPES` ("id", "uuid")
- Uses `inflect.engine()` for pluralization of slot names

### Naming Conventions
- JSON files from EA export: `t_object.json`, `t_attribute.json`, `t_connector.json`, etc.
- Output directories: `release-{major}-{minor}/` (e.g., `release-4-0/`)
- USDM input files: `{version}_USDM_UML.qea`, `{version}_USDM_CT.xlsx`

### Dependencies to Note
- **mdbtools**: Required for .eapx processing (macOS: `brew install mdbtools`)
- **LinkML**: Schema generation framework (`linkml>=1.9.0`)
- **mdb-parser**: Python library for MDB file parsing
- **openpyxl**: Excel file processing for CT files
- **inflect**: Pluralization for schema generation

## Integration Points

### External APIs
- **CDISC Library API**: Fetches controlled terminology (requires token in `.env`)
- **NCI EVS API**: Optional external value set connector ([src/eapexpand/helpers/evs_connector.py](src/eapexpand/helpers/evs_connector.py))

### Output Formats
- **LinkML YAML**: Primary output, used for downstream Pydantic generation
- **Excel (XLSX)**: Tabular representation via [src/eapexpand/render/render_workbook.py](src/eapexpand/render/render_workbook.py)
- **Prisma Schema**: Database schema via [src/eapexpand/render/render_prisma.py](src/eapexpand/render/render_prisma.py)
- **SHACL**: RDF validation shapes via [src/eapexpand/render/render_shapes.py](src/eapexpand/render/render_shapes.py)

### File Structure Assumptions
```
input/{version}/           # USDM source files per version
  {version}_USDM_UML.qea
  {version}_USDM_CT.xlsx
output/release-{X}-{Y}/    # Generated schemas
docs/pydantic_templates/   # Jinja2 templates for Pydantic codegen
examples/                  # Sample .usdm.json files for testing
```

## Common Gotchas
- .eapx files require `mdbtools` installed; .qea files work out-of-box (SQLite3)
- USDM mode requires both UML file AND CT file (will error without `--usdm-ct`)
- `load_expanded_dir()` expects pre-extracted JSON files; use `scripts/expand.bash` first
- LinkML generator always creates Excel workbook as fallback if no `--linkml/--prisma/--shapes` specified
- Date format auto-detection in [src/eapexpand/models/eap.py](src/eapexpand/models/eap.py) can fail if mixed formats present
