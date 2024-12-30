from pathlib import Path

from PIL import Image, ImageTk

from src.config import paths


def load_image(reference_image_path: Path):
    if reference_image_path.exists():
        image = Image.open(reference_image_path)
        image_tk = ImageTk.PhotoImage(image)
        return image, image_tk
    else:
        return None, None


def save_cropped_reference_image(reference_image: Image, selected_area: tuple[int]):
    cropped_image_path = paths.SRC_ASSETS_DIR.joinpath("cropped_referans_image.png")
    cropped_image = reference_image.crop(selected_area)
    cropped_image.save(cropped_image_path, quality=95)
    print(f"Selection saved to {cropped_image_path}")


def crop_areas_to_compare_from_images(
    reference_image: Image,
    reference_image_coordinates: tuple[int],
    product_image: Image,
    product_image_coordinates: tuple[int],
):
    cropped_reference_image = reference_image.crop(reference_image_coordinates)
    cropped_product_image = product_image.crop(product_image_coordinates)
    return cropped_reference_image, cropped_product_image


# def load_

# def save_cropped_reference_image_box(selected_reference_image: Image, selected_area_box: tuple[int]):
