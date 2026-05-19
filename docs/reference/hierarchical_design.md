# Hierarchical Sample Data Parser - Technical Design

## Implementation Overview

This document describes the technical architecture of the hierarchical data parser system for materials science data with synthesis parameters and experimental measurements.

## Problem Statement

### Original Issue
Materials science experiments often have a hierarchical data structure:
1. **Sample Level** - Synthesis parameters (Cu/Sn/Zn deposition, temperature, pressure, etc.)
2. **Experiment Level** - Individual measurements on that sample (image acquisitions)
3. **Measurement Level** - Raw data (images, spectra, etc.)

**Previous Solution Limitations:**
- Image parser only handled flat metadata.json files
- Manifest parser assumed sequential steps in a single experiment
- No way to link multiple experimental measurements to a sample's synthesis info
- Sample-level JSON files were not integrated into the data model

### Proposed Solution
Create a hierarchical parser that:
1. Discovers the folder structure automatically
2. Reads sample-level synthesis JSON
3. Traverses subfolders for experimental data
4. Creates proper NOMAD relationships
5. Generates visualizations at all levels

## Architecture

### Parser Chain

```
Mainfile: CuSnZnS_31.json (in CuSnZnS_31_123456/)
    ↓
HierarchicalSampleParser.parse()
    ↓
├─ Parse CuSnZnS_31.json
│   ↓
│   Create SampleSynthesisInfo
│   ├─ sample_id, sample_name, date, elements
│   ├─ Source powers (Cu, Sn, Zn)
│   ├─ Temperatures (°C → K conversion)
│   ├─ Pressures (mtorr, mbar)
│   └─ Process timing (minutes)
│
├─ Discover experimental subfolders
│   ↓
│   For each subfolder with metadata.json:
│   ├─ Create ExperimentalResult
│   │   ├─ experiment_id (folder name)
│   │   └─ images (list of ImageData)
│   │       ↓
│   │       For metadata.json in subfolder:
│   │       ├─ Create ImageData
│   │       ├─ Parse ImageMetadata
│   │       ├─ Parse ImageDimensions
│   │       ├─ Parse RegionOfInterest
│   │       └─ Generate Plotly visualization
│   │
│   └─ Repeat for all experimental folders
│
└─ Create SampleWithExperiments entry
    ├─ name, sample_folder_path
    ├─ synthesis_info (SampleSynthesisInfo)
    └─ experimental_results (list of ExperimentalResult)
        ↓
        Store in archive.data
```

### Schema Class Hierarchy

```python
# Base classes
PlotSection, EntryData, ArchiveSection

# New classes
├── SampleSynthesisInfo(ArchiveSection)
│   └── Captures all synthesis parameters
│
├── ExperimentalResult(ArchiveSection)
│   └── Groups images from one measurement
│       └── images: ImageData[]
│
└── SampleWithExperiments(PlotSection, EntryData, ArchiveSection)
    ├── synthesis_info: SampleSynthesisInfo
    └── experimental_results: ExperimentalResult[]

# Existing classes (unchanged)
├── ImageData(PlotSection, ArchiveSection)
│   ├── metadata: ImageMetadata
│   ├── dimensions: ImageDimensions
│   ├── roi: RegionOfInterest
│   └── figures: PlotlyFigure[]
│
├── ImageMetadata(ArchiveSection)
├── ImageDimensions(ArchiveSection)
├── RegionOfInterest(ArchiveSection)
└── BoundingBox(ArchiveSection)
```

## Implementation Details

### File Structure

```
src/nomad_plugin_images/
├── parsers/
│   ├── __init__.py              # Updated with HierarchicalSampleParserEntryPoint
│   ├── image_parser.py          # Existing (unchanged)
│   ├── manifest_parser.py       # Existing (unchanged)
│   └── hierarchical_parser.py   # NEW
│
└── schema_packages/
    ├── __init__.py              # Unchanged
    └── image_analysis.py        # Extended with new classes
```

### Core Parser Logic

**File:** `hierarchical_parser.py`

**Main Method:** `parse(mainfile, archive, logger)`

```python
def parse(self, mainfile: str, archive: 'EntryArchive', logger):
    # 1. Validate mainfile is JSON
    # 2. Get parent directory (sample folder)
    # 3. Parse synthesis JSON
    # 4. Create SampleSynthesisInfo
    # 5. Discover experimental subfolders
    # 6. For each subfolder: parse ExperimentalResult
    # 7. Assemble SampleWithExperiments
    # 8. Store in archive.data
```

**Helper Method:** `_parse_experiment_folder(exp_folder, metadata_file, logger)`

```python
def _parse_experiment_folder(self, exp_folder, metadata_file, logger):
    # 1. Create ExperimentalResult
    # 2. Parse metadata.json from this folder
    # 3. Create ImageData
    # 4. Call _create_image_visualization()
    # 5. Return ExperimentalResult with images
```

### Unit Conversion Strategy

**Temperatures:**
```python
# Input: degrees Celsius (from JSON)
# Output: Kelvin (NOMAD standard)
celsius_value = float(synthesis_dict.get('source_temperature_degc', 0))
kelvin_value = celsius_value + 273.15
```

**Pressures:**
```python
# Input: various units (mtorr, mbar from JSON)
# Output: NOMAD units (specified in Quantity definition)
pressure_mtorr = float(synthesis_dict.get('pressure_mtorr', 0))
# Unit specified as: unit="millitorr"
```

**Powers:**
```python
# Input: string or number (watts)
# Output: float (watts)
cu_power = float(synthesis_dict.get('cu_source_power', 0))
# Unit specified as: unit="watt"
```

