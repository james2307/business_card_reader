import cv2
import numpy as np

def preprocess_image(image):
    """
    Preprocess the image for better text detection

    Args:
        image: numpy array of the input image

    Returns:
        processed_image: numpy array of the processed image
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Apply dilation to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    gray = cv2.dilate(gray, kernel, iterations=1)

    # Apply bilateral filter to remove noise while keeping edges sharp
    processed = cv2.bilateralFilter(gray, 9, 75, 75)

    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    processed = clahe.apply(processed)

    return processed

def detect_text_regions(image):
    """
    Detect text regions in the image using contour detection

    Args:
        image: preprocessed grayscale image

    Returns:
        text_regions: list of bounding rectangles containing text
    """
    # Find contours
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on area and aspect ratio
    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect_ratio = w / float(h)

        if area > 100 and 0.1 < aspect_ratio < 10:
            text_regions.append((x, y, w, h))

    return text_regions
