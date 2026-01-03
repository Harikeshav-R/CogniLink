import cv2
import numpy as np
from PIL import Image
from loguru import logger
from skimage.metrics import structural_similarity as ssim


def compare_images(frame1: Image.Image, frame2: Image.Image, threshold: float = 0.85) -> bool:
    """
    Compares two images to determine if they are significantly different, based on a
    threshold value. The comparison uses Structural Similarity Index Measure (SSIM),
    which evaluates the similarity of the images' structure. For optimization, the
    images are resized to 256x256 and converted to grayscale.

    :param frame1: The first image to compare.
    :type frame1: Image.Image
    :param frame2: The second image to compare.
    :type frame2: Image.Image
    :param threshold: The similarity threshold. If the SSIM score is less than this
        value, the images are considered different. Default is 0.85.
    :type threshold: float
    :return: True if the images are significantly different; False otherwise.
    :rtype: bool
    """
    logger.trace("Entering compare_images function")
    logger.debug(f"Comparison threshold: {threshold}")

    # 1. Convert PIL images to grayscale NumPy arrays
    logger.debug("Converting PIL images to grayscale and then to NumPy arrays")
    gray1_pil = frame1.convert('L')
    gray2_pil = frame2.convert('L')
    gray1 = np.array(gray1_pil)
    gray2 = np.array(gray2_pil)

    # 2. Resize for Performance
    logger.debug("Resizing images to 256x256 for performance")
    gray1 = cv2.resize(gray1, (256, 256))
    gray2 = cv2.resize(gray2, (256, 256))

    # 3. Compute SSIM
    logger.debug("Computing Structural Similarity Index (SSIM)")
    score = ssim(gray1, gray2, full=False)
    logger.debug(f"SSIM score: {score}")

    # 5. Return Logic
    result = score < threshold
    logger.debug(f"Images are {'different' if result else 'similar'}")
    logger.trace("Exiting compare_images function")
    return bool(result)
