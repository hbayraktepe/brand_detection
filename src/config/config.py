"""
Config module for the brand detection project.

This module provides the necessary configurations, such as database
connections, logger, and project paths, to be used throughout the project.
Project paths are defined using the ProjectPaths dataclass, which makes it
easy to access various directories within the project. Logger is set up to
log both to console and to a file, and can be imported and used by other
modules. Database configurations are loaded from environment variables.

Author: Yusuf Akyazıcı
"""

import logging.handlers
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Path = Path(__file__).parents[2]


@dataclass
class ProjectPaths:
    DATA_DIR: Path = BASE_DIR / "data"
    SRC_DIR: Path = BASE_DIR / "src"
    SRC_ASSETS_DIR: Path = SRC_DIR / "assets"
    SRC_PRODUCT_IMAGES_DIR: Path = SRC_ASSETS_DIR / "product_images"
    SRC_REFERENCE_IMAGES_DIR: Path = SRC_ASSETS_DIR / "reference_images"
    SRC_COORDINATES_DIR: Path = SRC_ASSETS_DIR / "coordinates"
    SRC_AZURE_TTK_THEME_DIR: Path = SRC_ASSETS_DIR / "Azure-ttk-theme" / "azure.tcl"
    SRC_PARAMETERS_OF_REFERENCE_IMAGES: Path = (
        SRC_ASSETS_DIR / "parameters_of_reference_images"
    )
    SRC_CONFIG_DIR: Path = SRC_DIR / "config"
    SRC_DATABASE_DIR: Path = SRC_DIR / "database"
    SRC_UTILITIES_DIR: Path = SRC_DIR / "utilities"
    SRC_LOGS_DIR: Path = SRC_DIR / "logs"
    SRC_SERVICES_DIR: Path = SRC_DIR / "services"


def create_rotating_file_handler(
    log_file: Path,
    max_log_size: int = 10 * 1024 * 1024,
    backup_count: int = 50,
    log_level: int = logging.DEBUG,
    formatter: logging.Formatter = None,
) -> logging.Handler:
    """Create a rotating file handler."""
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_log_size, backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    if formatter:
        file_handler.setFormatter(formatter)
    return file_handler


def create_console_handler(
    log_level: int = logging.DEBUG, formatter: logging.Formatter = None
) -> logging.Handler:
    """Create a console handler."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    if formatter:
        console_handler.setFormatter(formatter)
    return console_handler


def configure_logging(
    logger_name: str = "brand_detection",
    log_dir: Path = ProjectPaths.SRC_LOGS_DIR,
    log_file_name: str = "brand_detection.log",
    file_log_level: int = logging.DEBUG,
    console_log_level: int = logging.DEBUG,
    max_log_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    formatter: logging.Formatter = None,
) -> logging.Logger:
    """Configure logging with given parameters."""
    if not formatter:
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(filename)s | %(funcName)s | %(levelname)s: %(message)s"
        )

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_file_name

    file_handler = create_rotating_file_handler(
        log_file, max_log_size, backup_count, file_log_level, formatter
    )
    console_handler = create_console_handler(console_log_level, formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
