"""
Parser for hierarchical sample data with experiments and images.

Reads folder structure:
CuSnZnS_31_123456/
├── CuSnZnS_31.json          # Sample synthesis parameters
└── 20260323_133521/         # Experimental folder
    ├── metadata.json        # Acquisition metadata
    └── image_raw.npy        # Raw image data

Creates a SampleWithExperiments entry linking synthesis info to experimental results.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive

from nomad.parsing import MatchingParser

from nomad_plugin_images.schema_packages.image_analysis import (
    BoundingBox,
    ExperimentalResult,
    ImageData,
    ImageDimensions,
    ImageMetadata,
    RegionOfInterest,
    SampleSynthesisInfo,
    SampleWithExperiments,
)


class HierarchicalSampleParser(MatchingParser):
    """
    Parser for hierarchical sample data with synthesis info and experimental results.

    Matches JSON files in sample folders and builds complete entry with:
    - Synthesis parameters from the JSON
    - All experimental measurements (subfolders)
    - All images within each experiment
    """

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger,
    ) -> None:
        """
        Parse hierarchical sample data.

        Args:
            mainfile: Path to the sample synthesis JSON file (e.g., CuSnZnS_31.json)
            archive: The entry archive to populate
            logger: Structlog logger
        """
        try:
            mainfile_path = Path(mainfile)
            sample_folder = mainfile_path.parent

            if logger:
                logger.info(f'Parsing hierarchical sample from: {sample_folder.name}')

            # Create main entry
            sample_entry = SampleWithExperiments()
            sample_entry.name = sample_folder.name
            sample_entry.sample_folder_path = sample_folder.name

            # Parse synthesis information
            try:
                with open(mainfile_path, 'r') as f:
                    synthesis_dict = json.load(f)
                if logger:
                    logger.info(f'Loaded synthesis info with keys: {list(synthesis_dict.keys())}')
            except Exception as e:
                if logger:
                    logger.error(f'Error reading synthesis JSON: {str(e)}')
                archive.data = sample_entry
                return

            # Create SampleSynthesisInfo
            sample_entry.synthesis_info = SampleSynthesisInfo()
            sample_entry.synthesis_info.sample_id = str(synthesis_dict.get('sample_id', ''))
            sample_entry.synthesis_info.sample_name = str(synthesis_dict.get('sample_name', ''))
            sample_entry.synthesis_info.date = str(synthesis_dict.get('date', ''))
            sample_entry.synthesis_info.elements = str(synthesis_dict.get('elements', ''))

            # Parse numerical synthesis parameters
            try:
                sample_entry.synthesis_info.cu_source_power = float(
                    synthesis_dict.get('cu_source_power', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.cu_source_power = 0.0

            try:
                sample_entry.synthesis_info.sn_source_power = float(
                    synthesis_dict.get('sn_source_power', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.sn_source_power = 0.0

            try:
                sample_entry.synthesis_info.zn_source_power = float(
                    synthesis_dict.get('zn_source_power', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.zn_source_power = 0.0

            try:
                sample_entry.synthesis_info.pressure_mtorr = float(
                    synthesis_dict.get('pressure_mtorr', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.pressure_mtorr = 0.0

            try:
                sample_entry.synthesis_info.source_temperature_degc = float(
                    synthesis_dict.get('source_temperature_degc', 0)
                ) + 273.15  # Convert C to K
            except (ValueError, TypeError):
                sample_entry.synthesis_info.source_temperature_degc = 273.15

            try:
                sample_entry.synthesis_info.process_temperature_degc = float(
                    synthesis_dict.get('process_temperature_degc', 0)
                ) + 273.15  # Convert C to K
            except (ValueError, TypeError):
                sample_entry.synthesis_info.process_temperature_degc = 273.15

            try:
                sample_entry.synthesis_info.chamber_pressure_mbar = float(
                    synthesis_dict.get('chamber_pressure_mbar', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.chamber_pressure_mbar = 0.0

            try:
                sample_entry.synthesis_info.process_time_min = float(
                    synthesis_dict.get('process_time_min', 0)
                )
            except (ValueError, TypeError):
                sample_entry.synthesis_info.process_time_min = 0.0

            try:
                cooling_time_str = str(synthesis_dict.get('cooling_time_min', ''))
                if cooling_time_str and cooling_time_str.strip() and cooling_time_str != '-':
                    sample_entry.synthesis_info.cooling_time_min = float(cooling_time_str)
            except (ValueError, TypeError):
                pass

            try:
                cooling_rate_str = str(synthesis_dict.get('cooling_rate_degc_min', ''))
                if cooling_rate_str and cooling_rate_str.strip() and cooling_rate_str != '-':
                    # Replace comma with period for decimal separator
                    cooling_rate_str = cooling_rate_str.replace(',', '.')
                    sample_entry.synthesis_info.cooling_rate_degc_min = float(cooling_rate_str)
            except (ValueError, TypeError):
                pass

            if logger:
                logger.info(f'Successfully parsed synthesis info')

            # Discover and parse experimental folders
            experimental_results = []
            for item in sample_folder.iterdir():
                if item.is_dir() and item.name != '__pycache__':
                    # Check if this folder contains metadata.json
                    metadata_file = item / 'metadata.json'
                    if metadata_file.exists():
                        try:
                            exp_result = self._parse_experiment_folder(
                                item, metadata_file, logger
                            )
                            if exp_result:
                                experimental_results.append(exp_result)
                                if logger:
                                    logger.info(
                                        f'Parsed experiment folder: {item.name}'
                                    )
                        except Exception as e:
                            if logger:
                                logger.error(
                                    f'Error parsing experiment folder {item.name}: {str(e)}'
                                )
                                import traceback
                                logger.error(traceback.format_exc())

            sample_entry.experimental_results = experimental_results

            if logger:
                logger.info(
                    f'Successfully parsed sample with '
                    f'{len(experimental_results)} experimental results'
                )

            archive.data = sample_entry

        except Exception as e:
            if logger:
                logger.error(f'Error parsing hierarchical sample data: {str(e)}')
                import traceback
                logger.error(traceback.format_exc())
            archive.data = SampleWithExperiments()

    def _parse_experiment_folder(
        self, exp_folder: Path, metadata_file: Path, logger
    ) -> ExperimentalResult:
        """
        Parse an experimental measurement folder.

        Args:
            exp_folder: Path to the experiment folder (e.g., 20260323_133521)
            metadata_file: Path to metadata.json in this folder
            logger: Structlog logger

        Returns:
            ExperimentalResult with image data
        """
        exp_result = ExperimentalResult()
        exp_result.experiment_id = exp_folder.name
        exp_result.description = f'Experimental measurement: {exp_folder.name}'

        # Read metadata
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            if logger:
                logger.info(f'Loaded metadata with keys: {list(metadata_dict.keys())}')
        except Exception as e:
            if logger:
                logger.error(f'Error reading metadata.json: {str(e)}')
            return exp_result

        # Create ImageData entry
        image_entry = ImageData()
        image_entry.name = f'Image_{exp_folder.name}'

        # Parse ImageMetadata (Acquisition Settings)
        image_entry.metadata = ImageMetadata()
        image_entry.metadata.timestamp = metadata_dict.get('timestamp', exp_folder.name)
        image_entry.metadata.exposure_ms = float(metadata_dict.get('exposure_ms', 0.0))
        image_entry.metadata.gain = int(metadata_dict.get('gain', 0))
        image_entry.metadata.bit_depth = int(metadata_dict.get('bit_depth', 8))

        # Parse ImageDimensions
        image_entry.dimensions = ImageDimensions()
        shape = metadata_dict.get('shape', [0, 0, 3])

        if isinstance(shape, list) and len(shape) >= 2:
            image_entry.dimensions.height = int(shape[0])
            image_entry.dimensions.width = int(shape[1])
            image_entry.dimensions.channels = int(shape[2]) if len(shape) > 2 else 1

        image_entry.dimensions.is_color = metadata_dict.get('is_color', True)
        image_entry.dimensions.pixel_value_min = int(metadata_dict.get('min', 0))
        image_entry.dimensions.pixel_value_max = int(metadata_dict.get('max', 255))

        # Parse RegionOfInterest
        roi_dict = metadata_dict.get('circular_roi', {})
        if roi_dict:
            image_entry.roi = RegionOfInterest()
            image_entry.roi.center_x_px = float(roi_dict.get('center_x_px', 0))
            image_entry.roi.center_y_px = float(roi_dict.get('center_y_px', 0))
            image_entry.roi.radius_px = float(roi_dict.get('radius_px', 0))
            image_entry.roi.square_crop_size_px = int(
                roi_dict.get('square_crop_size_px', 0)
            )

            # Parse bounding box
            bbox_dict = roi_dict.get('bounding_box', {})
            if bbox_dict:
                image_entry.roi.bounding_box = BoundingBox()
                image_entry.roi.bounding_box.x_min = int(bbox_dict.get('x_min', 0))
                image_entry.roi.bounding_box.y_min = int(bbox_dict.get('y_min', 0))
                image_entry.roi.bounding_box.x_max = int(bbox_dict.get('x_max', 0))
                image_entry.roi.bounding_box.y_max = int(bbox_dict.get('y_max', 0))
                image_entry.roi.bounding_box.width = int(bbox_dict.get('width', 0))
                image_entry.roi.bounding_box.height = int(bbox_dict.get('height', 0))

        # Find and reference the .npy file
        npy_file = metadata_file.parent / 'image_raw.npy'
        if npy_file.exists():
            image_entry.npy_file_path = str(npy_file.relative_to(npy_file.parent.parent))
            if logger:
                logger.info(f'Found .npy file: {npy_file.name}')

            # Try to create visualization
            try:
                npy_data = np.load(npy_file)
                if logger:
                    logger.info(f'Numpy array shape: {npy_data.shape}, dtype: {npy_data.dtype}')

                try:
                    image_entry._create_image_visualization(npy_file, logger)
                    if logger:
                        logger.info('Successfully created visualization')
                except Exception as viz_error:
                    if logger:
                        logger.error(f'Error creating visualization: {str(viz_error)}')
            except Exception as e:
                if logger:
                    logger.warning(f'Could not load .npy file: {str(e)}')

        exp_result.images = [image_entry]
        return exp_result
