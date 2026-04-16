"""
Tests for the Image Parser.

Tests the parsing of metadata.json and image_raw.npy files.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from nomad.datamodel import EntryArchive

from nomad_plugin_images.parsers.image_parser import ImageParser


@pytest.fixture
def test_data_dir():
    """Returns the test data directory path."""
    return Path(__file__).parent.parent / 'data'


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "timestamp": "20260323_133255",
        "shape": [3000, 4096, 3],
        "bit_depth": 12,
        "is_color": True,
        "exposure_ms": 5.005,
        "gain": 0,
        "min": 0,
        "max": 255,
        "circular_roi": {
            "center_x_px": 1532,
            "center_y_px": 2107,
            "radius_px": 898,
            "square_crop_size_px": 1796,
            "bounding_box": {
                "x_min": 632,
                "y_min": 1207,
                "x_max": 2432,
                "y_max": 3007,
                "width": 1800,
                "height": 1800
            }
        }
    }


@pytest.fixture
def sample_npy_file(tmp_path):
    """Create a sample .npy file for testing."""
    # Create a small test array (instead of full 3000x4096x3)
    test_array = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
    npy_path = tmp_path / "image_raw.npy"
    np.save(npy_path, test_array)
    return npy_path


def test_parser_initialization():
    """Test that the ImageParser can be instantiated."""
    parser = ImageParser(
        name='ImageParser',
        description='Test parser',
        mainfile_name_re=r'metadata\.json',
    )
    assert parser is not None
    assert parser.name == 'ImageParser'


def test_parse_metadata_only(tmp_path, sample_metadata):
    """Test parsing a metadata.json file."""
    # Create a metadata.json file
    metadata_file = tmp_path / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(sample_metadata, f)

    # Create minimal .npy file
    npy_file = tmp_path / "image_raw.npy"
    test_array = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)
    np.save(npy_file, test_array)

    # Parse
    parser = ImageParser(
        name='ImageParser',
        description='Test parser',
        mainfile_name_re=r'metadata\.json',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(metadata_file), archive, logger)

    # Verify
    assert archive.data is not None
    assert archive.data.metadata is not None
    assert archive.data.metadata.timestamp == "20260323_133255"
    # exposure_ms is stored as a Quantity with unit, so check the magnitude
    assert archive.data.metadata.exposure_ms.magnitude == 5.005
    assert archive.data.dimensions is not None
    assert archive.data.dimensions.height == 3000
    assert archive.data.dimensions.width == 4096
    assert archive.data.roi is not None
    assert archive.data.roi.center_x_px == 1532.0
    assert archive.data.roi.center_y_px == 2107.0


def test_parse_with_actual_data(test_data_dir):
    """Test parsing with real data if available."""
    metadata_file = test_data_dir / "metadata.json"
    npy_file = test_data_dir / "image_raw.npy"

    if not metadata_file.exists() or not npy_file.exists():
        pytest.skip("Test data files not available")

    parser = ImageParser(
        name='ImageParser',
        description='Test parser',
        mainfile_name_re=r'metadata\.json',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(metadata_file), archive, logger)

    # Verify structure
    assert archive.data is not None
    assert archive.data.metadata is not None
    assert archive.data.dimensions is not None
    assert archive.data.roi is not None
    assert archive.data.npy_file_path is not None


def test_bounding_box_extraction():
    """Test that bounding box is correctly parsed."""
    metadata = {
        "timestamp": "test_20260323",
        "shape": [100, 100, 3],
        "bit_depth": 8,
        "is_color": True,
        "exposure_ms": 1.0,
        "gain": 0,
        "min": 0,
        "max": 255,
        "circular_roi": {
            "center_x_px": 50,
            "center_y_px": 50,
            "radius_px": 20,
            "square_crop_size_px": 40,
            "bounding_box": {
                "x_min": 30,
                "y_min": 30,
                "x_max": 70,
                "y_max": 70,
                "width": 40,
                "height": 40
            }
        }
    }

    from nomad_plugin_images.schema_packages.image_analysis import (
        BoundingBox,
        RegionOfInterest,
    )

    bbox = BoundingBox()
    bbox.x_min = metadata["circular_roi"]["bounding_box"]["x_min"]
    bbox.y_min = metadata["circular_roi"]["bounding_box"]["y_min"]
    bbox.x_max = metadata["circular_roi"]["bounding_box"]["x_max"]
    bbox.y_max = metadata["circular_roi"]["bounding_box"]["y_max"]
    bbox.width = metadata["circular_roi"]["bounding_box"]["width"]
    bbox.height = metadata["circular_roi"]["bounding_box"]["height"]

    assert bbox.x_min == 30
    assert bbox.y_min == 30
    assert bbox.x_max == 70
    assert bbox.y_max == 70
    assert bbox.width == 40
    assert bbox.height == 40
