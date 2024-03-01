import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
from tkinter import Toplevel, Label, Scale, HORIZONTAL
from PIL import ImageTk, Image
import requests
from PIL import Image, ImageTk
from src.config import paths, logger
from src.utilities.file_helper import (
    write_last_reference_image_name,
    read_last_reference_image_name,
    write_last_reference_image_coordinates,
    read_last_reference_image_coordinates,
    write_last_reference_image_parameters,
    read_last_reference_image_parameters,
    write_reference_images_names_from_entry,
    read_saved_reference_images_names,
    split_tuple_values
)
from src.utilities.video_stream_handler import VideoStreamHandler
from src.utilities.image_adjust import ImageAdjustWindow
from src.utilities.image_comparison import calculate_similarity
from src.database.database import add_record, upload_to_minio

# import RPi.GPIO as GPIO
# import threading
# import time


# def listen_for_button_press(app):
#     while True:
#         input_state = GPIO.input(18)  Bağlanılacak olan kablonun pini
#         if input_state == False:
#             app.product_compare_image_button_click()
#             print('Button Pressed')
#             time.sleep(0.2)


class BrandDetectionApp:
    def __init__(self, root: tk.Tk, window_title: str, video_source: int,
                 video_width: int, video_height: int):
        self.root = root
        self.style_ttk = ttk.Style()
        self.root.title(window_title)
        self.image_adjust_window = None
        self.video_source = video_source
        self.video_width = video_width
        self.video_height = video_height
        self.vid = VideoStreamHandler(self.video_width, self.video_height)

        # Screen resolution
        self.screen_width = self.root.winfo_width()
        self.screen_height = self.root.winfo_height()

        self.rects = []

        # Reference image settings
        self.reference_image_path = None
        self.selected_reference_image_path = paths.SRC_ASSETS_DIR.joinpath("selected_reference_image.png")
        self.selected_reference_image = None
        self.selected_reference_image_tk = None
        self.cropped_reference_image = None
        self.selected_reference_image_name = None
        self.selected_reference_image_coordinates = []
        self.saved_reference_images_names = None
        self.new_reference_image_name = None

        # Product image settings
        self.product_image_path = paths.SRC_PRODUCT_IMAGES_DIR.joinpath("product_image.png")
        self.product_image = None
        self.product_image_tk = None

        # Selected and cropped

        # Canvas state
        self.current_canvas = None
        self.update_image_tk = None
        self.canvas_width = 800
        self.canvas_height = 600

        # Selection box
        self.rect = None
        self.product_rect = None
        self.start_x = None
        self.start_y = None

        # Variables for filter parameters
        self.d_var = tk.IntVar()
        self.sigma_color_var = tk.DoubleVar()
        self.sigma_space_var = tk.DoubleVar()
        self.threshold1_var = tk.IntVar()
        self.threshold2_var = tk.IntVar()

        # Label frames for canvases
        # Create a label frame for the reference canvas
        self.reference_canvas_frame = tk.LabelFrame(
            self.root,
            text="Referans Ürün Görseli",
            font=("Helvetica", 20, "bold"),
            borderwidth=4
        )
        self.reference_canvas_frame.grid(row=0, column=0, padx=50, pady=30)

        # Create a label frame for the product canvas
        self.product_canvas_frame = tk.LabelFrame(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            text="Karşılaştırılacak Ürün Görseli",
            font=("Helvetica", 20, "bold"),
            borderwidth=4
        )
        self.product_canvas_frame.grid(row=0, column=1, padx=110, ipady=37)

        # Canvases for images
        # Create canvas for the reference image
        self.reference_canvas = tk.Canvas(
            self.reference_canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height
        )
        self.reference_canvas.pack(padx=5, pady=5)

        # Create canvas for the product image
        self.product_canvas = tk.Canvas(
            self.product_canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height
        )
        self.product_canvas.pack(padx=5, pady=5)

        # Combobox for selected reference image
        self.saved_reference_images_combobox = ttk.Label(
            self.reference_canvas_frame,
            text="Kayıtlı referans görsel seçimi:",
            font="Helvetica, 14"
        )
        self.saved_reference_images_combobox.pack()

        self.saved_reference_images_combobox = ttk.Combobox(
            self.reference_canvas_frame,
            font="Helvetica, 14",
            state="readonly",
        )
        self.saved_reference_images_combobox.pack(pady=5)
        self.saved_reference_images_combobox.bind("<<ComboboxSelected>>", self.on_select_combobox)

        # Label Frames for buttons
        # Create a label frame for the area selection buttons on the reference image
        self.reference_image_area_select_buttons_frame = tk.LabelFrame(
            self.root,
            text="Referans Alan Seçimi",
            font=("Helvetica", 16, "bold"),
            borderwidth=4
        )
        self.reference_image_area_select_buttons_frame.grid(row=1, column=0, sticky="W", padx=50, pady=20)

        # Create a label frame for the reference image selection buttons
        self.reference_select_image_button_frame = tk.LabelFrame(
            self.root,
            text="Referans Ürün Görsel Kaydı",
            font=("Helvetica", 16, "bold"),
            borderwidth=4
        )
        self.reference_select_image_button_frame.grid(row=2, column=0, sticky="W", padx=50, pady=20)

        # Create a label frame for the product image selection buttons to compare
        self.product_image_button_frame = tk.LabelFrame(
            self.root,
            text="Ürün Kontrolü",
            font=("Helvetica", 16, "bold"),
            borderwidth=4
        )
        self.product_image_button_frame.grid(row=1, column=1, sticky="W", padx=110, pady=5)

        self.result_label_frame = tk.LabelFrame(
            self.root,
            font=("Helvetica", 16, "bold"),
            borderwidth=0,
            highlightthickness=0
        )
        self.result_label_frame.grid(row=2, column=1, sticky="W", padx=110, pady=5)

        # Buttons for functionality
        # Buttons to select area from reference image
        self.style_ttk.configure('Accent.TButton', font="Helvetica, 14")
        self.style_ttk.configure('Disabled.TButton', font="Helvetica, 14")
        self.reference_image_area_select_button = ttk.Button(
            self.reference_image_area_select_buttons_frame,
            text="Alan seç",
            command=self.reference_image_area_select_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.reference_image_area_select_button.grid(row=0, column=0, padx=10, pady=10)

        self.reference_image_area_clear_button = ttk.Button(
            self.reference_image_area_select_buttons_frame,
            text="Seçili alanı temizle",
            command=self.reference_image_area_clear_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.reference_image_area_clear_button.grid(row=0, column=1, padx=10, pady=10)

        self.reference_image_area_apply_button = ttk.Button(
            self.reference_image_area_select_buttons_frame,
            text="Seçili alanları onayla",
            command=self.reference_image_area_apply_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.reference_image_area_apply_button.grid(row=0, column=3, padx=10, pady=10)

        self.reference_select_image_button = ttk.Button(
            self.reference_select_image_button_frame,
            text="Kamerayı aç",
            command=self.reference_select_image_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.reference_select_image_button.grid(row=0, column=0, padx=10, pady=10)

        self.save_reference_select_image_label = ttk.Label(
            self.reference_select_image_button_frame,
            text="Görsel etiketi:",
            font="Helvetica, 14"
        )
        self.save_reference_select_image_label.grid(row=0, column=1, padx=1, pady=10)

        self.save_reference_select_image_entry = tk.Entry(
            self.reference_select_image_button_frame,
            font="Helvetica, 14"
        )
        self.save_reference_select_image_entry.grid(row=0, column=2, padx=1, pady=10)

        self.save_reference_select_image_button = ttk.Button(
            self.reference_select_image_button_frame,
            text="Görseli kaydet",
            command=self.save_reference_select_image_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.save_reference_select_image_button.grid(row=0, column=3, padx=10, pady=10)

        # Buttons to compare product image
        self.product_open_camera_button = ttk.Button(
            self.product_image_button_frame,
            text="Kamerayı aç",
            command=self.product_open_camera_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.product_open_camera_button.grid(row=0, column=0, sticky="W", padx=10, pady=10)

        self.product_close_camera_button = ttk.Button(
            self.product_image_button_frame,
            text="Kamerayı kapat",
            command=self.product_close_camera_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.product_close_camera_button.grid(row=0, column=1, sticky="W", padx=10, pady=10)

        self.product_compare_image_button = ttk.Button(
            self.product_image_button_frame,
            text="Görseli kontrol et",
            command=self.product_compare_image_button_click,
            state="normal",
            style='Accent.TButton'
        )
        self.product_compare_image_button.grid(row=0, column=2, sticky="W", padx=10, pady=10)

        # Label
        self.result_static_label = tk.Label(
            self.result_label_frame,
            text='Ürün Kontrol Sonucu:',
            font="Helvetica, 22"
        )
        self.result_static_label.grid(row=0, column=0, sticky="W", padx=0, pady=10)
        # result_static_label.pack(side=tk.LEFT)

        self.result_dynamic_label = tk.Label(
            self.result_label_frame,
            text='',
            font="Helvetica, 24",
            fg="#00FF00"
        )
        self.result_dynamic_label.grid(row=0, column=1, sticky="NSWE", padx=5, pady=10)
        # self.result_dynamic_label.pack(side=tk.LEFT)

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Görsel Ayarları", menu=filemenu)
        filemenu.add_command(label="Parametre ayarları", command=self.create_new_window, font=("Helvetica", 14))

        # Bind events
        self.reference_canvas.bind("<Button-1>", self.start_rect)
        self.reference_canvas.bind("<ButtonRelease-1>", self.update_rect)

        self.initialize()

    def create_new_window(self):
        params = read_last_reference_image_parameters(self.selected_reference_image_name)

        self.d_var.set(params[0])
        self.sigma_color_var.set(params[1])
        self.sigma_space_var.set(params[2])
        self.threshold1_var.set(params[3])
        self.threshold2_var.set(params[4])

        full_reference_image = Image.open(self.selected_reference_image_path)

        self.image_adjust_window = ImageAdjustWindow(
            master=self.root,
            reference_image_name=self.selected_reference_image_name,
            canvas_image=full_reference_image,
            d_var=self.d_var,
            sigma_color_var=self.sigma_color_var,
            sigma_space_var=self.sigma_space_var,
            threshold1_var=self.threshold1_var,
            threshold2_var=self.threshold2_var
        )

    def initialize(self):
        if self.selected_reference_image_path.exists():
            self.filling_combobox_options()
            self.selected_reference_image_name = read_last_reference_image_name()
            self.saved_reference_images_combobox.set(self.selected_reference_image_name)
            self.manage_reference_image_and_canvas(self.selected_reference_image_path)
            self.reference_canvas.config(state="disabled")
            self.initial_components_status()
        else:
            paths.SRC_ASSETS_DIR.joinpath("reference_images_names.txt").touch(exist_ok=True)
            paths.SRC_ASSETS_DIR.joinpath("last_reference_image_used.txt").touch(exist_ok=True)
            self.initial_components_status_with_selected_image_check()

    def on_select_combobox(self, event):
        self.selected_reference_image_name = self.saved_reference_images_combobox.get()
        self.reference_image_path = paths.SRC_REFERENCE_IMAGES_DIR.joinpath(
            "".join([self.selected_reference_image_name, ".png"])
        )
        write_last_reference_image_name(self.selected_reference_image_name)
        self.manage_reference_image_and_canvas(self.reference_image_path)
        shutil.copy(self.reference_image_path, self.selected_reference_image_path)
        self.selected_reference_image.save(self.selected_reference_image_path, quality=95)
        self.reference_canvas.config(state="disabled")
        self.initial_components_status()

    def manage_reference_image_and_canvas(self, image_path):
        self.reference_image_area_clear_button_click()
        self.selected_reference_image = Image.open(image_path)
        self.selected_reference_image_tk = ImageTk.PhotoImage(self.selected_reference_image)
        self.reference_canvas.create_image(0, 0, image=self.selected_reference_image_tk, anchor="nw")

        # Koordinatları oku ve kullan
        self.selected_reference_image_coordinates = read_last_reference_image_coordinates(
            self.selected_reference_image_name)
        if self.selected_reference_image_coordinates:
            for coords in self.selected_reference_image_coordinates:
                x1, y1, x2, y2 = coords  # Her bir koordinat setini unpack et
                self.reference_canvas.create_rectangle(x1, y1, x2, y2, outline="#00FF00", width=2)

    def filling_combobox_options(self):
        self.saved_reference_images_names = read_saved_reference_images_names()
        self.saved_reference_images_combobox['values'] = self.saved_reference_images_names

    def start_rect(self, event):
        if self.reference_canvas["state"] != "disabled":
            self.start_x = self.reference_canvas.canvasx(event.x)
            self.start_y = self.reference_canvas.canvasy(event.y)

            rect = self.reference_canvas.create_rectangle(self.start_x, self.start_y, self.start_x,
                                                          self.start_y, outline="red", width=2)
            self.rects.append(rect)

    def update_rect(self, event):
        if not self.rects:
            return

        cur_x = self.reference_canvas.canvasx(event.x)
        cur_y = self.reference_canvas.canvasy(event.y)

        self.reference_canvas.coords(self.rects[-1], self.start_x, self.start_y, cur_x, cur_y)

    def reference_image_area_select_button_click(self):
        confirmation = messagebox.askyesno(
            "Referans Alanı Değiştirme",
            "Referans alan değiştirilecek. Devam etmek istiyor musunuz?",
            icon=messagebox.QUESTION
        )
        if confirmation:
            self.reference_image_area_select_buttons_state()
        else:
            return

    def reference_image_area_apply_button_click(self):
        all_selected_coordinates = []  # Seçilen tüm alanların koordinatlarını tutacak liste
        for rect in self.rects:
            coordinates = self.reference_canvas.coords(rect)  # Mevcut dikdörtgenin koordinatlarını al
            if coordinates:
                x1, y1, x2, y2 = coordinates  # Koordinatları unpack et
                box = (int(x1), int(y1), int(x2), int(y2))  # Koordinatları bir tuple olarak sakla
                all_selected_coordinates.append(box)  # Koordinat setini listeye ekle
                self.reference_canvas.itemconfig(rect, outline="#00FF00",
                                                 width=2)  # Dikdörtgeni onaylanmış olarak işaretle
        self.selected_reference_image_coordinates = all_selected_coordinates
        write_last_reference_image_coordinates(
            self.selected_reference_image_name, all_selected_coordinates
        )
        self.reference_image_area_apply_buttons_state()


    def reference_image_area_clear_button_click(self):
        for rect in self.rects:
            self.reference_canvas.delete(rect)
        self.rects.clear()


    def reference_select_image_button_click(self):
        confirmation = messagebox.askyesno("Referans Görüntü Değiştirme",
                                           "Referans görüntü değiştirilecek. "
                                           "Devam etmek istiyor musunuz?",
                                           icon=messagebox.QUESTION)
        if confirmation:
            self.reference_image_selection_buttons_states()
            self.current_canvas = self.reference_canvas
            self.delete_reference_canvas_image()
            self.update_image()

    def product_open_camera_button_click(self):
        self.product_open_camera_buttons_states()
        self.current_canvas = self.product_canvas
        self.delete_product_canvas_image()
        self.update_image()

    def product_close_camera_button_click(self):
        self.stop_product_canvas_streaming()
        self.product_close_camera_buttons_states()

    def save_reference_select_image_button_click(self):
        self.new_reference_image_name = self.save_reference_select_image_entry.get()
        if not self.new_reference_image_name:
            self.stop_reference_canvas_streaming()
            self.reference_product_image_selection_enable_states()
            if self.selected_reference_image_path.exists():
                self.manage_reference_image_and_canvas(self.selected_reference_image_path)
            else:
                self.initial_components_status_with_selected_image_check()
            return messagebox.showwarning("Uyarı", "Lütfen referans görsel etiketi alanını boş bırakmayın!")
        else:
            self.save_reference_select_image_entry.delete(0, tk.END)
            self.selected_reference_image_name = self.new_reference_image_name
            self.reference_image_path = paths.SRC_REFERENCE_IMAGES_DIR.joinpath(
                "".join([self.selected_reference_image_name, ".png"])
            )
            self.vid.snapshot(self.reference_image_path)
            self.stop_reference_canvas_streaming()
            default_box = (0, 0, 1, 1)
            default_values_of_image_parameters = (1, 0.0, 0.0, 0, 0)
            shutil.copy(self.reference_image_path, self.selected_reference_image_path)
            write_last_reference_image_coordinates(self.selected_reference_image_name, default_box)
            write_last_reference_image_parameters(self.selected_reference_image_name,
                                                  default_values_of_image_parameters)
            write_reference_images_names_from_entry(self.selected_reference_image_name)
            write_last_reference_image_name(self.selected_reference_image_name)
            self.manage_reference_image_and_canvas(self.reference_image_path)
            self.filling_combobox_options()
            self.saved_reference_images_combobox.set(self.selected_reference_image_name)
            self.reference_product_image_selection_enable_states()
            messagebox.showinfo("Başarılı", f"Referans görsel '{self.new_reference_image_name}' olarak kaydedildi!")
            messagebox.showwarning("Uyarı", f"Lütfen '{self.new_reference_image_name}' referans görseli için "
                                            f"bir referans alanı belirleyiniz!")

    def manage_product_image_and_canvas(self):
        # Ürün görselini kaydet ve yükle
        self.vid.snapshot(self.product_image_path)
        self.product_image = Image.open(self.product_image_path)
        self.product_image_tk = ImageTk.PhotoImage(self.product_image)

        # Görseli canvas'a ekle ve referansı sakla
        self.current_image_on_canvas = self.product_canvas.create_image(0, 0, image=self.product_image_tk, anchor="nw")

        for coords in self.selected_reference_image_coordinates:
            x1, y1, x2, y2 = coords
            self.product_canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=3)

    def manage_diff_image_and_canvas(self, diff_image, coords):
        x1, y1, x2, y2 = coords

        diff_image_pil = Image.fromarray(diff_image)
        Image.Image.paste(self.product_image, diff_image_pil, (x1, y1))

        self.product_image_tk = ImageTk.PhotoImage(self.product_image)
        # Saklanan referansı kullanarak canvas üzerindeki görseli güncelle
        self.product_canvas.itemconfig(self.current_image_on_canvas, image=self.product_image_tk)

        self.product_canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=3)

    def product_compare_image_button_click(self):
        if self.current_canvas is None:
            self.manage_product_image_and_canvas()
            cropped_reference_images, cropped_product_images = self.crop_areas_to_compare_from_images()

            comparison_results = {}  # Karşılaştırma sonuçlarını tutacak dict

            for index, (cropped_reference_image, cropped_product_image) in enumerate(
                    zip(cropped_reference_images, cropped_product_images), start=1):
                score, diff_image = calculate_similarity(
                    self.selected_reference_image_name,
                    1.0,
                    cropped_reference_image,
                    cropped_product_image
                )

                # Her bir karşılaştırma sonucunu dict'e ekle
                comparison_results[f"Alan {index}"] = f"Skor: {score:.2f}"

                if not score:  # Eğer skor yoksa, yani eşleşme başarısızsa
                    coords = self.selected_reference_image_coordinates[index - 1]  # İlgili koordinat setini al
                    self.manage_diff_image_and_canvas(diff_image, coords)
                brand_name = self.saved_reference_images_combobox.get()

                result_text, result_color, result_flag = ("BAŞARILI", "#00FF00", True) if score else (
                "BAŞARISIZ", "#ff1e00", False)
                self.result_dynamic_label.config(text=result_text, fg=result_color)


                # try:
                #     bilateral_params, canny_params = split_tuple_values(
                #         read_last_reference_image_parameters(self.selected_reference_image_name))
                #     coords = ', '.join(map(str, self.selected_reference_image_coordinates))
                #     response = add_record(68, datetime.now(), brand_name, bilateral_params, canny_params, coords,
                #                           result_flag)
                #     logger.info(msg=f"Response: {response.text}")
                # except requests.exceptions.RequestException as err:
                #     logger.error(msg=f"An error occurred: {str(err)}", exc_info=True)
                #     messagebox.showerror("Hata", "Veri kaydedilemedi! Sunucu bağlantı hatası! ")
                #
                # if response.status_code == 200:
                #     record_id = response.json().get('added_record_id')
                #     upload_to_minio(record_id, brand_name, self.selected_reference_image_path, result_flag)
            self.show_comparison_results(comparison_results)
        else:
            self.product_close_camera_button_click()
            self.product_compare_image_button_click()

    def show_comparison_results(self, comparison_results):
        result_message = "Karşılaştırma Sonuçları:\n\n"
        for area, score in comparison_results.items():
            result_message += f"{area}: {score}\n"

        messagebox.showinfo("Karşılaştırma Sonuçları", result_message)

    def crop_areas_to_compare_from_images(self):
        cropped_reference_images = []
        cropped_product_images = []

        for rect in self.rects:
            coordinates = self.reference_canvas.coords(rect)
            if coordinates:
                x1, y1, x2, y2 = coordinates
                cropped_reference_image = self._crop_image(self.selected_reference_image, (x1, y1, x2, y2))
                cropped_reference_images.append(cropped_reference_image)
                cropped_product_image = self._crop_image(self.product_image, (x1, y1, x2, y2))
                cropped_product_images.append(cropped_product_image)
        print(cropped_product_images)

        return cropped_reference_images, cropped_product_images

    def _crop_image(self, image, coords):
        return image.crop(coords) if coords else None

    def update_image(self):
        if self.current_canvas:
            ret, frame = self.vid.get_frame()
            if ret:
                self.update_image_tk = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.current_canvas.create_image(0, 0, anchor="nw", image=self.update_image_tk)
                self.current_canvas.update()
                self.root.after(5, self.update_image)

    def stop_reference_canvas_streaming(self):
        self.current_canvas = None
        self.delete_reference_canvas_image()

    def start_product_canvas_streaming(self):
        self.current_canvas = self.product_canvas
        self.delete_product_canvas_image()
        self.update_image()

    def stop_product_canvas_streaming(self):
        self.current_canvas = None
        self.delete_product_canvas_image()

    def delete_reference_canvas_image(self):
        if self.reference_canvas.find_all():
            self.reference_canvas.delete("all")

    def delete_product_canvas_image(self):
        if self.product_canvas.find_all():
            self.product_canvas.delete("all")

    def reference_product_image_selection_enable_states(self):
        self.saved_reference_images_combobox.config(state="readonly")
        self.reference_image_area_select_button.config(state="normal", style='Accent.TButton')
        self.reference_select_image_button.config(state="normal", style='Accent.TButton')
        self.save_reference_select_image_entry.config(state="disable")
        self.save_reference_select_image_button.config(state="disable", style='Disabled.TButton')
        self.product_open_camera_button.config(state="normal", style='Accent.TButton')
        self.product_open_camera_button.config(state="normal", style='Accent.TButton')
        self.product_close_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_compare_image_button.config(state="normal", style='Accent.TButton')

    def reference_image_selection_buttons_states(self):
        self.camera_open_button_common_states()
        self.save_reference_select_image_entry.config(state="normal")
        self.save_reference_select_image_button.config(state="normal", style='Accent.TButton')
        self.product_open_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_close_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_compare_image_button.config(state="disable", style='Disabled.TButton')

    def reference_image_area_select_buttons_state(self):
        self.reference_canvas.config(state="normal")
        self.saved_reference_images_combobox.config(state="disabled")
        self.reference_image_area_select_button.config(state="disabled", style='Disabled.TButton')
        self.reference_image_area_clear_button.config(state="normal", style='Accent.TButton')
        self.reference_image_area_apply_button.config(state="normal", style='Accent.TButton')
        self.reference_select_image_button.config(state="disabled", style='Disabled.TButton')
        self.save_reference_select_image_button.config(state="disabled", style='Disabled.TButton')
        self.product_open_camera_button.config(state="disabled", style='Disabled.TButton')
        self.product_close_camera_button.config(state="disabled", style='Disabled.TButton')
        self.product_compare_image_button.config(state="disabled", style='Disabled.TButton')

    def reference_image_area_apply_buttons_state(self):
        self.reference_canvas.config(state="disabled")
        self.saved_reference_images_combobox.config(state="readonly")
        self.reference_image_area_select_button.config(state="normal", style='Accent.TButton')
        self.reference_image_area_clear_button.config(state="disabled", style='Disabled.TButton')
        self.reference_image_area_apply_button.config(state="disabled", style='Disabled.TButton')
        self.reference_select_image_button.config(state="normal", style='Accent.TButton')
        self.product_open_camera_button.config(state="normal", style='Accent.TButton')
        self.product_close_camera_button.config(state="disabled", style='Disabled.TButton')
        self.product_compare_image_button.config(state="normal", style='Accent.TButton')

    def product_open_camera_buttons_states(self):
        self.camera_open_button_common_states()
        self.product_open_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_close_camera_button.config(state="normal", style='Accent.TButton')
        self.save_reference_select_image_entry.config(state="disabled")
        self.save_reference_select_image_button.config(state="disable", style='Disabled.TButton')

    def product_close_camera_buttons_states(self):
        self.reference_product_image_selection_enable_states()
        self.product_close_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_open_camera_button.config(state="normal", style='Accent.TButton')

    def camera_open_button_common_states(self):
        self.saved_reference_images_combobox.config(state="disable")
        self.reference_image_area_select_button.config(state="disable", style='Disabled.TButton')
        self.reference_select_image_button.config(state="disable", style='Disabled.TButton')

    def initial_components_status(self):
        self.reference_image_area_clear_button.config(state="disabled", style='Disabled.TButton')
        self.reference_image_area_apply_button.config(state="disabled", style='Disabled.TButton')
        self.save_reference_select_image_entry.config(state="disabled")
        self.save_reference_select_image_button.config(state="disabled", style='Disabled.TButton')
        self.product_close_camera_button.config(state="disabled", style='Disabled.TButton')

    def initial_components_status_with_selected_image_check(self):
        self.initial_components_status()
        self.reference_canvas.config(state="disabled")
        self.saved_reference_images_combobox.config(state="disable")
        self.reference_image_area_select_button.config(state="disabled", style='Disabled.TButton')
        self.product_open_camera_button.config(state="disable", style='Disabled.TButton')
        self.product_compare_image_button.config(state="disabled", style='Disabled.TButton')


if __name__ == '__main__':
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    root_object = tk.Tk()
    # root_object.attributes('-fullscreen', True)
    root_object.option_add("*Font", ("Verdana", 25))
    root_object.tk.call("source", paths.SRC_AZURE_TTK_THEME_DIR)
    root_object.tk.call("set_theme", "dark")
    app = BrandDetectionApp(
        root=root_object,
        window_title="Marka Tespit",
        video_source=0,
        video_width=1920,
        video_height=1080
    )

    # t = threading.Thread(target=listen_for_button_press, args=(app,))
    # t.start()

    root_object.mainloop()
