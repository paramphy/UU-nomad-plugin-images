"""
Parser for image analysis experiment manifest files.

Reads manifest CSV files that define experiments with multiple image steps,
where each step references a folder containing:
- metadata.json: Camera settings and ROI information
- image_raw.npy: Numpy array containing the raw image data

Creates an ImageExperimentRun entry with nested ImageSteps and ImageData.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive

from nomad.parsing import MatchingParser

from nomad_plugin_images.schema_packages.image_analysis import (
    BoundingBox,
    ImageData,
    ImageDimensions,
    ImageExperimentRun,
    ImageMetadata,
    ImageStep,
    RegionOfInterest,
)


class ManifestParser(MatchingParser):
    """
    Parser for image experiment manifest files.
    
    Reads a manifest CSV that defines multiple image acquisition steps,
    creating a complete ImageExperimentRun structure.
    """

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger,
    ) -> None:
        """
        Parse experiment manifest and create ImageExperimentRun structure.
        
        Args:
            mainfile: Path to the manifest CSV file (e.g., exp_0_manifest.csv)
            archive: The entry archive to populate
            logger: Structlog logger
        """
        try:
            mainfile_path = Path(mainfile)
            
            # Extract run_id from filename (exp_XXX_manifest.csv)
            filename_stem = mainfile_path.stem
            if filename_stem.endswith('_manifest'):
                run_id = filename_stem.replace('_manifest', '')
            else:
                run_id = filename_stem
            
            # Read manifest CSV
            manifest_df = pd.read_csv(mainfile_path)
            
            if logger:
                logger.info(
                    f'Parsing image manifest for run: {run_id}, found {len(manifest_df)} images'
                )
            
            # Create ImageExperimentRun
            experiment = ImageExperimentRun()
            experiment.name = run_id
            experiment.run_id = run_id
            
            # Parse each step from manifest
            steps = []
            for idx, row in manifest_df.iterrows():
                try:
                    step = self._parse_manifest_row(row, mainfile_path.parent, logger)
                    if step:
                        steps.append(step)
                        if logger:
                            logger.info(f'Created step {idx}, step_number={step.step}')
                    else:
                        if logger:
                            logger.warning(f'Step {idx} returned None')
                except Exception as e:
                    if logger:
                        logger.error(f'Error parsing step {idx}: {str(e)}')
                        import traceback
                        logger.error(traceback.format_exc())
            
            # Assign all steps to experiment
            experiment.steps = steps
            
            archive.data = experiment
            
            if logger:
                logger.info(f'Successfully parsed experiment with {len(experiment.steps)} image steps')
        
        except Exception as e:
            if logger:
                logger.error(f'Error parsing manifest: {str(e)}')
                import traceback
                logger.error(traceback.format_exc())
            # Create empty experiment on error
            archive.data = ImageExperimentRun()
    
    def _parse_manifest_row(
        self, row, data_dir: Path, logger
    ) -> ImageStep:
        """
        Parse a single row from the manifest CSV.
        
        Expected manifest columns:
        - step: Step number
        - timestamp: Timestamp of the measurement
        - folder: Name of the folder containing metadata.json and image_raw.npy
        - is_repeat: Whether this is a repeat measurement
        
        Args:
            row: DataFrame row from manifest
            data_dir: Parent directory where folders are located
            logger: Structlog logger
            
        Returns:
            ImageStep with parsed image data
        """
        step = ImageStep()
        
        # Parse step metadata
        try:
            step.step = int(row.get('step', -1))
        except (ValueError, TypeError):
            step.step = -1
        
        step.timestamp = str(row.get('timestamp', ''))
        
        # Parse boolean field
        is_repeat_val = row.get('is_repeat', 'False')
        step.is_repeat = str(is_repeat_val).lower() == 'true'
        
        if logger:
            logger.info(f'Parsing step {step.step}, timestamp={step.timestamp}')
        
        # Get folder name from manifest
        folder_name = str(row.get('folder', ''))
        if not folder_name:
            if logger:
                logger.error('No folder column in manifest row')
            return None
        
        # Construct path to the folder
        data_folder = data_dir / folder_name
        metadata_file = data_folder / 'metadata.json'
        
        if logger:
            logger.info(f'Looking for metadata in: {metadata_file}')
        
        if not metadata_file.exists():
            if logger:
                logger.error(f'Metadata file not found: {metadata_file}')
            return step
        
        # Parse the image data from this folder
        try:
            image_data = self._parse_image_data(metadata_file, logger)
            if image_data:
                step.image = image_data
                if logger:
                    logger.info(f'Successfully parsed image data from step {step.step}')
            else:
                if logger:
                    logger.warning(f'Failed to parse image data for step {step.step}')
        except Exception as e:
            if logger:
                logger.error(f'Error parsing image data in step {step.step}: {str(e)}')
                import traceback
                logger.error(traceback.format_exc())
        
        return step
    
    def _parse_image_data(self, metadata_file: Path, logger) -> ImageData:
        """
        Parse a metadata.json file and create ImageData section.
        
        Args:
            metadata_file: Path to metadata.json file
            logger: Structlog logger
            
        Returns:
            ImageData with all parsed information
        """
        image_entry = ImageData()
        
        # Extract timestamp from parent folder name
        timestamp = metadata_file.parent.name
        image_entry.name = f'Image_{timestamp}'
        
        # Read metadata.json
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            if logger:
                logger.info(f'Loaded metadata with keys: {list(metadata_dict.keys())}')
        except Exception as e:
            if logger:
                logger.error(f'Error reading metadata.json: {str(e)}')
            return image_entry
        
        # Parse ImageMetadata (Acquisition Settings)
        image_entry.metadata = ImageMetadata()
        image_entry.metadata.timestamp = metadata_dict.get('timestamp', timestamp)
        image_entry.metadata.exposure_ms = float(metadata_dict.get('exposure_ms', 0.0))
        image_entry.metadata.gain = int(metadata_dict.get('gain', 0))
        image_entry.metadata.bit_depth = int(metadata_dict.get('bit_depth', 8))
        
        # Parse ImageDimensions
        image_entry.dimensions = ImageDimensions()
        shape = metadata_dict.get('shape', [0, 0, 3])  # Default: 3 channels
        
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
            # Store relative path from the folder containing metadata.json
            # This is more reliable when files are moved/extracted
            image_entry.npy_file_path = str(npy_file.relative_to(npy_file.parent.parent))
            if logger:
                logger.info(f'Found corresponding .npy file: {npy_file.name}')
                logger.info(f'Storing relative path: {image_entry.npy_file_path}')
        else:
            if logger:
                logger.warning(f'No image_raw.npy file found in {metadata_file.parent}')
        
        # Try to verify the .npy file can be loaded and create visualization
        if npy_file.exists():
            try:
                npy_data = np.load(npy_file)
                if logger:
                    logger.info(
                        f'Numpy array shape: {npy_data.shape}, dtype: {npy_data.dtype}'
                    )
                
                # Create visualization DURING PARSING while file still exists
                try:
                    image_entry._create_image_visualization(npy_file, logger)
                    if logger:
                        logger.info(f'Successfully created visualization during parsing for manifest entry')
                except Exception as viz_error:
                    if logger:
                        logger.error(f'Error creating visualization for manifest entry: {str(viz_error)}')
                        import traceback
                        logger.error(traceback.format_exc())
                        
            except Exception as e:
                if logger:
                    logger.warning(f'Could not load .npy file: {str(e)}')
        
        return image_entry
