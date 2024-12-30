from typing import Tuple

import cv2 as cv
import imagehash
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from src.utilities.file_helper import read_last_reference_image_parameters


def euclidean_distance(image1: np.ndarray, image2: np.ndarray) -> float:
    flatten1 = image1.flatten()
    flatten2 = image2.flatten()
    distance = np.linalg.norm(flatten1 - flatten2)
    max_distance = np.linalg.norm(
        np.full(flatten1.shape, 255)
    )  # Tüm piksellerin maksimum değerde olduğu durum
    distance_percentage = (distance / max_distance) * 100
    print(
        "Euclidean Distance as a percentage of max possible distance: {:.2f}%".format(
            distance_percentage
        )
    )
    return distance_percentage


def histogram_intersection(hist1: np.ndarray, hist2: np.ndarray) -> float:
    """
    Calculate the histogram intersection between two histograms.
    """
    minima = np.minimum(hist1, hist2)
    intersection = np.true_divide(np.sum(minima), np.sum(hist2))
    return intersection


def calculate_histogram_intersection_for_grayscale(
    images1: np.ndarray, images2: np.ndarray
) -> float:
    """
    Calculate Histogram Intersection for two grayscale images.
    """
    # Grayscale görüntülerin histogramlarını hesapla
    hist1 = cv.calcHist([images1], [0], None, [256], [0, 256])
    hist2 = cv.calcHist([images2], [0], None, [256], [0, 256])

    # Histogramları normalize et
    cv.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    cv.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    # Histogramların kesişimini hesapla
    intersection_score = histogram_intersection(hist1, hist2)
    print("Histogram Intersection for Grayscale Images: ", intersection_score)
    return intersection_score


def sift_similarity(org_img: np.ndarray, pred_img: np.ndarray) -> Tuple[float, int]:
    # SIFT özelliği çıkarıcıyı başlat
    sift = cv.SIFT_create()

    # Her iki görüntü için anahtar noktaları ve tanımlayıcıları hesapla
    kp1, des1 = sift.detectAndCompute(org_img, None)
    kp2, des2 = sift.detectAndCompute(pred_img, None)

    # BFMatcher nesnesi oluştur ve anahtar noktaları eşleştir
    bf = cv.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Lowe'un oran testini uygula
    good_matches = []
    for m, n in matches:
        if m.distance < 0.9 * n.distance:
            good_matches.append(m)

    # İyi eşleşmelerin sayısını ve toplam eşleşme sayısına oranını döndür
    if len(matches) > 0:
        ratio = len(good_matches) / len(matches)
    else:
        ratio = 0

    return ratio, len(good_matches)


def bhattacharyya_distance(edges1: np.ndarray, edges2: np.ndarray) -> float:
    """
    Calculate Bhattacharyya Distance for two images.
    """
    hist1 = cv.calcHist([edges1], [0], None, [256], [0, 256])
    hist2 = cv.calcHist([edges2], [0], None, [256], [0, 256])
    cv.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    cv.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    bhattacharyya_distance_score = cv.compareHist(
        hist1, hist2, cv.HISTCMP_BHATTACHARYYA
    )
    print("Bhattacharyya Distance: ", bhattacharyya_distance_score)
    return bhattacharyya_distance_score


def phash_percentage_difference(image1: np.ndarray, image2: np.ndarray) -> float:
    # Numpy dizilerini PIL Image nesnelerine dönüştür
    img1 = Image.fromarray(image1)
    img2 = Image.fromarray(image2)

    # Her iki resmin perceptual hash değerlerini hesapla
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)

    # İki hash arasındaki farkı hesapla
    hash_difference = hash1 - hash2

    # Maksimum farkı ve yüzdelik farkı hesapla (64 bitlik hash için maksimum fark 64)
    maksimum_fark = 64
    yuzde_fark = (hash_difference / maksimum_fark) * 100
    print("{:.2f}%".format(yuzde_fark))
    return yuzde_fark


def filter_images(
    reference_image_name: str, reference_image, product_image
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Filter images using parameters from last reference image.
    """
    reference_image_gray = cv.cvtColor(np.array(reference_image), cv.COLOR_RGB2GRAY)
    product_image_gray = cv.cvtColor(np.array(product_image), cv.COLOR_RGB2GRAY)
    params = read_last_reference_image_parameters(reference_image_name)
    filtered_reference_image = cv.bilateralFilter(
        reference_image_gray, params[0], params[1], params[2]
    )
    filtered_product_image = cv.bilateralFilter(
        product_image_gray, params[0], params[1], params[2]
    )
    edge_detected_reference_image = cv.Canny(
        filtered_reference_image, params[3], params[4]
    )
    edge_detected_product_image = cv.Canny(filtered_product_image, params[3], params[4])
    return (
        filtered_reference_image,
        filtered_product_image,
        edge_detected_reference_image,
        edge_detected_product_image,
    )


def find_the_difference_between_two_images(
    reference_image=None,
    reference_image_edges=None,
    product_image_edges=None,
    euclidean_distance=None,
):
    reference_image_bgr = cv.cvtColor(np.array(reference_image), cv.COLOR_RGB2BGR)

    # İki edge görüntüsü arasındaki farkı hesaplayın
    diff = cv.absdiff(reference_image_edges, product_image_edges)

    h, w = diff.shape

    for y in range(h):
        for x in range(w):
            if diff[y, x] != 0:  # Fark varsa
                reference_image_bgr[y, x] = [0, 0, 255]

    return reference_image_bgr


def calculate_similarity(
    reference_image_name: str,
    sensitivity: float = 1.0,
    reference_image=None,
    product_image=None,
) -> float:
    """
    Calculate similarity between reference image and product image.
    """
    (
        filtered_reference_image,
        filtered_product_image,
        edge_detected_reference_image,
        edge_detected_product_image,
    ) = filter_images(reference_image_name, reference_image, product_image)

    score, _ = structural_similarity(
        filtered_reference_image, filtered_product_image, full=True, channel_axis=1
    )
    print("Image similarity", score)

    # bhattacharyya_distance_score = bhattacharyya_distance(edge_detected_reference_image, edge_detected_product_image)
    #
    # euclidean_distance_value = euclidean_distance(edge_detected_reference_image, edge_detected_product_image)
    #
    # # sift_ratio, sift_matches = sift_similarity(filtered_reference_image, filtered_product_image)
    # # print(f"SIFT Matches: {sift_matches}, SIFT Ratio: {sift_ratio}")
    #
    # phash=phash_percentage_difference(filtered_reference_image, filtered_product_image)

    histI = calculate_histogram_intersection_for_grayscale(
        filtered_reference_image, filtered_product_image
    )

    if histI > 0.80 and score > 0.75:
        print(True)
        return True, None
    else:
        diff_image = find_the_difference_between_two_images(
            product_image, edge_detected_reference_image, edge_detected_product_image
        )
        return False, cv.cvtColor(diff_image, cv.COLOR_BGR2RGB)
