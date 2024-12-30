import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk

from src.utilities.file_helper import write_last_reference_image_parameters


class ImageAdjustWindow:
    """A window for adjusting image filter parameters."""

    def __init__(
        self,
        reference_image_name=None,
        master=None,
        canvas_image=None,
        d_var=None,
        sigma_color_var=None,
        sigma_space_var=None,
        threshold1_var=None,
        threshold2_var=None,
    ):
        self.window = tk.Toplevel(master)
        self.window.resizable(False, False)
        self.window.title("Parametre Ayarları")
        self.style_image_scale = ttk.Style()
        self.style_image_button = ttk.Style()
        self.image_name = reference_image_name
        self.canvas_frame = None
        self.canvas = None
        self.bilateral_frame = None
        self.canny_frame = None
        self.canvas_image = canvas_image  ######top widget
        self.canvas_image_width = canvas_image.size[0]
        self.canvas_image_height = canvas_image.size[1]
        self.resize_rate = 1.0
        self.original_image = cv.cvtColor(
            np.array(canvas_image.copy()), cv.COLOR_RGB2GRAY
        )  # Store a copy of the original image
        self.filtered_image = cv.cvtColor(
            np.array(canvas_image.copy()), cv.COLOR_RGB2GRAY
        )
        self.edge_detected_image = None

        # Assign filter parameters
        self.d_var = d_var
        self.sigma_color_var = sigma_color_var
        self.sigma_space_var = sigma_space_var
        self.threshold1_var = threshold1_var
        self.threshold2_var = threshold2_var

        self.create_canvas()
        self.create_sliders()
        self.create_apply_button()
        self.create_apply_edge_button()
        self.create_apply_contour_button()
        self.apply_filters()

        # Pencereye odaklanma özelliği eklenir
        self.window.grab_set()

        # Set up a handler for the window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_canvas(self):
        """Create a canvas and load an image onto it."""

        self.canvas_frame = tk.LabelFrame(self.window, bd=5)
        self.canvas_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

        orig_width, orig_height = self.canvas_image.size
        max_size = 800
        if orig_width > max_size or orig_height > max_size:
            if orig_width > orig_height:
                self.resize_rate = max_size / orig_width
            else:
                self.resize_rate = max_size / orig_height
        else:
            self.resize_rate = 1
        self.canvas_image_width = int(orig_width * self.resize_rate)
        self.canvas_image_height = int(orig_height * self.resize_rate)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=self.canvas_image_width,
            height=self.canvas_image_height,
        )
        self.canvas.pack()

        # Add image to canvas
        self.update_canvas()

    def update_canvas(self):
        img = self.canvas_image.resize(
            (
                int(self.canvas_image_width * self.resize_rate),
                int(self.canvas_image_height * self.resize_rate),
            )
        )
        img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)

        # Keep a reference to the image to prevent it from being garbage collected
        self.canvas.image = img

    def create_sliders(self):
        """Create sliders for adjusting filter parameters."""

        self.style_image_scale.configure("Accent.TButton", font="Helvetica, 14")

        # Bilateral Filter Parameters
        self.bilateral_frame = tk.LabelFrame(
            self.window,
            text="Bilateral Filtre Parametreleri",
            font=("Helvetica", 14, "bold"),
        )
        # self.bilateral_frame.pack(padx=20, pady=10)
        self.bilateral_frame.grid(row=1, column=0, padx=20, pady=10)
        bilateral_parameters = [
            (self.d_var, 1, 100, "d"),
            (self.sigma_color_var, 0, 255, "Sigma Color", 0.1),
            (self.sigma_space_var, 0, 255, "Sigma Space", 0.1),
        ]

        for param in bilateral_parameters:
            var, from_, to, label = param[0:4]
            resolution = param[4] if len(param) > 4 else 1
            tk.Scale(
                self.bilateral_frame,
                from_=from_,
                to=to,
                variable=var,
                label=label,
                orient=tk.HORIZONTAL,
                length=350,
                resolution=resolution,
                font="Helvetica, 14",
            ).pack(padx=20, pady=2)

        # Canny Edge Detector Parameters
        self.canny_frame = tk.LabelFrame(
            self.window,
            text="Canny Kenar Algılayıcı Parametreleri",
            font=("Helvetica", 14, "bold"),
        )
        # self.canny_frame.pack(padx=20, pady=10)
        self.canny_frame.grid(row=1, column=1, padx=20, pady=10)
        canny_parameters = [
            (self.threshold1_var, 0, 255, "Threshold 1"),
            (self.threshold2_var, 0, 255, "Threshold 2"),
        ]

        for param in canny_parameters:
            var, from_, to, label = param[0:4]
            resolution = param[4] if len(param) > 4 else 1
            tk.Scale(
                self.canny_frame,
                from_=from_,
                to=to,
                variable=var,
                label=label,
                orient=tk.HORIZONTAL,
                length=350,
                resolution=resolution,
                font="Helvetica, 14",
            ).pack(padx=20, pady=2)

    def create_apply_button(self):
        """Create a button for applying filters."""

        # The apply button is now created inside the bilateral_frame
        apply_button = ttk.Button(
            self.bilateral_frame,
            text="Ayarları Kaydet",
            style="Accent.TButton",
            command=self.apply_filters,
        )
        apply_button.pack(pady=15)

    def create_apply_edge_button(self):
        """Create a button for applying Canny edge detection."""

        apply_edge_button = ttk.Button(
            self.canny_frame,
            text="Ayarları Kaydet",
            style="Accent.TButton",
            command=self.apply_edge_detection,
        )
        apply_edge_button.pack(pady=15)

    def create_apply_contour_button(self):
        """Create a button for applying contour."""

        apply_contour_button = ttk.Button(
            self.canny_frame,
            text="Contour Önizleme",
            style="Accent.TButton",
            command=self.apply_contour,
        )
        apply_contour_button.pack(pady=15)

    def apply_filters(self):
        """Apply filters to the image."""

        # Always start with the original image
        self.canvas_image = self.original_image.copy()

        # Apply bilateral filter
        self.filtered_image = cv.bilateralFilter(
            self.canvas_image,
            self.d_var.get(),
            self.sigma_color_var.get(),
            self.sigma_space_var.get(),
        )

        # Convert back to PIL format
        self.canvas_image = Image.fromarray(self.filtered_image)

        # Update the canvas
        self.update_canvas()

    def apply_edge_detection(self):
        """Apply Canny edge detection to the image."""

        # Always start with the original image
        self.canvas_image = self.filtered_image.copy()

        # Apply Canny edge detection
        self.edge_detected_image = cv.Canny(
            self.canvas_image, self.threshold1_var.get(), self.threshold2_var.get()
        )

        # Convert back to PIL format
        self.canvas_image = Image.fromarray(self.edge_detected_image)

        # Update the canvas
        self.update_canvas()

    def apply_contour(self):
        image_colored = cv.cvtColor(self.filtered_image, cv.COLOR_GRAY2BGR)
        contours, _ = cv.findContours(
            self.edge_detected_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
        )
        cv.drawContours(image_colored, contours, -1, (0, 255, 0), 2)
        self.canvas_image = Image.fromarray(image_colored)
        self.update_canvas()

    def on_close(self):
        """This function will be called when the window is closed."""

        values_of_parameters = (
            self.d_var.get(),
            self.sigma_color_var.get(),
            self.sigma_space_var.get(),
            self.threshold1_var.get(),
            self.threshold2_var.get(),
        )
        write_last_reference_image_parameters(self.image_name, values_of_parameters)
        self.window.destroy()
