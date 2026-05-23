"""
Tests for the Hierarchical Sample Parser.

Tests the parsing of hierarchical sample data with synthesis info and experimental results.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from nomad.datamodel import EntryArchive

from nomad_plugin_images.parsers.hierarchical_parser import HierarchicalSampleParser


@pytest.fixture
def test_data_dir():
    """Returns the test data directory path."""
    return Path(__file__).parent.parent / 'data'


@pytest.fixture
def temp_sample_hierarchy(tmp_path):
    """Create a temporary hierarchical sample directory structure."""
    # Create sample folder
    sample_folder = tmp_path / 'CuSnZnS_31_123456'
    sample_folder.mkdir()

    # Create sample synthesis JSON
    synthesis_json = {
        'date': '2026-03-05',
        'sample_id': '249606',
        'sample_name': 'CuSnZnS_31',
        'elements': 'Cu, Sn, Zn',
        'cu_source_power': '94',
        'sn_source_power': '70',
        'zn_source_power': '64',
        'pressure_mtorr': '15',
        'source_temperature_degc': '130',
        'process_temperature_degc': '550',
        'chamber_pressure_mbar': '100',
        'process_time_min': '10',
        'cooling_time_min': '60',
        'cooling_rate_degc_min': '8.333333333'
    }
    synthesis_file = sample_folder / 'CuSnZnS_31.json'
    with open(synthesis_file, 'w') as f:
        json.dump(synthesis_json, f)

    # Create first experimental folder
    exp1_folder = sample_folder / '20260323_133521'
    exp1_folder.mkdir()

    metadata1 = {
        'timestamp': '20260323_133521',
        'shape': [100, 100, 3],
        'bit_depth': 12,
        'is_color': True,
        'exposure_ms': 2.005,
        'gain': 0,
        'min': 0,
        'max': 255,
        'circular_roi': {
            'center_x_px': 50,
            'center_y_px': 50,
            'radius_px': 20,
            'square_crop_size_px': 40,
            'bounding_box': {
                'x_min': 30,
                'y_min': 30,
                'x_max': 70,
                'y_max': 70,
                'width': 40,
                'height': 40
            }
        }
    }
    with open(exp1_folder / 'metadata.json', 'w') as f:
        json.dump(metadata1, f)

    # Create .npy file
    arr1 = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
    np.save(exp1_folder / 'image_raw.npy', arr1)

    # Create second experimental folder
    exp2_folder = sample_folder / '20260323_140000'
    exp2_folder.mkdir()

    metadata2 = {
        'timestamp': '20260323_140000',
        'shape': [100, 100, 3],
        'bit_depth': 12,
        'is_color': True,
        'exposure_ms': 2.5,
        'gain': 5,
        'min': 0,
        'max': 255,
        'circular_roi': {
            'center_x_px': 50,
            'center_y_px': 50,
            'radius_px': 20,
            'square_crop_size_px': 40,
            'bounding_box': {
                'x_min': 30,
                'y_min': 30,
                'x_max': 70,
                'y_max': 70,
                'width': 40,
                'height': 40
            }
        }
    }
    with open(exp2_folder / 'metadata.json', 'w') as f:
        json.dump(metadata2, f)

    arr2 = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
    np.save(exp2_folder / 'image_raw.npy', arr2)

    return sample_folder, synthesis_file


def test_hierarchical_parser_initialization():
    """Test that the HierarchicalSampleParser can be instantiated."""
    parser = HierarchicalSampleParser(
        name='HierarchicalSampleParser',
        description='Test parser',
        mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
    )
    assert parser is not None
    assert parser.name == 'HierarchicalSampleParser'


def test_parse_hierarchical_sample(temp_sample_hierarchy):
    """Test parsing a complete hierarchical sample structure."""
    sample_folder, synthesis_file = temp_sample_hierarchy

    parser = HierarchicalSampleParser(
        name='HierarchicalSampleParser',
        description='Test parser',
        mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(synthesis_file), archive, logger)

    # Verify main entry
    assert archive.data is not None
    assert archive.data.name == 'CuSnZnS_31_123456'
    assert archive.data.synthesis_info is not None

    # Verify synthesis info
    synthesis = archive.data.synthesis_info
    assert synthesis.sample_id == '249606'
    assert synthesis.sample_name == 'CuSnZnS_31'
    assert synthesis.elements == 'Cu, Sn, Zn'
    assert synthesis.cu_source_power.magnitude == 94.0
    assert synthesis.sn_source_power.magnitude == 70.0
    assert synthesis.zn_source_power.magnitude == 64.0

    # Verify experimental results
    assert len(archive.data.experimental_results) == 2

    # Verify first experiment
    exp1 = archive.data.experimental_results[0]
    assert exp1.experiment_id == '20260323_133521'
    assert len(exp1.images) == 1
    assert exp1.images[0].metadata.exposure_ms.magnitude == 2.005

    # Verify second experiment
    exp2 = archive.data.experimental_results[1]
    assert exp2.experiment_id == '20260323_140000'
    assert len(exp2.images) == 1
    assert exp2.images[0].metadata.exposure_ms.magnitude == 2.5


def test_parse_synthesis_parameters(temp_sample_hierarchy):
    """Test that all synthesis parameters are correctly parsed."""
    sample_folder, synthesis_file = temp_sample_hierarchy

    parser = HierarchicalSampleParser(
        name='HierarchicalSampleParser',
        description='Test parser',
        mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(synthesis_file), archive, logger)

    synthesis = archive.data.synthesis_info
    # Handle both Quantity objects and plain floats
    assert (synthesis.pressure_mtorr.magnitude if hasattr(synthesis.pressure_mtorr, 'magnitude') else synthesis.pressure_mtorr) == 15.0
    assert (synthesis.chamber_pressure_mbar.magnitude if hasattr(synthesis.chamber_pressure_mbar, 'magnitude') else synthesis.chamber_pressure_mbar) == 100.0
    assert (synthesis.process_time_min.magnitude if hasattr(synthesis.process_time_min, 'magnitude') else synthesis.process_time_min) == 10.0
    assert (synthesis.cooling_time_min.magnitude if hasattr(synthesis.cooling_time_min, 'magnitude') else synthesis.cooling_time_min) == 60.0
    cooling_rate = synthesis.cooling_rate_degc_min.magnitude if hasattr(synthesis.cooling_rate_degc_min, 'magnitude') else synthesis.cooling_rate_degc_min
    assert cooling_rate == pytest.approx(8.333333333, rel=1e-5)


def test_parse_image_metadata_in_experiments(temp_sample_hierarchy):
    """Test that image metadata is correctly parsed within experiments."""
    sample_folder, synthesis_file = temp_sample_hierarchy

    parser = HierarchicalSampleParser(
        name='HierarchicalSampleParser',
        description='Test parser',
        mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(synthesis_file), archive, logger)

    # Check image dimensions from first experiment
    image = archive.data.experimental_results[0].images[0]
    assert image.dimensions.height == 100
    assert image.dimensions.width == 100
    assert image.dimensions.channels == 3
    assert image.dimensions.is_color is True

    # Check ROI
    assert image.roi is not None
    assert image.roi.center_x_px == 50.0
    assert image.roi.center_y_px == 50.0
    assert image.roi.bounding_box.x_min == 30
    assert image.roi.bounding_box.y_min == 30


def test_parse_real_sample_data(test_data_dir):
    """Test parsing with real test data if available."""
    sample_folders = list(test_data_dir.glob('CuSnZnS_*_*'))

    if not sample_folders:
        pytest.skip('No sample folders available')

    sample_folder = sample_folders[0]

    # Find JSON file
    json_files = list(sample_folder.glob('*.json'))
    if not json_files:
        pytest.skip('No JSON file in sample folder')

    synthesis_file = json_files[0]

    parser = HierarchicalSampleParser(
        name='HierarchicalSampleParser',
        description='Test parser',
        mainfile_name_re=r'^[A-Za-z0-9_]+\.json$',
    )
    archive = EntryArchive()
    logger = logging.getLogger()

    parser.parse(str(synthesis_file), archive, logger)

    # Verify structure
    assert archive.data is not None
    assert archive.data.synthesis_info is not None
    assert len(archive.data.experimental_results) >= 1

    # Check first experiment has images
    if archive.data.experimental_results:
        exp = archive.data.experimental_results[0]
        assert len(exp.images) >= 1
        assert exp.images[0].metadata is not None
        assert exp.images[0].dimensions is not None
