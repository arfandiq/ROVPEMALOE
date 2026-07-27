"""Camera display widget for live USB camera feed."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np


class CameraDisplay(QWidget):
    """Display live USB camera feed or placeholder."""

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Camera label
        self.camera_label = QLabel('USB Camera Feed')
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet(
            'background-color: #1a1a1a; color: white; font-size: 18px;'
        )
        self.camera_label.setMinimumHeight(480)
        self.layout.addWidget(self.camera_label)

        # Try to initialize camera
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.timer.start(33)  # ~30 FPS
        except Exception as e:
            self.camera_label.setText(f'Camera Error: {str(e)}\n(Running in demo mode)')

    def update_frame(self):
        """Read and display camera frame."""
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            # Resize to fit widget
            h, w = frame.shape[:2]
            ratio = min(640 / w, 480 / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            frame = cv2.resize(frame, (new_w, new_h))

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Display
            pixmap = QPixmap.fromImage(q_img)
            self.camera_label.setPixmap(pixmap)

    def closeEvent(self, event):
        """Release camera on close."""
        if self.cap is not None:
            self.cap.release()
        self.timer.stop()
        super().closeEvent(event)
