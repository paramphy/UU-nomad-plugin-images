# nomad-plugin-images

**A comprehensive NOMAD plugin for parsing and visualizing hierarchical image analysis data with synthesis parameters and experimental results.**

This plugin provides parsers for multiple data organization patterns commonly used in materials science:
- Single image metadata (metadata.json + image_raw.npy)
- Manifest-based experiments (CSV with multiple images)
- **NEW:** Hierarchical samples with synthesis info and multiple experiments

---

## Features Overview

### ✨ What This Plugin Does

1. **Parses Hierarchical Sample Data**
   - Links material synthesis parameters to experimental measurements
   - Auto-discovers folder structures
   - Handles multiple experiments per sample
   - No configuration needed

2. **Generates Interactive Visualizations**
   - Automatic Plotly figure generation
   - ROI overlays (circular ROI + bounding box)
   - Interactive hover information
   - Pan/zoom/download capabilities
   - Automatic downsampling for large images

3. **Handles Unit Conversion**
   - Temperature: Celsius → Kelvin (automatic)
   - Powers: watts with proper units
   - Pressure: multiple units (mtorr, mbar)
   - Time: seconds/minutes with unit assignment

4. **Ensures Data Integrity**
   - Graceful error handling
   - Detailed logging
   - Optional fields with sensible defaults
   - Full parameter preservation

---

## Quick Start (30 seconds)

### Data Structure

```
CuSnZnS_31_123456/                  ← Sample folder
├── CuSnZnS_31.json                 ← Synthesis parameters
└── 20260323_133521/                ← Experiment folder
    ├── metadata.json               ← Acquisition settings
    └── image_raw.npy               ← Image data
```

### Upload to NOMAD

1. Organize data as above
2. Upload the sample folder to NOMAD
3. Select **HierarchicalSampleParser**
4. Click Parse
5. View: Complete entry with synthesis info + interactive image plots

**For detailed quick start:** See [`QUICK_START.md`](QUICK_START.md)

---

## Available Parsers

### 1. **HierarchicalSampleParser** (NEW)

**Purpose:** Parse hierarchical sample data with synthesis info and experiments

**Input:** Sample folder with:
- Sample synthesis JSON (root level)
- Multiple experimental subfolders (each with metadata.json + image_raw.npy)

**Output:** `SampleWithExperiments` entry linking synthesis to experiments

**Best for:** Complete experimental campaigns with material synthesis and multiple measurements

```python
hierarchical_parser = HierarchicalSampleParserEntryPoint(
    name='HierarchicalSampleParser',
    description='Parser for hierarchical sample data',
    mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
)
```

### 2. **ImageParser**

**Purpose:** Parse individual image with metadata

**Input:** `metadata.json` + `image_raw.npy` in same folder

**Output:** `SingleImageEntry` with image data and visualization

**Best for:** Standalone images or simple image acquisitions

### 3. **ImageManifestParser**

**Purpose:** Parse experiment manifest defining multiple image steps

**Input:** CSV manifest file with multiple image folders

**Output:** `ImageExperimentRun` with multiple `ImageStep` entries

**Best for:** Sequential experimental steps defined in CSV

---

## Schema Classes

### SampleWithExperiments (Top-level Entry)
```
├── name                          # Sample identifier
├── sample_folder_path            # Folder path
├── synthesis_info                # SampleSynthesisInfo
│   ├── sample_id, sample_name
│   ├── date, elements
│   ├── cu/sn/zn_source_power [W]
│   ├── source_temperature [K]
│   ├── process_temperature [K]
│   ├── chamber_pressure [mbar]
│   └── process timing [min]
│
└── experimental_results[]        # ExperimentalResult (multiple)
    ├── experiment_id
    ├── description
    └── images[]                  # ImageData
        ├── metadata              # ImageMetadata
        ├── dimensions            # ImageDimensions
        ├── roi                   # RegionOfInterest
        └── figures               # Plotly visualization
```

---

## Installation & Development

### Clone and Setup

```sh
git clone https://github.com/marzieh-saeedimasine/nomad-plugin-images.git
cd nomad-plugin-images
python3.11 -m venv .pyenv
. .pyenv/bin/activate
pip install --upgrade pip
pip install uv
uv pip install -e '.[dev]'
```

### Run Tests

```sh
# Run all tests
python -m pytest -sv tests

# Run with coverage report
uv pip install pytest-cov
python -m pytest --cov=src tests

# Run specific test
python -m pytest tests/parsers/test_hierarchical_parser.py -v
```

### Code Quality

# Check formatting
ruff format . --check
```

### Debugging

For interactive debugging of the tests, use `pytest` with the `--pdb` flag. We recommend using an IDE for debugging, e.g., _VSCode_. If that is the case, add the following snippet to your `.vscode/launch.json`:

```json
{
  "configurations": [
      {
        "name": "<descriptive tag>",
        "type": "debugpy",
        "request": "launch",
        "cwd": "${workspaceFolder}",
        "program": "${workspaceFolder}/.pyenv/bin/pytest",
        "justMyCode": true,
        "env": {
            "_PYTEST_RAISE": "1"
        },
        "args": [
            "-sv",
            "--pdb",
            "<path-to-plugin-tests>",
        ]
    }
  ]
}
```

where `<path-to-plugin-tests>` must be changed to the local path to the test module to be debugged.

The settings configuration file `.vscode/settings.json` automatically applies the linting and formatting upon saving the modified file.

### Documentation on Github pages

To view the documentation locally, install the related packages using:

```sh
uv pip install -r requirements_docs.txt
mkdocs serve
```

---

## Documentation

### User Guides
- **[QUICK_START.md](QUICK_START.md)** - 30-second guide to get started
- **[docs/how_to/hierarchical_data_parser.md](docs/how_to/hierarchical_data_parser.md)** - Complete user guide with examples

### Technical Documentation
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - What was implemented and why
- **[docs/reference/hierarchical_design.md](docs/reference/hierarchical_design.md)** - Technical architecture and design decisions

---

## Adding this plugin to NOMAD

### NOMAD Oasis

Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/staging/docs/howto/oasis/plugins_install.html) for all details on how to deploy the plugin on your NOMAD instance.

### Local NOMAD Installation

We recommend using the dedicated [`nomad-distro-dev`](https://github.com/FAIRmat-NFDI/nomad-distro-dev) repository to simplify the process. Please refer to that repository for detailed instructions.

---

## Publishing

To publish this plugin to PyPI:

1. Set up your PyPI account and configure credentials
2. Uncomment the `deploy` job in `.github/workflows/publish.yml`
3. Create a release on GitHub
4. The workflow will automatically publish to PyPI

For detailed instructions, see [How to Publish a Python Package to PyPI](https://realpython.com/pypi-publish-python-package/).

### Template Updates

We use [`cruft`](https://github.com/cruft/cruft) to update the project based on template changes. To check for updates locally:

```sh
cruft update
```

More details on [`cruft` website](https://cruft.github.io/cruft/#updating-a-project).

---

## Main Contributors

| Name                  | Email                             |
|---                    |---                                |
| Marzieh Saeedimasine  | marzieh.saeedimasine@gmail.com   |

---

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
