#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, SectionProperties
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = Package(name='Image Analysis Schema')


class BoundingBox(ArchiveSection):
    """
    Bounding box definition for the region of interest.
    Represents the rectangular boundaries of a circular ROI.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "x_min",
                    "y_min",
                    "x_max",
                    "y_max",
                    "width",
                    "height",
                ],
            ),
        ),
    )

    x_min = Quantity(
        type=int,
        description='Minimum X coordinate (left edge) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    y_min = Quantity(
        type=int,
        description='Minimum Y coordinate (top edge) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    x_max = Quantity(
        type=int,
        description='Maximum X coordinate (right edge) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    y_max = Quantity(
        type=int,
        description='Maximum Y coordinate (bottom edge) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    width = Quantity(
        type=int,
        description='Width of bounding box in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    height = Quantity(
        type=int,
        description='Height of bounding box in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the bounding box."""
        super().normalize(archive, logger)


class RegionOfInterest(ArchiveSection):
    """
    Circular region of interest (ROI) information.
    Defines the area of interest in the image with center, radius, and bounding box.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "center_x_px",
                    "center_y_px",
                    "radius_px",
                    "square_crop_size_px",
                    "bounding_box",
                ],
            ),
        ),
    )

    center_x_px = Quantity(
        type=float,
        description='X coordinate of circle center in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    center_y_px = Quantity(
        type=float,
        description='Y coordinate of circle center in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    radius_px = Quantity(
        type=float,
        description='Radius of the circular ROI in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    square_crop_size_px = Quantity(
        type=int,
        description='Size of the square crop around the circle in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    bounding_box = SubSection(
        section_def=BoundingBox,
        description='Bounding box coordinates for the ROI',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the region of interest."""
        super().normalize(archive, logger)


class ImageDimensions(ArchiveSection):
    """
    Image dimension and shape information.
    Contains the resolution, number of color channels, and pixel value range.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "height",
                    "width",
                    "channels",
                    "is_color",
                    "pixel_value_min",
                    "pixel_value_max",
                ],
            ),
        ),
    )

    height = Quantity(
        type=int,
        description='Image height (number of rows) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    width = Quantity(
        type=int,
        description='Image width (number of columns) in pixels',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    channels = Quantity(
        type=int,
        description='Number of color channels (e.g., 3 for RGB)',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    is_color = Quantity(
        type=bool,
        description='Whether the image is color (True) or grayscale (False)',
        a_eln={
            "component": "BoolEditQuantity",
        },
    )

    pixel_value_min = Quantity(
        type=int,
        description='Minimum pixel value in the image',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    pixel_value_max = Quantity(
        type=int,
        description='Maximum pixel value in the image',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the image dimensions."""
        super().normalize(archive, logger)


class ImageMetadata(ArchiveSection):
    """
    Acquisition settings and metadata for the image.
    Contains camera settings like exposure time, gain, and bit depth.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "timestamp",
                    "exposure_ms",
                    "gain",
                    "bit_depth",
                ],
            ),
        ),
    )

    timestamp = Quantity(
        type=str,
        description='Timestamp when the image was acquired (ISO format or custom format)',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    exposure_ms = Quantity(
        type=float,
        description='Exposure time in milliseconds',
        a_eln={
            "component": "NumberEditQuantity",
            "defaultDisplayUnit": "millisecond",
        },
        unit="millisecond",
    )

    gain = Quantity(
        type=int,
        description='Camera gain setting (typically 0-100)',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    bit_depth = Quantity(
        type=int,
        description='Bit depth of the image (e.g., 8, 10, 12, 16 bits)',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the image metadata."""
        super().normalize(archive, logger)


