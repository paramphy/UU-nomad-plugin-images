# Architecture & Data Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOMAD Upload Interface                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Hierarchical Parser Detection                   │
│   Matches: CuSnZnS_31.json in folder CuSnZnS_31_123456/        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           HierarchicalSampleParser.parse()                       │
│                                                                   │
│  1. Read synthesis JSON                                          │
│  2. Create SampleSynthesisInfo                                   │
│  3. Discover experimental subfolders                             │
│  4. For each subfolder:                                          │
│     a. Read metadata.json                                        │
│     b. Create ImageData                                          │
│     c. Load image_raw.npy                                        │
│     d. Generate Plotly visualization                             │
│  5. Create ExperimentalResult                                    │
│  6. Assemble SampleWithExperiments                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NOMAD Archive Entry                           │
│              (SampleWithExperiments)                             │
│                                                                   │
│  ✓ Synthesis info                                                │
│  ✓ Multiple experiments                                          │
│  ✓ Images with metadata                                          │
│  ✓ Interactive visualizations                                    │
│  ✓ Full provenance tracking                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Organization Flow

```
USER'S FILESYSTEM                    NOMAD ARCHIVE
══════════════════════════════════════════════════════════════════

CuSnZnS_31_123456/                   SampleWithExperiments
│                                    ├── name: "CuSnZnS_31_123456"
├── CuSnZnS_31.json                  ├── synthesis_info
│   {                                │   ├── sample_id: "249606"
│     "sample_id": "249606",          │   ├── sample_name: "CuSnZnS_31"
│     "cu_source_power": "94",        │   ├── cu_source_power: 94.0 W
│     "source_temp": "130",           │   ├── source_temp: 403.15 K
│     ...                             │   └── ...
│   }          ────────────────►      │
│                                    │
├── 20260323_133521/                 └── experimental_results[]
│   │                                    └── [0] ExperimentalResult
│   ├── metadata.json         ───┐       ├── experiment_id: "20260323_133521"
│   │   {                        │       └── images[]
│   │     "exposure_ms": 2.005,  │           └── [0] ImageData
│   │     "shape": [3000, 4096], │               ├── metadata.exposure: 2.005 ms
│   │     "circular_roi": {...}  │               ├── dimensions.height: 3000
│   │   }                        │               ├── dimensions.width: 4096
│   │                            ├──────►       ├── roi.bounding_box: {...}
│   │                            │               └── figures: [PlotlyFigure]
│   └── image_raw.npy  ──────────┤               └── [Interactive Plot]
│       (3000x4096x3)            │
│                                │
└── 20260323_140000/             │
    ├── metadata.json    ───┐    │
    │                       │    │
    └── image_raw.npy  ─────┴────┼──► experimental_results[]
                                │    └── [1] ExperimentalResult
                                │        ├── experiment_id: "20260323_140000"
                                │        └── images[]: [ImageData with plot]
                                │
                                └─────► (Multiple experiments auto-discovered)
```

## Parser Processing Pipeline

```
INPUT: CuSnZnS_31.json in CuSnZnS_31_123456/
           │
           ▼
┌─────────────────────────────────────┐
│ 1. PARSE SYNTHESIS JSON             │
│                                     │
│ ✓ Read CuSnZnS_31.json             │
│ ✓ Extract fields:                  │
│   - sample_id, sample_name, date   │
│   - elements composition           │
│   - cu/sn/zn source power          │
│   - temperatures, pressures        │
│   - process timing                 │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 2. UNIT CONVERSION                  │
│                                     │
│ ✓ Celsius → Kelvin (+273.15)       │
│ ✓ String → Float (with units)      │
│ ✓ Assign units to quantities        │
│ ✓ Handle optional fields            │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 3. CREATE SampleSynthesisInfo       │
│                                     │
│ ✓ SampleSynthesisInfo object        │
│ ✓ All fields populated              │
│ ✓ Units verified                    │
│ ✓ Ready for NOMAD                   │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 4. DISCOVER EXPERIMENTAL FOLDERS    │
│                                     │
│ ✓ Iterate sample folder             │
│ ✓ Find dirs with metadata.json      │
│ ✓ List: [20260323_133521,           │
│          20260323_140000, ...]      │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 5. PARSE EACH EXPERIMENT (LOOP)    │
│                                     │
│ For each experimental folder:       │
│   ✓ Read metadata.json              │
│   ✓ Create ImageData                │
│   ✓ Parse image metadata            │
│   ✓ Parse image dimensions          │
│   ✓ Parse ROI information           │
│   ✓ Find image_raw.npy              │
│   ✓ Generate visualization          │
│   ✓ Create ExperimentalResult       │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 6. VISUALIZATION GENERATION         │
│                                     │
│ For each image:                     │
│   ✓ Load .npy file                  │
│   ✓ Normalize pixel values          │
│   ✓ Downsample if >1000px           │
│   ✓ Convert to RGB if needed        │
│   ✓ Create Plotly figure            │
│   ✓ Add ROI overlays:               │
│     - Circular ROI (blue)           │
│     - Bounding box (red)            │
│   ✓ Enable interactive controls     │
│   ✓ Store as PlotlyFigure           │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 7. ASSEMBLE FINAL ENTRY             │
│                                     │
│ ✓ Create SampleWithExperiments      │
│ ✓ Attach synthesis_info             │
│ ✓ Attach experimental_results[]     │
│ ✓ Set name, paths, metadata         │
└─────────────────────────────────────┘
           │
           ▼
OUTPUT: archive.data = SampleWithExperiments
        (Ready for NOMAD database)
```

