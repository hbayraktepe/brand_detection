import time

from PIL import Image
from pypylon import pylon


class VideoStreamHandler:
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.camera = None
        self._initialize_video_capture()
        self.start_row = int((height - 600) / 2)
        self.start_col = int((width - 800) / 2)
        self.end_row = self.start_row + 600
        self.end_col = self.start_col + 800
        self.converter = pylon.ImageFormatConverter()

        # converting to opencv bgr format
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def _initialize_video_capture(self):
        # connecting to the first available camera
        self.camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )

        # Grabing Continuously (video) with minimal delay
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        time.sleep(0.5)
        print(f"Camera Initialized")

    def get_frame(self):
        if not self.camera or not self.camera.IsGrabbing():
            raise ValueError(
                "Cannot get frame because video capture is not initialized or opened"
            )

        grabResult = self.camera.RetrieveResult(
            5000, pylon.TimeoutHandling_ThrowException
        )
        if grabResult.GrabSucceeded():
            # Access the image data
            image = self.converter.Convert(grabResult)
            frame = image.GetArray()
            grabResult.Release()
            return (
                True,
                frame[self.start_row : self.end_row, self.start_col : self.end_col],
            )
        return False, None

    def snapshot(self, filename: str):
        if not (self.camera and self.camera.IsGrabbing()):
            raise ValueError(
                "Cannot take snapshot because video capture is not initialized or opened"
            )

        grabResult = self.camera.RetrieveResult(
            5000, pylon.TimeoutHandling_ThrowException
        )
        if grabResult.GrabSucceeded():
            image = self.converter.Convert(grabResult)
            frame = image.GetArray()
            cropped_frame = frame[
                self.start_row : self.end_row, self.start_col : self.end_col
            ]
            img = Image.fromarray(cropped_frame)
            img.save(filename, quality=95)
            grabResult.Release()
        else:
            raise ValueError("Failed to read frame for snapshot")

    def release(self):
        if self.camera and self.camera.IsGrabbing():
            self.camera.StopGrabbing()
        else:
            print("No active video capture to release")
