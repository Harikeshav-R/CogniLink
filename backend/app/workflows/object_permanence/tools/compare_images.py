import cv2
import numpy as np
from PIL import Image
from langchain.tools import tool
from skimage.metrics import structural_similarity as ssim


@tool
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
    # 1. Convert PIL Images to NumPy arrays (RGB)
    img1_np = np.array(frame1)
    img2_np = np.array(frame2)

    # 2. Convert to Grayscale (SSIM works best on structure, color is noise)
    # Note: PIL uses RGB, OpenCV default is BGR, but since we convert both identical ways,
    # generic RGB2GRAY works fine for structure comparison.
    gray1 = cv2.cvtColor(img1_np, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2GRAY)

    # 3. Resize for Performance (Critical Optimization)
    # comparing 4k images is slow; 256x256 is enough for "Did something move?"
    gray1 = cv2.resize(gray1, (256, 256))
    gray2 = cv2.resize(gray2, (256, 256))

    # 4. Compute SSIM
    # full=True is not strictly necessary here unless you want the diff map,
    # setting it to False is slightly faster for just the score.
    score, _ = ssim(gray1, gray2, full=False)

    # 5. Return Logic
    # If score < threshold -> Return True (Yes, they are different)
    return score < threshold
