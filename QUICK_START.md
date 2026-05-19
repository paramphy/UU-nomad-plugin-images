# Quick Start Guide: Hierarchical Sample Parser

## 30-Second Overview

The **Hierarchical Sample Parser** handles your materials science data with this structure:

```
YourSample_ID/
├── SampleInfo.json           ← Synthesis parameters
└── Timestamp_Measurement/
    ├── metadata.json         ← Acquisition settings
    └── image_raw.npy         ← Image data
```

**Result in NOMAD:** A complete entry linking synthesis info to experimental measurements with interactive visualizations.

---

## Step-by-Step

### 1. Organize Your Data

Create a folder with this structure:

```
CuSnZnS_31_123456/
├── CuSnZnS_31.json
└── 20260323_133521/
    ├── metadata.json
    └── image_raw.npy
```

### 2. Prepare Sample JSON

**File:** `CuSnZnS_31.json`

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

### 3. Prepare Experimental Metadata

**File:** `metadata.json` (in each experimental subfolder)

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

### 4. Add Image Data

**File:** `image_raw.npy` (in same folder as metadata.json)

- NumPy array (binary format)
- Dimensions must match `shape` in metadata.json
- Supports: grayscale (2D), color/RGB (3D), any bit depth

**Generate with Python:**
```python
import numpy as np
# Create your image
img = np.array(...)  # your image data
# Save as numpy array
np.save('image_raw.npy', img)
```

### 5. Upload to NOMAD

1. **Open NOMAD** and go to upload section
2. **Select folder:** `CuSnZnS_31_123456/`
3. **Choose parser:** `HierarchicalSampleParser`
4. **Click Parse**
5. **View results** in NOMAD database

---

## What You Get

### In NOMAD Archive:

✅ **Sample Entry** with:
- Sample ID, name, date, elements
- All synthesis parameters (powers, temperatures, pressures, timing)
- Unit conversion (°C→K) automatic

✅ **Multiple Experiments** grouped under sample:
- Each with its own metadata
- All images and settings preserved

✅ **Interactive Visualizations**:
- Image display
- ROI circle overlay (blue)
- Bounding box overlay (red)
- Hover for pixel coordinates
- Zoom/pan/download capabilities

✅ **Full Traceability**:
- From synthesis → to experiments → to images
- All parameters preserved
- Proper units assigned

---

## Real Example

### Input Files:

**CuSnZnS_31_123456/CuSnZnS_31.json:**
```json
{"sample_name": "CuSnZnS_31", "elements": "Cu, Sn, Zn", ...}
```

**CuSnZnS_31_123456/20260323_133521/metadata.json:**
```json
{"timestamp": "20260323_133521", "exposure_ms": 2.005, ...}
```

**CuSnZnS_31_123456/20260323_133521/image_raw.npy:**
Raw image data (3000 x 4096 x 3)

### NOMAD Output:

```
SampleWithExperiments
├── Sample: CuSnZnS_31_123456
├── Synthesis:
│   ├── Sample ID: 249606
│   ├── Elements: Cu, Sn, Zn
│   ├── Cu Power: 94 W
│   ├── Source Temp: 403.15 K
│   └── ...
├── Experiment 1: 20260323_133521
│   ├── Image: 3000x4096 pixels (RGB)
│   ├── Exposure: 2.005 ms
│   ├── Gain: 0
│   └── [Interactive plot with ROI overlay]
└── ... (more experiments)
```

---

## Naming Conventions

### Sample Folder
- **Format:** `{SampleName}_{UniqueID}`
- **Examples:** `CuSnZnS_31_123456`, `Sample_001_ABC`

### Sample JSON
- **Name:** Can match sample (e.g., `CuSnZnS_31.json`)
- **Must be** in sample folder root
- **Format:** JSON with synthesis parameters

### Experimental Folders
- **Name:** Timestamp or descriptive (e.g., `20260323_133521`)
- **Must contain:** `metadata.json` + `image_raw.npy`
- **Count:** Unlimited (auto-discovered)

---

## Common Issues

### Parser Not Detecting My Files
- ❌ JSON in wrong folder (must be in sample root)
- ❌ metadata.json missing from experimental subfolder
- ✅ Check file paths exactly match
- ✅ Verify JSON is valid (use jsonlint.com)

### Images Not Displaying
- ❌ .npy file missing or wrong location
- ❌ Shape in metadata doesn't match actual array
- ✅ Check metadata.json: `shape` field
- ✅ Verify: `np.load('image_raw.npy').shape`

### Temperature Shows Wrong Value
- ✓ This is normal - parser converts °C to Kelvin
- Input: `source_temperature_degc: 130`
- Output: `403.15 K` (correct!)

### Missing Cooling Parameters
- ✓ Optional fields can be empty or "-"
- Parser handles gracefully

---

## Full Documentation

- **User Guide:** See `docs/how_to/hierarchical_data_parser.md`
- **Technical Details:** See `docs/reference/hierarchical_design.md`
- **Testing:** See `tests/parsers/test_hierarchical_parser.py`

---

## Python Code Example

```python
from nomad_plugin_images.parsers.hierarchical_parser import HierarchicalSampleParser
from nomad.datamodel import EntryArchive

# Create parser
parser = HierarchicalSampleParser(
    name='HierarchicalSampleParser',
    description='Parse hierarchical samples',
    mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
)

# Create archive
archive = EntryArchive()

# Parse your data
parser.parse('/path/to/CuSnZnS_31.json', archive, logger=None)

# Access results
sample = archive.data
print(f"Sample: {sample.name}")
print(f"Sample ID: {sample.synthesis_info.sample_id}")
print(f"Experiments: {len(sample.experimental_results)}")

for exp in sample.experimental_results:
    print(f"  - {exp.experiment_id}: {len(exp.images)} image(s)")
    for img in exp.images:
        print(f"    * {img.name}: {img.dimensions.height}x{img.dimensions.width}")
```

---

## Tips & Tricks

### Multiple Experiments
Just add more subfolders! Parser auto-discovers all:

```
CuSnZnS_31_123456/
├── CuSnZnS_31.json
├── 20260323_133521/      ← Experiment 1
│   ├── metadata.json
│   └── image_raw.npy
├── 20260323_140000/      ← Experiment 2 (auto-discovered)
│   ├── metadata.json
│   └── image_raw.npy
└── 20260323_150000/      ← Experiment 3 (auto-discovered)
    ├── metadata.json
    └── image_raw.npy
```

### Handling Large Images
- Parser auto-downsamples >1000px for display
- Original data preserved in .npy file
- ROI coordinates scaled automatically

### Decimal Separators
- Commas replaced with periods: `8,333` → `8.333`
- Works with European and US formats

---

## Support

**Questions?** Check:
1. Quick Start Guide (this file)
2. User Guide: `docs/how_to/hierarchical_data_parser.md`
3. Technical Design: `docs/reference/hierarchical_design.md`
4. Test Examples: `tests/parsers/test_hierarchical_parser.py`

**Issues?** Check parser logs in NOMAD for detailed error messages.

---

## Next Steps

1. ✅ Organize your data as shown above
2. ✅ Create sample JSON with synthesis parameters
3. ✅ Create metadata.json for each experiment
4. ✅ Save images as image_raw.npy
5. ✅ Upload to NOMAD
6. ✅ Select HierarchicalSampleParser
7. ✅ View results with interactive plots!

**Enjoy exploring your data in NOMAD!** 🚀
