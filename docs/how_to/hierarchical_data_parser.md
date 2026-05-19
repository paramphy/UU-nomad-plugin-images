# Hierarchical Sample Data Parser

## Overview

The **Hierarchical Sample Parser** handles complex, multi-level data structures commonly found in materials science experiments. It bridges the gap between raw sample synthesis information and experimental measurements performed on those samples.

## Data Structure

The parser expects the following directory hierarchy:

```
CuSnZnS_31_123456/                    # Sample folder (top level)
├── CuSnZnS_31.json                   # Sample synthesis parameters
└── 20260323_133521/                  # Experimental measurement folder
    ├── metadata.json                 # Acquisition-specific metadata
    └── image_raw.npy                 # Raw image data (numpy array)
└── 20260323_140000/                  # Another experimental measurement
    ├── metadata.json
    └── image_raw.npy
```

### Sample Synthesis JSON (`CuSnZnS_31.json`)

Contains all parameters used to synthesize/create the material sample:

```json
{
  "date": "2026-03-05",
  "sample_id": "249606",
  "sample_name": "CuSnZnS_31",
  "elements": "Cu, Sn, Zn",
  "cu_source_power": "94",
  "sn_source_power": "70",
  "zn_source_power": "64",
  "pressure_mtorr": "15",
  "source_temperature_degc": "130",
  "process_temperature_degc": "550",
  "chamber_pressure_mbar": "100",
  "process_time_min": "10",
  "cooling_time_min": "60",
  "cooling_rate_degc_min": "8.333333333"
}
```

**Supported Fields:**
- `sample_id`, `sample_name`, `date`, `elements` - Identifiers and composition
- `cu_source_power`, `sn_source_power`, `zn_source_power` - Source power in watts
- `pressure_mtorr` - Deposition pressure in millitorr
- `source_temperature_degc` - Source temperature (converted to Kelvin)
- `process_temperature_degc` - Process temperature (converted to Kelvin)
- `chamber_pressure_mbar` - Chamber pressure in millibar
- `process_time_min` - Process duration in minutes
- `cooling_time_min` - Cooling duration (optional)
- `cooling_rate_degc_min` - Cooling rate (optional)

### Experimental Metadata (`metadata.json`)

Located in each experimental subfolder, contains acquisition-specific parameters:

```json
{
  "timestamp": "20260323_133521",
  "shape": [3000, 4096, 3],
  "bit_depth": 12,
  "is_color": true,
  "exposure_ms": 2.005,
  "gain": 0,
  "min": 0,
  "max": 255,
  "circular_roi": {
    "center_x_px": 1539,
    "center_y_px": 2093,
    "radius_px": 895,
    "square_crop_size_px": 1790,
    "bounding_box": {
      "x_min": 639,
      "y_min": 1193,
      "x_max": 2439,
      "y_max": 2993,
      "width": 1800,
      "height": 1800
    }
  }
}
```

**Fields:**
- `timestamp` - When the measurement was taken
- `shape` - Image dimensions [height, width, channels]
- `bit_depth` - Sensor bit depth (8, 10, 12, 16)
- `is_color` - Whether image is color (true) or grayscale (false)
- `exposure_ms` - Camera exposure time in milliseconds
- `gain` - Camera gain setting
- `min`, `max` - Pixel value range
- `circular_roi` - Region of interest with center, radius, and bounding box

### Image Data (`image_raw.npy`)

NumPy array file containing the raw image data. Supports:
- Grayscale images (2D arrays)
- Color images (3D arrays with RGB channels)
- Various bit depths and data types

## NOMAD Schema

### Class Hierarchy

```
SampleWithExperiments (Top-level entry)
├── SampleSynthesisInfo (Synthesis parameters)
└── ExperimentalResult (Multiple experimental measurements)
    └── ImageData (Images from that measurement)
        ├── ImageMetadata (Acquisition settings)
        ├── ImageDimensions (Resolution, channels)
        └── RegionOfInterest (ROI with bounding box)
```

### SampleWithExperiments

**Top-level entry** for a complete sample with all its experimental results.

**Fields:**
- `name` - Sample identifier (e.g., "CuSnZnS_31_123456")
- `sample_folder_path` - Path to the sample folder
- `synthesis_info` - SubSection with `SampleSynthesisInfo`
- `experimental_results` - List of `ExperimentalResult` entries

### SampleSynthesisInfo

Contains all synthesis parameters for the sample.

**Fields:**
- `sample_id`, `sample_name`, `date`, `elements`
- Source power fields (with unit conversion to watts)
- Temperature fields (converted to Kelvin)
- Pressure fields (millitorr, millibar)
- Process timing (minutes)

### ExperimentalResult

Represents one experimental measurement session.

**Fields:**
- `experiment_id` - Unique identifier (typically timestamp folder name)
- `description` - Human-readable description
- `images` - List of `ImageData` entries from this measurement

### ImageData

Complete image entry with metadata and visualization.

