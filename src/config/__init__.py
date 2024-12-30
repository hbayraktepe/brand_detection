"""
Configuration module for the project.

This module provides easy access to the project configuration settings,
such as paths, logger configurations.

Exports:
    - paths (ProjectPaths): An instance of the ProjectPaths dataclass with pre-defined paths for various directories in
      the project.
    - logger (logging.Logger): A pre-configured logger instance for logging messages throughout the project.

Author: Yusuf Akyazıcı
"""

from src.config.config import ProjectPaths, configure_logging

paths = ProjectPaths()
logger = configure_logging()