## Schema Class Relationships

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    SampleWithExperiments                         │
│                   (PlotSection, EntryData)                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Properties:                                             │   │
│  │ • name: str                                            │   │
│  │ • sample_folder_path: str                              │   │
│  │ • synthesis_info: SampleSynthesisInfo ──┐             │   │
│  │ • experimental_results: ExperimentalResult[] ──┐      │   │
│  │                                          │      │      │   │
│  └─────────────────────────────────────────┼──────┼──────┘   │
│                                            │      │            │
└────────────────────────────────────────────┼──────┼────────────┘
                                             │      │
                        ┌────────────────────┘      │
                        │                           │
                        ▼                           │
        ┌─────────────────────────────────┐         │
        │  SampleSynthesisInfo            │         │
        │  (ArchiveSection)               │         │
        │                                 │         │
        │ • sample_id: str                │         │
        │ • sample_name: str              │         │
        │ • date: str                     │         │
        │ • elements: str                 │         │
        │ • cu_source_power: float [W]    │         │
        │ • sn_source_power: float [W]    │         │
        │ • zn_source_power: float [W]    │         │
        │ • pressure_mtorr: float         │         │
        │ • source_temperature: float [K] │         │
        │ • process_temperature: float [K]│         │
        │ • chamber_pressure: float [mbar]│         │
        │ • process_time_min: float [min] │         │
        │ • cooling_time_min: float [min] │         │
        │ • cooling_rate: float [K/min]   │         │
        └─────────────────────────────────┘         │
                                                     │
        ┌────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│  ExperimentalResult[]          │
│  (ArchiveSection)              │
│                                │
│ • experiment_id: str           │
│ • description: str             │
│ • images: ImageData[] ──┐      │
└────────────────────────┼───────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │  ImageData              │
            │  (PlotSection)          │
            │                         │
            │ • name: str             │
            │ • npy_file_path: str    │
            │ • metadata ─────────┐   │
            │ • dimensions ───────┼─┐ │
            │ • roi ──────────────┼─┤ │
            │ • figures ──────────┤ │ │
            │                     │ │ │
            └─────────────────────┼─┼─┘
                                  │ │
            ┌─────────────────────┘ │
            │  ┌──────────────────┘  │
            │  │                     │
            ▼  ▼                     ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
    │ ImageMetadata   │    │ImageDimensions  │    │ RegionOfInterest │
    │                 │    │                 │    │                  │
    │ • timestamp     │    │ • height        │    │ • center_x       │
    │ • exposure_ms   │    │ • width         │    │ • center_y       │
    │ • gain          │    │ • channels      │    │ • radius         │
    │ • bit_depth     │    │ • is_color      │    │ • bounding_box   │
    │                 │    │ • pixel_min     │    │   ├─ x_min       │
    │                 │    │ • pixel_max     │    │   ├─ y_min       │
    │                 │    │                 │    │   ├─ x_max       │
    │                 │    │                 │    │   ├─ y_max       │
    │                 │    │                 │    │   ├─ width       │
    │                 │    │                 │    │   └─ height      │
    └─────────────────┘    └─────────────────┘    └──────────────────┘
