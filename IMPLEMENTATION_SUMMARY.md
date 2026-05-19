# Implementation Summary: Hierarchical Sample Data Parser

## Overview

A comprehensive hierarchical data parser has been implemented to handle materials science experiments with multi-level data structures. This enables users to upload complete experimental campaigns where each sample's synthesis information is linked to multiple experimental measurements with associated imagery.

## What Was Implemented

### 1. **New Schema Classes** (`src/nomad_plugin_images/schema_packages/image_analysis.py`)

#### SampleSynthesisInfo
- Captures all material synthesis parameters
- Fields: sample_id, sample_name, date, elements
- Deposition parameters: Cu/Sn/Zn source power (watts)
- Process parameters: temperature (Kelvin), pressure (various units), timing (minutes)
- Unit conversion: Celsius → Kelvin, strings → floats with proper units

#### ExperimentalResult
- Groups images from one experimental measurement session
- Fields: experiment_id, description, images (list of ImageData)
- Acts as intermediate level between sample and individual images

#### SampleWithExperiments (Top-level Entry)
- Links synthesis info to multiple experimental measurements
- Extends `PlotSection` + `EntryData` for visualization support
- Fields: name, sample_folder_path, synthesis_info, experimental_results
- Inherits image visualization capabilities

### 2. **New Parser** (`src/nomad_plugin_images/parsers/hierarchical_parser.py`)

#### HierarchicalSampleParser
- **Mainfile Detection:** Matches JSON files in sample folders (regex configurable)
- **Hierarchical Discovery:**
  1. Reads sample-level synthesis JSON
  2. Discovers experimental subfolders
  3. Parses metadata.json from each experimental folder
  4. Generates visualizations

#### Key Features:
- **Automatic Structure Discovery:** Recursively finds all experimental folders
- **Unit Conversion:** Celsius→Kelvin, strings→floats with proper units
- **Image Visualization:** Plotly plots with ROI overlays (circular + bounding box)
- **Downsampling:** Automatically downsample large images (>1000px) for faster rendering
- **Robust Error Handling:** Continues on errors, logs details for debugging
- **Folder-level Discovery:** No explicit manifest required

### 3. **Entry Point Registration**

**pyproject.toml:**
```toml
[project.entry-points.'nomad.plugin']
hierarchical_parser = "nomad_plugin_images.parsers:hierarchical_parser"
```

**src/nomad_plugin_images/parsers/__init__.py:**
- New `HierarchicalSampleParserEntryPoint` class
- Configured with appropriate regex patterns
- Registered as `hierarchical_parser`

### 4. **Comprehensive Documentation**

#### User Guide (`docs/how_to/hierarchical_data_parser.md`)
- Data structure explanation with examples
- Field descriptions for both JSON files
- Schema class hierarchy
- Usage instructions
- Visualization capabilities
- Troubleshooting guide

#### Technical Design (`docs/reference/hierarchical_design.md`)
- Architecture overview
- Implementation details
- File structure
- Parser logic flow
- Unit conversion strategy
- Error handling approach
- Performance considerations
- Security considerations
- Future enhancement roadmap

### 5. **Comprehensive Tests** (`tests/parsers/test_hierarchical_parser.py`)

Test coverage includes:
- Parser initialization
- Complete hierarchical structure parsing
- Synthesis parameter parsing with unit conversion
- Image metadata parsing within experiments
- Real data integration tests
- Multi-experiment handling

**Key Test Cases:**
```python
test_hierarchical_parser_initialization()
test_parse_hierarchical_sample()
test_parse_synthesis_parameters()
test_parse_image_metadata_in_experiments()
test_parse_real_sample_data()
```

## Data Structure Supported

```
Sample Folder (Top Level)
└── CuSnZnS_31_123456/
    ├── CuSnZnS_31.json                    # Synthesis parameters
    ├── 20260323_133521/                   # Experiment 1
    │   ├── metadata.json                  # Acquisition metadata
    │   └── image_raw.npy                  # Image data
    └── 20260323_140000/                   # Experiment 2
        ├── metadata.json
        └── image_raw.npy
```

## NOMAD Archive Output

When parsed, creates a hierarchical NOMAD entry:

```
SampleWithExperiments
├── name: "CuSnZnS_31_123456"
├── synthesis_info: SampleSynthesisInfo
│   ├── sample_id, sample_name, date, elements
│   ├── cu_source_power, sn_source_power, zn_source_power [watts]
│   ├── pressure, temperatures [K], etc.
│   └── ... (all synthesis parameters)
│
└── experimental_results: ExperimentalResult[] (multiple)
    ├── experiment_id: "20260323_133521"
    ├── images: ImageData[]
    │   ├── metadata: ImageMetadata (exposure, gain, bit depth)
    │   ├── dimensions: ImageDimensions (height, width, channels)
    │   ├── roi: RegionOfInterest (with bounding box)
    │   └── figures: PlotlyFigure[] (interactive visualization)
    │
    └── [Another experiment...]
```

