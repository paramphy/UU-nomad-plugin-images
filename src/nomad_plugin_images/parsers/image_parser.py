"""
Parser for image analysis data with metadata.

Reads pairs of files:
- metadata.json: Camera settings and ROI information
- image_raw.npy: Numpy array containing the raw image data

Creates an ImageData entry with complete metadata structure.
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
    ImageData,
    ImageDimensions,
    ImageMetadata,
    RegionOfInterest,
    SingleImageEntry,
)


class ImageParser(MatchingParser):
    """
    Parser for image analysis metadata and numpy array files.
    
    Reads metadata.json and associates it with the corresponding .npy file,
    creating a complete ImageData structure with all acquisition parameters
    and image information.
    """

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger,
    ) -> None:
        """
        Parse image metadata and create ImageData entry.
        
        Args:
            mainfile: Path to the metadata.json file
            archive: The entry archive to populate
            logger: Structlog logger
        """
        try:
            mainfile_path = Path(mainfile)
            
            if logger:
                logger.info(f'Parsing image data from: {mainfile_path.name}')
            
            # Create SingleImageEntry entry
            image_entry = SingleImageEntry()
            
            # Extract timestamp from parent folder name
            timestamp = mainfile_path.parent.name
            image_entry.name = f'Image_{timestamp}'
            
            # Read metadata.json
            try:
                with open(mainfile_path, 'r') as f:
                    metadata_dict = json.load(f)
                if logger:
                    logger.info(f'Loaded metadata with keys: {list(metadata_dict.keys())}')
            except Exception as e:
                if logger:
                    logger.error(f'Error reading metadata.json: {str(e)}')
                archive.data = image_entry
                return
            
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
            npy_file = mainfile_path.parent / 'image_raw.npy'
            if npy_file.exists():
                # Store relative path from the folder containing metadata.json
                # This is more reliable when files are moved/extracted
                image_entry.npy_file_path = str(npy_file.relative_to(npy_file.parent.parent))
                if logger:
                    logger.info(f'Found corresponding .npy file: {npy_file.name}')
                    logger.info(f'Storing relative path: {image_entry.npy_file_path}')
            else:
                if logger:
                    logger.warning(f'No image_raw.npy file found in {mainfile_path.parent}')
            
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
                            logger.info(f'Successfully created visualization during parsing')
                    except Exception as viz_error:
                        if logger:
                            logger.error(f'Error creating visualization during parsing: {str(viz_error)}')
                            import traceback
                            logger.error(traceback.format_exc())
                            
                except Exception as e:
                    if logger:
                        logger.warning(f'Could not load .npy file: {str(e)}')
            
            archive.data = image_entry
            
            if logger:
                logger.info(f'Successfully parsed image: {image_entry.name}')
        
        except Exception as e:
            if logger:
                logger.error(f'Error parsing image data: {str(e)}')
                import traceback

                logger.error(traceback.format_exc())
            # Create minimal entry on error
            archive.data = SingleImageEntry()