```

## File I/O and Processing

```
HIERARCHICAL_PARSER.parse()
│
├─ INPUT: mainfile = "/path/CuSnZnS_31_123456/CuSnZnS_31.json"
│
├─ [Step 1] Extract parent directory
│   sample_folder = Path("/path/CuSnZnS_31_123456/")
│
├─ [Step 2] Read synthesis JSON
│   ├─ Read: CuSnZnS_31.json
│   └─ Parse: json.load(f)
│
├─ [Step 3] Discover subfolders
│   ├─ sample_folder.iterdir()
│   ├─ Filter: is_dir() and "metadata.json" exists
│   └─ Result: [20260323_133521, 20260323_140000]
│
├─ [Step 4] For each experimental folder:
│   │
│   ├─ [4a] Locate files
│   │   ├─ metadata.json
│   │   └─ image_raw.npy
│   │
│   ├─ [4b] Read metadata.json
│   │   └─ Parse: json.load(f)
│   │
│   ├─ [4c] Load image
│   │   ├─ np.load(npy_file)
│   │   └─ Check: shape, dtype
│   │
│   ├─ [4d] Generate visualization
│   │   ├─ Normalize pixels
│   │   ├─ Downsample if needed
│   │   ├─ Create Plotly figure
│   │   ├─ Add ROI overlays
│   │   └─ Store: PlotlyFigure
│   │
│   └─ [4e] Create ImageData object
│       └─ Attach all metadata + visualization
│
├─ [Step 5] Assemble results
│   ├─ Create SampleWithExperiments
│   ├─ Attach synthesis_info
│   ├─ Attach experimental_results[]
│   └─ Set all properties
│
└─ OUTPUT: archive.data = SampleWithExperiments
           (Write to NOMAD database)
```

## Error Handling Flow

```
                    parse() called
                          │
                          ▼
            ┌─────────────────────────────┐
            │ Try: Read synthesis JSON    │
            └────────┬────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    SUCCESS                    ERROR
        │                         │
        ▼                         ▼
   Continue          ┌────────────────────────┐
                     │ logger.error()         │
                     │ Return empty entry     │
                     │ Continue gracefully    │
                     └────────────────────────┘

            For each experimental folder:
                          │
                          ▼
            ┌─────────────────────────────┐
            │ Try: Parse folder           │
            └────────┬────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    SUCCESS                    ERROR
        │                         │
        ▼                         ▼
   Add result         ┌────────────────────────┐
                     │ logger.error()         │
                     │ Skip this folder       │
                     │ Continue to next       │
                     └────────────────────────┘

          For each image visualization:
                          │
                          ▼
            ┌─────────────────────────────┐
            │ Try: Create visualization   │
            └────────┬────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    SUCCESS                    ERROR
        │                         │
        ▼                         ▼
   Attach plot       ┌────────────────────────┐
                     │ logger.error()         │
                     │ Skip visualization     │
                     │ Continue with metadata │
                     └────────────────────────┘

                     Final Result
                          │
                          ▼
        ┌───────────────────────────────────┐
        │ SampleWithExperiments             │
        │ ✓ Best case: Complete entry      │
        │ ✓ Partial: Some data missing     │
        │ ✓ Worst case: Empty structure   │
        │ ✓ Always: Graceful degradation  │
        └───────────────────────────────────┘
```

## Integration with NOMAD

```
NOMAD Upload Interface
         │
         │ User selects parser
         ▼
Parser Registry
         │
         ├─ ImageParser (matches: metadata.json)
         ├─ ManifestParser (matches: *_manifest.csv)
         └─ HierarchicalSampleParser (matches: *.json in sample folder) ◄── NEW
         │
         ▼
HierarchicalSampleParser.parse()
         │
         ├─ Parse hierarchical structure
         ├─ Create NOMAD entries
         ├─ Generate visualizations
         ├─ Assign units
         └─ Populate archive
         │
         ▼
NOMAD Archive
         │
         ├─ SampleWithExperiments entry
         ├─ Synthesis parameters indexed
         ├─ Experimental results linked
         ├─ Images with metadata
         ├─ Interactive visualizations
         └─ Full provenance tracking
         │
         ▼
NOMAD Database
         │
         ├─ Searchable entries
         ├─ Interactive exploration
         ├─ Data discovery
         ├─ Export/API access
         └─ Integration with other tools
```
