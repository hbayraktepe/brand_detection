from datetime import datetime

import requests
from minio import Minio


def add_record(
    device_id: int,
    date: datetime,
    brand_name: str,
    bilateral_params: str,
    canny_params: str,
    coordinates: str,
    state: bool,
) -> requests.Response:
    """
    Adds a record to the brand_detection API.

    :param device_id: ID of the device.
    :param date: Date of the record (as a datetime object).
    :param brand_name: Brand name of the device.
    :param bilateral_params: String representation of three parameters for the bilateral filter applied to the image.
                             This should include the diameter of the pixel neighborhood, the standard deviation in
                             color space, and the standard deviation in coordinate space, separated by commas.
    :param canny_params: String representation of two parameters for the Canny edge detection applied to the image.
                         This should include the lower threshold and the upper threshold, separated by a comma.
    :param coordinates: String representation of the coordinates of the cropped image. This should include the top-left
                        x and y coordinates, as well as the width and height of the crop, separated by commas.
    :param state: State of the device (True or False).
    :return: Response from the API (requests.Response object).
    """
    # API endpoint
    url = "http://192.168.4.118:85/brand_detection/add_record/"

    # Preparing the payload
    data = {
        "device_id": device_id,
        "date": date.isoformat(),
        "brand_name": brand_name,
        "bilateral_params": bilateral_params,
        "canny_params": canny_params,
        "coordinates": coordinates,
        "state": state,
    }

    # Making the POST request
    response = requests.post(url, json=data)
    return response


def upload_to_minio(record_id: int, brand_name: str, file_path: str, state: bool):
    """
    Uploads a file to a specified bucket in MinIO.
    """

    # Initialize MinIO client
    minio_client = Minio(
        minio_url,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )

    # Determine the file path in MinIO based on the state
    result_flag = "1" if state else "0"
    object_name = f"{brand_name}/{result_flag}/{record_id}_{brand_name}.jpg"

    # Check if the bucket exists, if not, create it
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # Upload the file
    minio_client.fput_object(bucket_name, object_name, file_path)


# MinIO configuration
minio_url = "192.168.4.118:9000"
minio_access_key = "mVhhXRCRQdILyZSaw9tG"
minio_secret_key = "XeV6KYRSj6iDrBsRi3S0k9xpw1gxAY1mYIXYBXKW"
bucket_name = "deneme"