class ImageData(PlotSection, ArchiveSection):
    """
    Complete image data entry containing acquisition metadata, dimensions, and ROI.
    
    Represents one image capture with:
    - Acquisition settings (exposure, gain, bit depth, timestamp)
    - Image dimensions (height, width, channels)
    - Region of interest (circular ROI with bounding box)
    - Reference to the numpy array file
    - Visualization plots (image with ROI overlay)
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "name",
                    "metadata",
                    "dimensions",
                    "roi",
                    "npy_file_path",
                ],
            ),
        ),
    )

    name = Quantity(
        type=str,
        description='Name or identifier for this image entry',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    metadata = SubSection(
        section_def=ImageMetadata,
        description='Acquisition settings and camera parameters',
    )

    dimensions = SubSection(
        section_def=ImageDimensions,
        description='Image dimensions and shape information',
    )

    roi = SubSection(
        section_def=RegionOfInterest,
        description='Circular region of interest information',
    )

    npy_file_path = Quantity(
        type=str,
        description='Path to the numpy array file (.npy) containing the raw image data',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        Normalize the ImageData entry.
        Note: Visualization is created during parsing when files are available.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)
    
    def _create_image_visualization(self, npy_path: Path, logger) -> None:
        """
        Create a Plotly visualization of the image with ROI overlay.
        Optimized for large images by downsampling for display.
        
        Args:
            npy_path: Path to the .npy file
            logger: Structlog logger
        """
        try:
            # Load numpy array header only first to check size
            img_data = np.load(npy_path)
            
            if logger:
                logger.info(f'Loaded image with shape: {img_data.shape}, dtype: {img_data.dtype}')
            
            # Downsample large images for faster visualization
            max_display_size = 1000
            img_display = img_data.copy()
            
            if img_display.shape[0] > max_display_size or img_display.shape[1] > max_display_size:
                # Calculate downsampling factor
                scale_h = max(1, img_display.shape[0] // max_display_size)
                scale_w = max(1, img_display.shape[1] // max_display_size)
                scale = max(scale_h, scale_w)
                
                # Downsample using slicing (fast)
                img_display = img_display[::scale, ::scale]
                if len(img_display.shape) == 3:
                    img_display = img_display[:, :, :3] if img_display.shape[2] >= 3 else img_display
                
                if logger:
                    logger.info(f'Downsampled image from {img_data.shape} to {img_display.shape} (scale factor: {scale}x)')
            
            # Normalize image data for visualization (0-255)
            img_normalized = img_display.astype(np.float32)
            if img_normalized.max() > 0:
                img_normalized = (img_normalized / img_normalized.max() * 255).astype(np.uint8)
            
            # For RGB images, use as-is; for single channel, convert to grayscale
            if len(img_display.shape) == 3 and img_display.shape[2] >= 3:
                # Use first 3 channels as RGB
                display_data = img_normalized[:, :, :3]
            elif len(img_display.shape) == 3 and img_display.shape[2] == 1:
                # Single channel, repeat to RGB
                display_data = np.repeat(img_normalized, 3, axis=2)
            elif len(img_display.shape) == 2:
                # Grayscale, repeat to RGB
                display_data = np.stack([img_normalized, img_normalized, img_normalized], axis=2)
            else:
                if logger:
                    logger.warning(f'Unexpected image shape: {img_display.shape}')
                return
            
            # Create Plotly figure with image
            fig = go.Figure()
            
            # Add image (note: go.Image doesn't support showscale)
            fig.add_trace(
                go.Image(
                    z=display_data.astype(np.uint8),
                    name='Image',
                )
            )
            
            # Add ROI visualization if available
            if self.roi and self.roi.bounding_box:
                bbox = self.roi.bounding_box
                
                # If we downsampled, scale ROI coordinates
                if 'scale' in locals():
                    bbox_x_min = bbox.x_min // scale
                    bbox_y_min = bbox.y_min // scale
                    bbox_x_max = bbox.x_max // scale
                    bbox_y_max = bbox.y_max // scale
                else:
                    bbox_x_min = bbox.x_min
                    bbox_y_min = bbox.y_min
                    bbox_x_max = bbox.x_max
                    bbox_y_max = bbox.y_max
                
                # Add rectangle for bounding box
                fig.add_shape(
                    type='rect',
                    x0=bbox_x_min, y0=bbox_y_min,
                    x1=bbox_x_max, y1=bbox_y_max,
                    line=dict(color='red', width=3),
                    name='ROI Bounding Box',
                    label=dict(text='ROI', textposition='top center'),
                )
                
                # Add circle for circular ROI
                if self.roi.center_x_px is not None and self.roi.center_y_px is not None:
                    radius = self.roi.radius_px if self.roi.radius_px else 50
                    
                    # Scale center if downsampled
                    if 'scale' in locals():
                        center_x = self.roi.center_x_px // scale
                        center_y = self.roi.center_y_px // scale
                        display_radius = radius // scale
                    else:
                        center_x = self.roi.center_x_px
                        center_y = self.roi.center_y_px
                        display_radius = radius
                    
                    # Create circle using path
                    theta = np.linspace(0, 2 * np.pi, 50)  # Reduced points for speed
                    circle_x = center_x + display_radius * np.cos(theta)
                    circle_y = center_y + display_radius * np.sin(theta)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=circle_x, y=circle_y,
                            mode='lines',
                            name='Circular ROI',
                            line=dict(color='blue', width=2),
                            hovertemplate='<b>Circular ROI</b><br>Center: (%{customdata[0]:.1f}, %{customdata[1]:.1f})<br>Radius: %{customdata[2]:.1f}px',
                            customdata=np.column_stack((
                                np.full_like(circle_x, center_x),
                                np.full_like(circle_y, center_y),
                                np.full_like(circle_x, display_radius)
                            )),
                        )
                    )
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text=f'Image: {self.name}',
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title='Pixel X',
                yaxis_title='Pixel Y',
                template='plotly_white',
                dragmode='zoom',
                hovermode='closest',
                width=800,
                height=700,
                yaxis=dict(scaleanchor='x', scaleratio=1),
                xaxis=dict(scaleanchor='y', scaleratio=1),
            )
            
            # Store the figure
            self.figures = [PlotlyFigure(label='Image with ROI', figure=fig.to_plotly_json())]
            
            if logger:
                logger.info(f'Successfully created image visualization with ROI overlay')
        
        except Exception as e:
            if logger:
                logger.error(f'Error in image visualization: {str(e)}')
                import traceback
                logger.error(traceback.format_exc())


class ImageStep(ArchiveSection):
    """
    A single image acquisition step in an experiment.
    
    Contains metadata about one image measurement including:
    - Step number and timestamp
    - Link to the full image data
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "step",
                    "timestamp",
                    "is_repeat",
                    "image",
                ],
            ),
        ),
    )

    step = Quantity(
        type=int,
        description='Step number in the experiment',
        a_eln={
            "component": "NumberEditQuantity",
        },
    )

    timestamp = Quantity(
        type=str,
        description='Timestamp of the image acquisition',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    is_repeat = Quantity(
        type=bool,
        description='Whether this is a repeat measurement',
        a_eln={
            "component": "BoolEditQuantity",
        },
    )

    image = SubSection(
        section_def=ImageData,
        description='The image data for this step',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        Normalize the ImageStep entry.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)


class ImageExperimentRun(EntryData, ArchiveSection):
    """
    An image experiment run containing multiple image acquisition steps.
    
    This is the main entry point for manifest-based image analysis,
    containing:
    - Experiment metadata (run_id, name)
    - Multiple image steps (from manifest file)
    - Full traceability of all images in the experiment
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "name",
                    "run_id",
                    "steps",
                ],
            ),
        ),
    )

    name = Quantity(
        type=str,
        description='Name of the experiment run',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    run_id = Quantity(
        type=str,
        description='Unique identifier for this experiment run',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    steps = SubSection(
        section_def=ImageStep,
        repeats=True,
        description='List of image acquisition steps in this experiment',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        Normalize the ImageExperimentRun entry.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)


class SingleImageEntry(PlotSection, EntryData, ArchiveSection):
    """
    A standalone image entry (not part of an experiment run).
    
    This is used when uploading a single metadata.json file directly
    without a manifest file. Includes visualization plots.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "name",
                    "metadata",
                    "dimensions",
                    "roi",
                    "npy_file_path",
                ],
            ),
        ),
    )

    name = Quantity(
        type=str,
        description='Name or identifier for this image entry',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    metadata = SubSection(
        section_def=ImageMetadata,
        description='Acquisition settings and camera parameters',
    )

    dimensions = SubSection(
        section_def=ImageDimensions,
        description='Image dimensions and shape information',
    )

    roi = SubSection(
        section_def=RegionOfInterest,
        description='Circular region of interest information',
    )

    npy_file_path = Quantity(
        type=str,
        description='Path to the numpy array file (.npy) containing the raw image data',
        a_eln={
            "component": "StringEditQuantity",
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        Normalize the SingleImageEntry.
        Note: Visualization is created during parsing when files are available.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)
    
    def _create_image_visualization(self, npy_path: Path, logger) -> None:
        """
        Create a Plotly visualization of the image with ROI overlay.
        Optimized for large images by downsampling for display.
        (Same as ImageData._create_image_visualization)
        
        Args:
            npy_path: Path to the .npy file
            logger: Structlog logger
        """
        try:
            # Load numpy array header only first to check size
            img_data = np.load(npy_path)
            
            if logger:
                logger.info(f'Loaded image with shape: {img_data.shape}, dtype: {img_data.dtype}')
            
            # Downsample large images for faster visualization
            max_display_size = 1000
            img_display = img_data.copy()
            
            if img_display.shape[0] > max_display_size or img_display.shape[1] > max_display_size:
                # Calculate downsampling factor
                scale_h = max(1, img_display.shape[0] // max_display_size)
                scale_w = max(1, img_display.shape[1] // max_display_size)
                scale = max(scale_h, scale_w)
                
                # Downsample using slicing (fast)
                img_display = img_display[::scale, ::scale]
                if len(img_display.shape) == 3:
                    img_display = img_display[:, :, :3] if img_display.shape[2] >= 3 else img_display
                
                if logger:
                    logger.info(f'Downsampled image from {img_data.shape} to {img_display.shape} (scale factor: {scale}x)')
            
            # Normalize image data for visualization (0-255)
            img_normalized = img_display.astype(np.float32)
            if img_normalized.max() > 0:
                img_normalized = (img_normalized / img_normalized.max() * 255).astype(np.uint8)
            
            # For RGB images, use as-is; for single channel, convert to grayscale
            if len(img_display.shape) == 3 and img_display.shape[2] >= 3:
                # Use first 3 channels as RGB
                display_data = img_normalized[:, :, :3]
            elif len(img_display.shape) == 3 and img_display.shape[2] == 1:
                # Single channel, repeat to RGB
                display_data = np.repeat(img_normalized, 3, axis=2)
            elif len(img_display.shape) == 2:
                # Grayscale, repeat to RGB
                display_data = np.stack([img_normalized, img_normalized, img_normalized], axis=2)
            else:
                if logger:
                    logger.warning(f'Unexpected image shape: {img_display.shape}')
                return
            
            # Create Plotly figure with image
            fig = go.Figure()
            
            # Add image
            fig.add_trace(
                go.Image(
                    z=display_data.astype(np.uint8),
                    name='Image',
                    showscale=False,
                )
            )
            
            # Add ROI visualization if available
            if self.roi and self.roi.bounding_box:
                bbox = self.roi.bounding_box
                
                # If we downsampled, scale ROI coordinates
                if 'scale' in locals():
                    bbox_x_min = bbox.x_min // scale
                    bbox_y_min = bbox.y_min // scale
                    bbox_x_max = bbox.x_max // scale
                    bbox_y_max = bbox.y_max // scale
                else:
                    bbox_x_min = bbox.x_min
                    bbox_y_min = bbox.y_min
                    bbox_x_max = bbox.x_max
                    bbox_y_max = bbox.y_max
                
                # Add rectangle for bounding box
                fig.add_shape(
                    type='rect',
                    x0=bbox_x_min, y0=bbox_y_min,
                    x1=bbox_x_max, y1=bbox_y_max,
                    line=dict(color='red', width=3),
                    name='ROI Bounding Box',
                    label=dict(text='ROI', textposition='top center'),
                )
                
                # Add circle for circular ROI
                if self.roi.center_x_px is not None and self.roi.center_y_px is not None:
                    radius = self.roi.radius_px if self.roi.radius_px else 50
                    
                    # Scale center if downsampled
                    if 'scale' in locals():
                        center_x = self.roi.center_x_px // scale
                        center_y = self.roi.center_y_px // scale
                        display_radius = radius // scale
                    else:
                        center_x = self.roi.center_x_px
                        center_y = self.roi.center_y_px
                        display_radius = radius
                    
                    # Create circle using path
                    theta = np.linspace(0, 2 * np.pi, 50)  # Reduced points for speed
                    circle_x = center_x + display_radius * np.cos(theta)
                    circle_y = center_y + display_radius * np.sin(theta)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=circle_x, y=circle_y,
                            mode='lines',
                            name='Circular ROI',
                            line=dict(color='blue', width=2),
                            hovertemplate='<b>Circular ROI</b><br>Center: (%{customdata[0]:.1f}, %{customdata[1]:.1f})<br>Radius: %{customdata[2]:.1f}px',
                            customdata=np.column_stack((
                                np.full_like(circle_x, center_x),
                                np.full_like(circle_y, center_y),
                                np.full_like(circle_x, display_radius)
                            )),
                        )
                    )
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text=f'Image: {self.name}',
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title='Pixel X',
                yaxis_title='Pixel Y',
                template='plotly_white',
                dragmode='zoom',
                hovermode='closest',
                width=800,
                height=700,
                yaxis=dict(scaleanchor='x', scaleratio=1),
                xaxis=dict(scaleanchor='y', scaleratio=1),
            )
            
            # Store the figure
            self.figures = [PlotlyFigure(label='Image with ROI', figure=fig.to_plotly_json())]
            
            if logger:
                logger.info(f'Successfully created image visualization with ROI overlay')
        
        except Exception as e:
            if logger:
                logger.error(f'Error in image visualization: {str(e)}')
                import traceback
                logger.error(traceback.format_exc())


m_package.__init_metainfo__()
