from unittest.mock import patch

import pytest
from PIL import Image

from app.workflows.object_permanence.tools.compare_images import compare_images


@pytest.fixture
def identical_image():
    """Returns a simple black image."""
    return Image.new("RGB", (100, 100), color="black")


@pytest.fixture
def different_image():
    """Returns a simple white image."""
    return Image.new("RGB", (100, 100), color="white")


def test_compare_images_identical(identical_image):
    """
    Tests that compare_images returns False for identical images.
    """
    # The SSIM score should be 1.0 for identical images, so it should be not different
    assert compare_images(identical_image, identical_image) is False


def test_compare_images_different(identical_image, different_image):
    """
    Tests that compare_images returns True for completely different images.
    """
    # The SSIM score should be low for different images, so it should be different
    assert compare_images(identical_image, different_image) is True


@patch("app.workflows.object_permanence.tools.compare_images.ssim")
def test_compare_images_above_threshold(mock_ssim, identical_image):
    """
    Tests that compare_images returns False when SSIM score is above the threshold.
    """
    mock_ssim.return_value = 0.9  # Above the default threshold of 0.85
    assert compare_images(identical_image, identical_image, threshold=0.85) is False
    mock_ssim.assert_called_once()


@patch("app.workflows.object_permanence.tools.compare_images.ssim")
def test_compare_images_below_threshold(mock_ssim, identical_image):
    """
    Tests that compare_images returns True when SSIM score is below the threshold.
    """
    mock_ssim.return_value = 0.8  # Below the default threshold of 0.85
    assert compare_images(identical_image, identical_image, threshold=0.85) is True
    mock_ssim.assert_called_once()