**Fields:**
- `name` - Image identifier
- `metadata` - `ImageMetadata` with acquisition settings
- `dimensions` - `ImageDimensions` with resolution info
- `roi` - `RegionOfInterest` with bounding box
- `npy_file_path` - Reference to numpy array file
- `figures` - Plotly visualization (auto-generated)

## Features

### 1. Hierarchical Structure Support
- Automatically discovers experimental folders within the sample directory
- Parses all metadata files found
- Creates proper parent-child relationships in NOMAD

### 2. Unit Conversion
- Temperatures: Celsius → Kelvin
- Powers: String → float (watts)
- Pressures: Proper unit assignment

### 3. Image Visualization
- Automatic Plotly figure generation
- ROI overlay (circular ROI + bounding box)
- Downsampling for large images (>1000px) for faster rendering
- Interactive hover information

### 4. Flexible File Matching
- Matches JSON files in sample folders
- Pattern: `^[A-Za-z0-9_]+\.json$`
- Customizable regex for different naming schemes

### 5. Robust Error Handling
- Missing optional fields default to sensible values
- Handles missing ROI data gracefully
- Continues parsing even if individual images fail
- Detailed logging for debugging

## Usage

### Uploading to NOMAD

1. **Prepare your data** with the hierarchical structure above
2. **Upload the sample folder** (e.g., `CuSnZnS_31_123456/`)
3. **Select the parser**: Choose "HierarchicalSampleParser" from available parsers
4. **NOMAD processes**:
   - Parses the sample JSON
   - Discovers all experimental subfolders
   - Processes all metadata.json files
   - Generates image visualizations

### Python Usage (Direct)

```python
from nomad_plugin_images.parsers.hierarchical_parser import HierarchicalSampleParser
from nomad.datamodel import EntryArchive

parser = HierarchicalSampleParser(
    name='HierarchicalSampleParser',
    description='Parse hierarchical samples',
    mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
)

archive = EntryArchive()
parser.parse('/path/to/CuSnZnS_31.json', archive, logger=None)

# Access parsed data
sample = archive.data
print(f"Sample: {sample.name}")
print(f"Synthesis params: {sample.synthesis_info}")
print(f"Experimental results: {len(sample.experimental_results)}")
```

## File Naming Conventions

### Sample Folder
- Format: `{SampleName}_{UniqueID}`
- Example: `CuSnZnS_31_123456`

### Synthesis JSON
- Must be in the sample folder
- Filename matches sample parameters (e.g., `CuSnZnS_31.json`)
- Naming is flexible (uses regex pattern matching)

### Experimental Folders
- Format: `{Timestamp}` or descriptive name
- Example: `20260323_133521`
- Must contain `metadata.json` and `image_raw.npy`

## Visualization

The parser automatically generates **Plotly interactive plots** showing:

1. **Raw Image** - Displayed with proper aspect ratio
2. **Circular ROI** - Blue circle overlay
3. **Bounding Box** - Red rectangle overlay
4. **Interactive Controls**:
   - Zoom/pan with mouse
   - Hover for pixel coordinates
   - Download as PNG
   - Toggle elements on/off

### Image Downsampling

For large images (>1000 pixels):
- Automatically downsampled for faster rendering
- ROI coordinates scaled proportionally
- Original data preserved in `.npy` file

## Example: Complete Data Flow

```
User Upload
    ↓
CuSnZnS_31_123456/ folder
    ↓
HierarchicalSampleParser detects CuSnZnS_31.json
    ↓
Parse synthesis parameters from JSON
    ↓
Discover subfolders: 20260323_133521, 20260323_140000
    ↓
For each subfolder:
    - Read metadata.json
    - Load image_raw.npy
    - Generate visualization
    ↓
Create SampleWithExperiments entry with:
    - SampleSynthesisInfo
    - 2x ExperimentalResult entries
    - 2x ImageData entries (one per experiment)
    - 2x Plotly figures (auto-generated)
    ↓
Upload to NOMAD database
```

## Troubleshooting

### Parser Not Detecting Files
- Check folder naming convention matches regex
- Ensure JSON files are in the sample folder root
- Verify file is valid JSON

### Missing Images
- Check `metadata.json` and `image_raw.npy` are in the same experimental subfolder
- Verify file names match exactly (case-sensitive on Linux)
- Check file permissions

### Visualization Not Generated
- Verify `.npy` file is readable
- Check image dimensions in metadata match actual array shape
- Look for parser logs for specific error messages

### Unit Conversion Issues
- Temperature fields automatically convert °C to Kelvin
- Check decimal separator (some files use commas)
- Cooling fields (optional) may be empty or contain "-"

## Future Enhancements

Potential improvements:
- Support for additional file formats (HDF5, NetCDF)
- Multi-image support per experiment
- XRF analysis data integration
- Automatic property calculation (film thickness, etc.)
- Spectral data visualization
- Comparison plots across experiments