## Features

### Hierarchical Support
✅ Multi-level data structure (sample → experiments → images)
✅ Automatic folder discovery
✅ No explicit manifest required

### Visualization
✅ Automatic Plotly figure generation
✅ ROI overlay (circular + bounding box)
✅ Interactive hover information
✅ Downsampling for large images
✅ Image pan/zoom/download capabilities

### Unit Handling
✅ Temperature conversion (°C → K)
✅ Power values with unit assignment (watts)
✅ Pressure in multiple units (mtorr, mbar)
✅ Time in minutes/seconds with proper units

### Data Integrity
✅ Graceful error handling
✅ Continues on individual failures
✅ Detailed logging for debugging
✅ Optional fields handled with defaults

### Extensibility
✅ Configurable regex patterns for file matching
✅ Support for different naming schemes
✅ Ready for additional file formats (HDF5, NetCDF)

## Files Modified/Created

### Modified Files
1. `src/nomad_plugin_images/schema_packages/image_analysis.py`
   - Added: `SampleSynthesisInfo` class
   - Added: `ExperimentalResult` class
   - Added: `SampleWithExperiments` class (top-level entry)

2. `src/nomad_plugin_images/parsers/__init__.py`
   - Added: `HierarchicalSampleParserEntryPoint` class
   - Added: `hierarchical_parser` entry point

3. `pyproject.toml`
   - Added: `hierarchical_parser` to plugin entry-points

### New Files
1. `src/nomad_plugin_images/parsers/hierarchical_parser.py`
   - Main parser implementation (290+ lines)
   - `HierarchicalSampleParser` class
   - Helper method `_parse_experiment_folder()`

2. `docs/how_to/hierarchical_data_parser.md`
   - User guide and documentation

3. `docs/reference/hierarchical_design.md`
   - Technical design and architecture document

4. `tests/parsers/test_hierarchical_parser.py`
   - Comprehensive test suite (280+ lines)
   - 5+ test cases with fixtures

## Usage Example

### Step 1: Prepare Data
```
CuSnZnS_31_123456/
├── CuSnZnS_31.json
└── 20260323_133521/
    ├── metadata.json
    └── image_raw.npy
```

### Step 2: Upload to NOMAD
- Select folder: `CuSnZnS_31_123456/`
- Select parser: `HierarchicalSampleParser`
- Click "Parse"

### Step 3: Explore Results
- NOMAD creates: `SampleWithExperiments` entry
- Contains: Synthesis info + experimental measurements
- View: Interactive plots with ROI overlays
- Access: All parameters and metadata

### Step 4: Programmatic Access (Python)
```python
from nomad_plugin_images.parsers.hierarchical_parser import HierarchicalSampleParser
from nomad.datamodel import EntryArchive

parser = HierarchicalSampleParser(
    name='HierarchicalSampleParser',
    description='Parse hierarchical samples',
    mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
)

archive = EntryArchive()
parser.parse('path/to/CuSnZnS_31.json', archive, logger)

# Access data
sample = archive.data
print(f"Synthesis info: {sample.synthesis_info}")
print(f"Experiments: {len(sample.experimental_results)}")
```

## Benefits

1. **Complete Data Traceability**
   - Links synthesis parameters to experimental results
   - Full provenance tracking
   - Reproducibility

2. **Automatic Visualization**
   - No manual plot generation needed
   - Interactive exploration in NOMAD
   - ROI overlay for validation

3. **Scalability**
   - Handles multiple experiments per sample
   - Automatic folder discovery
   - No configuration needed

4. **Integration**
   - Works with existing image parsers
   - Compatible with NOMAD schema
   - Extensible for new data types

5. **Data Quality**
   - Unit conversion ensures consistency
   - Type safety (numbers, units)
   - Metadata preservation

## Testing

Run tests with:
```bash
python -m pytest tests/parsers/test_hierarchical_parser.py -v
```

Tests include:
- ✅ Parser initialization
- ✅ Hierarchical structure parsing
- ✅ Synthesis parameter extraction
- ✅ Image metadata parsing
- ✅ Unit conversion
- ✅ Real data integration
- ✅ Error handling

## Future Work

### Phase 2 (Immediate)
- [ ] XRF analysis data integration
- [ ] Multi-image per experiment support
- [ ] Statistical analysis (mean, std)

### Phase 3 (Short-term)
- [ ] Spectral data visualization
- [ ] Comparison plots across experiments
- [ ] Automated feature detection

### Phase 4 (Medium-term)
- [ ] ML integration for analysis
- [ ] Batch processing
- [ ] Advanced 3D visualization

## Conclusion

The hierarchical sample data parser provides a complete solution for managing complex, multi-level materials science experiment data. It automatically discovers folder structures, parses synthesis and experimental metadata, converts units appropriately, generates interactive visualizations, and creates proper NOMAD archive entries with full traceability.

The implementation is robust, well-documented, thoroughly tested, and ready for production use.