### Visualization Strategy

**Image Handling:**
1. Load numpy array from `.npy` file
2. Check dimensions (if >1000px, downsample)
3. Normalize pixel values (0-255)
4. Convert to RGB if grayscale
5. Create Plotly figure
6. Add ROI overlays (circle + bounding box)
7. Store as `PlotlyFigure` in `ImageData.figures`

**Downsampling:**
```python
# For display only, original data preserved
max_display_size = 1000
if img.shape[0] > max_display_size:
    scale = img.shape[0] // max_display_size
    img_display = img[::scale, ::scale]  # Preserve aspect ratio
    # Scale ROI coordinates by same factor
```

## Error Handling

### Graceful Degradation

```python
try:
    # Parse synthesis info
except Exception as e:
    logger.error(f"Error reading JSON: {e}")
    # Continue with empty/default values
    return SampleWithExperiments()

try:
    # Parse experiment folder
except Exception as e:
    logger.error(f"Error parsing folder: {e}")
    # Continue to next folder
    continue

try:
    # Create visualization
except Exception as e:
    logger.error(f"Visualization failed: {e}")
    # Continue without plot
    pass
```

### Logging Strategy

All significant operations logged at appropriate levels:
- `logger.info()` - Successful parsing steps
- `logger.warning()` - Missing optional data
- `logger.error()` - Failed operations (but continue)

## Entry Point Registration

**File:** `pyproject.toml`

```toml
[project.entry-points.'nomad.plugin']
hierarchical_parser = "nomad_plugin_images.parsers:hierarchical_parser"
```

**Entry Point Class:** `HierarchicalSampleParserEntryPoint`

```python
class HierarchicalSampleParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_plugin_images.parsers.hierarchical_parser import HierarchicalSampleParser
        return HierarchicalSampleParser(**self.model_dump())

hierarchical_parser = HierarchicalSampleParserEntryPoint(
    name='HierarchicalSampleParser',
    description='Parser for hierarchical sample data with synthesis info and experimental results.',
    mainfile_name_re=r'CuSnZnS_\d+\.json|^[A-Za-z0-9_]+\.json$',
    mainfile_mime_re=r'application/json',
)
```

## Testing Strategy

**Test File:** `tests/parsers/test_hierarchical_parser.py`

**Test Coverage:**

1. **Unit Tests:**
   - Parser initialization
   - JSON parsing (synthesis info)
   - Experimental folder discovery
   - Image metadata parsing
   - Unit conversions

2. **Integration Tests:**
   - Complete hierarchical structure
   - Multiple experimental folders
   - Visualization generation
   - Error handling

3. **Fixtures:**
   - `temp_sample_hierarchy()` - Creates temporary test structure
   - `test_data_dir()` - Points to real test data

## Data Flow Example

### Input Structure
```
CuSnZnS_31_123456/
├── CuSnZnS_31.json
│   {
│     "sample_id": "249606",
│     "sample_name": "CuSnZnS_31",
│     "cu_source_power": "94",
│     "source_temperature_degc": "130",
│     ...
│   }
└── 20260323_133521/
    ├── metadata.json
    │   {
    │     "timestamp": "20260323_133521",
    │     "exposure_ms": 2.005,
    │     "shape": [3000, 4096, 3],
    │     "circular_roi": {...}
    │   }
    └── image_raw.npy  (3000 x 4096 x 3 array)
```

### Output Structure (NOMAD Archive)

```
archive.data = SampleWithExperiments
├── name: "CuSnZnS_31_123456"
├── synthesis_info: SampleSynthesisInfo
│   ├── sample_id: "249606"
│   ├── cu_source_power: 94.0 [watt]
│   ├── source_temperature_degc: 403.15 [kelvin]
│   └── ... (all synthesis parameters)
│
└── experimental_results: [ExperimentalResult]
    └── [0] ExperimentalResult
        ├── experiment_id: "20260323_133521"
        └── images: [ImageData]
            └── [0] ImageData
                ├── name: "Image_20260323_133521"
                ├── metadata: ImageMetadata
                │   └── exposure_ms: 2.005 [millisecond]
                ├── dimensions: ImageDimensions
                │   ├── height: 3000
                │   ├── width: 4096
                │   └── channels: 3
                ├── roi: RegionOfInterest
                │   └── bounding_box: BoundingBox
                ├── npy_file_path: "20260323_133521/image_raw.npy"
                └── figures: [PlotlyFigure]
                    └── [0] Interactive plot with ROI overlay
```

## Performance Considerations

1. **Large Images:**
   - Downsampling for display (<1000px)
   - Original data in `.npy` file (preserved)
   - Lazy loading (only when needed)

2. **Multiple Experiments:**
   - Sequential folder iteration
   - Each parsed independently
   - Failures don't block others

3. **Memory:**
   - Images downsampled before Plotly serialization
   - Visualization generated during parsing (while files available)
   - No in-memory caching of raw arrays

## Security Considerations

1. **File Access:**
   - Only reads files within upload directory
   - No arbitrary filesystem access
   - Relative path usage

2. **Input Validation:**
   - JSON parsing with error handling
   - File existence checks
   - Path traversal prevention

3. **Data Isolation:**
   - Each upload in separate archive
   - No cross-sample data contamination

## Future Enhancements

### Phase 2
- XRF analysis data integration (CSV parser)
- Multi-image support per experiment
- Statistical analysis (mean, std of images)

### Phase 3
- Spectral data (wavelength series)
- Comparison plots (synthesis vs. results)
- Automated feature detection

### Phase 4
- Machine learning integration
- Batch processing of multiple samples
- Advanced visualization (3D data)
