"""
Tests for the Image Manifest Parser.

Tests the parsing of manifest.csv files that define experiments with multiple images.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from nomad.datamodel import EntryArchive

from nomad_plugin_images.parsers.manifest_parser import ManifestParser


@pytest.fixture
def test_data_dir():
    """Returns the test data directory path."""
    return Path(__file__).parent.parent / 'data'


@pytest.fixture
def temp_manifest_dir(tmp_path):
    """Create a temporary directory with manifest and test data."""
    # Create folders for two test images
    image1_dir = tmp_path / "20260323_133255"
    image2_dir = tmp_path / "20260323_133521"
    image1_dir.mkdir()
    image2_dir.mkdir()

    # Create metadata for first image
    metadata1 = {
        "timestamp": "20260323_133255",
        "shape": [100, 100, 3],
        "bit_depth": 12,
        "is_color": True,
        "exposure_ms": 5.0,
        "gain": 0,
        "min": 0,
        "max": 255,
        "circular_roi": {
            "center_x_px": 50,
            "center_y_px": 50,
            "radius_px": 20,
            "square_crop_size_px": 40,
            "bounding_box": {"x_min": 30, "y_min": 30, "x_max": 70, "y_max": 70, "width": 40, "height": 40}
        }
    }
    with open(image1_dir / "metadata.json", 'w') as f:
        json.dump(metadata1, f)

    # Create small .npy for first image
    arr1 = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
    np.save(image1_dir / "image_raw.npy", arr1)

    # Create metadata for second image
    metadata2 = {
        "timestamp": "20260323_133521",
        "shape": [150, 150, 3],
        "bit_depth": 10,
        "is_color": True,
        "exposure_ms": 3.5,
        "gain": 5,
        "min": 10,
        "max": 245,
        "circular_roi": {
            "center_x_px": 75,
            "center_y_px": 75,
            "radius_px": 30,
            "square_crop_size_px": 60,
            "bounding_box": {"x_min": 45, "y_min": 45, "x_max": 105, "y_max": 105, "width": 60, "height": 60}
        }
    }
    with open(image2_dir / "metadata.json", 'w') as f:
        json.dump(metadata2, f)

    # Create small .npy for second image
    arr2 = np.random.randint(0, 256, size=(150, 150, 3), dtype=np.uint8)
    np.save(image2_dir / "image_raw.npy", arr2)

    # Create manifest file
    manifest_csv = """step,timestamp,folder,is_repeat
0,20260323_133255,20260323_133255,False
1,20260323_133521,20260323_133521,False"""

    manifest_file = tmp_path / "exp_0_manifest.csv"
    with open(manifest_file, 'w') as f:
        f.write(manifest_csv)

    return tmp_path, manifest_file


def test_manifest_parser_initialization():
    """Test that the ManifestParser can be instantiated."""
    parser = ManifestParser(
        name='ImageManifestParser',
        description='Test parser',
        mainfile_name_re=r'.+_manifest\.csv',
    )
    assert parser is not None
    assert parser.name == 'ImageManifestParser'


def test_parse_manifest_file(temp_manifest_dir):
    """Test parsing a manifest file with multiple images."""
    tmp_path, manifest_file = temp_manifest_dir

    # Parse
    parser = ManifestParser(
        name='ImageManifestParser',
        description='Test parser',
        mainfile_name_re=r'.+_manifest\.csv',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(manifest_file), archive, logger)

    # Verify
    assert archive.data is not None
    assert hasattr(archive.data, 'steps')
    assert len(archive.data.steps) == 2

    # Verify first step
    step0 = archive.data.steps[0]
    assert step0.step == 0
    assert step0.timestamp == "20260323_133255"
    assert step0.is_repeat is False
    assert step0.image is not None
    assert step0.image.metadata.exposure_ms.magnitude == 5.0
    assert step0.image.dimensions.height == 100
    assert step0.image.dimensions.width == 100

    # Verify second step
    step1 = archive.data.steps[1]
    assert step1.step == 1
    assert step1.timestamp == "20260323_133521"
    assert step1.image is not None
    assert step1.image.metadata.exposure_ms.magnitude == 3.5
    assert step1.image.dimensions.height == 150
    assert step1.image.dimensions.width == 150


def test_parse_manifest_roi_data(temp_manifest_dir):
    """Test that ROI data is correctly parsed in manifest-based experiments."""
    tmp_path, manifest_file = temp_manifest_dir

    parser = ManifestParser(
        name='ImageManifestParser',
        description='Test parser',
        mainfile_name_re=r'.+_manifest\.csv',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(manifest_file), archive, logger)

    # Check first image's ROI
    roi = archive.data.steps[0].image.roi
    assert roi is not None
    assert roi.center_x_px == 50.0
    assert roi.center_y_px == 50.0
    assert roi.radius_px == 20.0
    assert roi.bounding_box.x_min == 30
    assert roi.bounding_box.y_min == 30
    assert roi.bounding_box.x_max == 70
    assert roi.bounding_box.y_max == 70


def test_parse_manifest_with_real_data(test_data_dir):
    """Test parsing with real test data if available."""
    manifest_file = test_data_dir / "exp_0_manifest.csv"

    if not manifest_file.exists():
        pytest.skip("Test manifest file not available")

    parser = ManifestParser(
        name='ImageManifestParser',
        description='Test parser',
        mainfile_name_re=r'.+_manifest\.csv',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(manifest_file), archive, logger)

    # Verify structure
    assert archive.data is not None
    assert hasattr(archive.data, 'steps')
    assert len(archive.data.steps) >= 1

    # Check first step
    step = archive.data.steps[0]
    assert step.image is not None
    assert step.image.metadata is not None
    assert step.image.dimensions is not None
