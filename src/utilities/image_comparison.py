from typing import Tuple
import cv2 as cv
import numpy as np
from skimage.metrics import structural_similarity
from src.utilities.file_helper import read_last_reference_image_parameters
from scipy.ndimage import distance_transform_edt


def calculate_intersection_and_union(edges1, edges2):
    intersection = np.logical_and(edges1, edges2)
    union = np.logical_or(edges1, edges2)
    return intersection, union


def dice_coefficient(intersection: np.ndarray, edges1: np.ndarray, edges2: np.ndarray) -> float:
    """
    Calculate Dice Coefficient for two images.
    """
    dice_coeff = 2. * intersection.sum() / (edges1.sum() + edges2.sum())
    print(f"Dice Benzerlik oranı: {dice_coeff}")
    return dice_coeff


# def jaccard_index(intersection: np.ndarray, union: np.ndarray) -> float:
#     """
#     Calculate Jaccard Index for two images.
#     """
#     jaccard_index = intersection.sum() / float(union.sum())
#     print('Jaccard Index: ', jaccard_index)
#     return jaccard_index


def bhattacharyya_distance(edges1: np.ndarray, edges2: np.ndarray) -> float:
    """
    Calculate Bhattacharyya Distance for two images.
    """
    hist1 = cv.calcHist([edges1], [0], None, [256], [0, 256])
    hist2 = cv.calcHist([edges2], [0], None, [256], [0, 256])
    cv.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    cv.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    bhattacharyya_distance_score = cv.compareHist(hist1, hist2, cv.HISTCMP_BHATTACHARYYA)
    print("Bhattacharyya Distance: ", bhattacharyya_distance_score)
    return bhattacharyya_distance_score


def find_centroid(image):
    contours, _ = cv.findContours(image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # En büyük kontürü bul
    cnt = max(contours, key=cv.contourArea)

    # Momentleri hesapla
    M = cv.moments(cnt)
    print(f"Max Kontür: {M}")

    # Merkezoidi bul
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])

    return cx, cy


def filter_images(reference_image_name: str, reference_image, product_image) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Filter images using parameters from last reference image.
    """
    reference_image_gray = cv.cvtColor(np.array(reference_image), cv.COLOR_RGB2GRAY)
    product_image_gray = cv.cvtColor(np.array(product_image), cv.COLOR_RGB2GRAY)
    params = read_last_reference_image_parameters(reference_image_name)
    filtered_reference_image = cv.bilateralFilter(
        reference_image_gray,
        params[0],
        params[1],
        params[2]
    )
    filtered_product_image = cv.bilateralFilter(
        product_image_gray,
        params[0],
        params[1],
        params[2]
    )
    edge_detected_reference_image = cv.Canny(
        filtered_reference_image,
        params[3],
        params[4]
    )
    edge_detected_product_image = cv.Canny(
        filtered_product_image,
        params[3],
        params[4]
    )
    return filtered_reference_image, filtered_product_image, edge_detected_reference_image, edge_detected_product_image


def find_the_difference_between_two_images(reference_image=None, reference_image_edges=None, product_image_edges=None, euclidean_distance=None):
    reference_image_bgr = cv.cvtColor(np.array(reference_image), cv.COLOR_RGB2BGR)

    # İki edge görüntüsü arasındaki farkı hesaplayın
    diff = cv.absdiff(reference_image_edges, product_image_edges)

    # Sadece product_image_edges'teki ve diff'te olan kenarları alın
    # shifted_edges_only = cv.bitwise_and(diff, product_image_edges)
    #
    # if euclidean_distance > 50:
    #     h, w = shifted_edges_only.shape
    #
    #     for y in range(h):
    #         for x in range(w):
    #             if shifted_edges_only[y, x] != 0:  # Farklı ve kaymış kenar varsa
    #                 reference_image_bgr[y, x] = [0, 0, 255]
    #
    #     return reference_image_bgr

    h, w = diff.shape

    for y in range(h):
        for x in range(w):
            if diff[y, x] != 0:  # Fark varsa
                reference_image_bgr[y, x] = [0, 0, 255]

    return reference_image_bgr


def calculate_similarity(reference_image_name: str, sensitivity: float = 1.0, reference_image=None, product_image=None) -> float:
    """
    Calculate similarity between reference image and product image.
    """
    filtered_reference_image, filtered_product_image, edge_detected_reference_image, edge_detected_product_image = filter_images(
        reference_image_name, reference_image, product_image
    )
    reference_image_edges = (edge_detected_reference_image > 0).astype(int)
    product_image_edges = (edge_detected_product_image > 0).astype(int)
    # intersection, union = calculate_intersection_and_union(reference_image_edges, product_image_edges)
    # jaccard_idx = jaccard_index(intersection, union)

    # dice_coeff = dice_coefficient(intersection, reference_image_edges, product_image_edges)

    score, _ = structural_similarity(filtered_reference_image, filtered_product_image, full=True, channel_axis=1)
    print("Image similarity", score)

    bhattacharyya_distance_score = bhattacharyya_distance(edge_detected_reference_image, edge_detected_product_image)

    # Centroid
    cx1, cy1 = find_centroid(edge_detected_reference_image)
    cx2, cy2 = find_centroid(edge_detected_product_image)

    # Euclidean distance
    distance = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
    print(f"Euclidean distance: {distance}")

    # Calculate thresholds based on sensitivity
    # bhattacharyya_distance_threshold = 0.0005 / sensitivity
    # ssim_threshold = 0.8 * sensitivity
    # dice_coefficient_threshold = 0.7 * sensitivity

    dist_transform = distance_transform_edt(~edge_detected_product_image)

    # Şablon pikselleri ile distance transform'ı çarp
    chamfer_matching = np.sum(dist_transform[edge_detected_reference_image > 0])
    print(chamfer_matching)

    if score > 0.90 and bhattacharyya_distance_score < 0.0005:
        print(True)
        return True, None
    else:
        diff_image = find_the_difference_between_two_images(
            product_image,
            edge_detected_reference_image,
            edge_detected_product_image,
            distance
        )
        return False, cv.cvtColor(diff_image, cv.COLOR_BGR2RGB)

    # Check if all similarity metrics are above their respective thresholds
    # is_similar = (bhattacharyya_distance_score < bhattacharyya_distance_threshold) and (score > ssim_threshold) and (
    #             dice_coeff > dice_coefficient_threshold)

    # print(is_similar)
    # return is_similar
