from src.config import paths


def cast_to_correct_type(value):
    if '.' in value:
        return float(value)
    return int(value)


def write_last_reference_image_name(reference_image_name: str):
    file_path = paths.SRC_ASSETS_DIR.joinpath("last_reference_image_used.txt")
    with file_path.open('w', encoding="utf-8") as file:
        file.write(reference_image_name)


def read_last_reference_image_name():
    file_path = paths.SRC_ASSETS_DIR.joinpath("last_reference_image_used.txt")
    with file_path.open("r", encoding="utf-8") as file:
        reference_image_name = file.read()
    return reference_image_name


def write_last_reference_image_coordinates(reference_image_name: str, coordinates: tuple[int]):
    file_path = paths.SRC_COORDINATES_DIR.joinpath("".join([reference_image_name, ".txt"]))
    with file_path.open("w", encoding="utf-8") as file:
        file.write(", ".join(map(str, coordinates)))


def read_last_reference_image_coordinates(reference_image_name: str):
    file_path = paths.SRC_COORDINATES_DIR.joinpath("".join([reference_image_name, ".txt"]))
    with file_path.open("r", encoding="utf-8") as file:
        content = file.read()
    coordinates = tuple(map(int, content.split(", ")))
    return coordinates


def write_last_reference_image_parameters(reference_image_name: str, values_of_parameters: tuple[int]):
    file_path = paths.SRC_PARAMETERS_OF_REFERENCE_IMAGES.joinpath("".join([reference_image_name, ".txt"]))
    with file_path.open("w", encoding="utf-8") as file:
        file.write(", ".join(map(str, values_of_parameters)))


def read_last_reference_image_parameters(reference_image_name: str):
    file_path = paths.SRC_PARAMETERS_OF_REFERENCE_IMAGES.joinpath("".join([reference_image_name, ".txt"]))
    with file_path.open("r", encoding="utf-8") as file:
        content = file.read()
    values_of_parameters = tuple(map(cast_to_correct_type, content.split(", ")))
    return values_of_parameters


def write_reference_images_names_from_entry(reference_image_name: str):
    if reference_image_name in read_saved_reference_images_names():
        return
    else:
        file_path = paths.SRC_ASSETS_DIR.joinpath("reference_images_names.txt")
        mode = 'a' if file_path.exists() else 'w'
        with file_path.open(mode, encoding="utf-8") as file:
            file.write(f"{reference_image_name}\n")


def read_saved_reference_images_names():
    file_path = paths.SRC_ASSETS_DIR.joinpath("reference_images_names.txt")
    with file_path.open("r", encoding="utf-8") as file:
        reference_images_names = file.read().splitlines()
    return reference_images_names


def split_tuple_values(t):
    # Tuple'ı unpacking ile ilk üç ve son iki eleman olarak ayırma
    *first_three, fourth, fifth = t

    # İlk üç değeri birleştirip string olarak saklama
    first_three_str = ', '.join(map(str, first_three))

    # Son iki değeri birleştirip string olarak saklama
    last_two_str = ', '.join(map(str, [fourth, fifth]))

    return first_three_str, last_two_str
