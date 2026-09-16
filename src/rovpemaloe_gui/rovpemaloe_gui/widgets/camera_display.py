"""Display remote ROS JPEG frames or an explicitly selected local USB camera."""
import time

import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class CameraDisplay(QWidget):
    def __init__(self, source='ros', local_device=0):
        super().__init__()
        if source not in ('ros', 'local', 'off'):
            raise ValueError('camera_source must be ros, local or off')
        self.source = source
        self.last_frame_time = None
        self.cap = None
        self.frame_pixmap = None
        self.layout = QVBoxLayout(self)
        self.camera_label = QLabel('Menunggu kamera RPi...' if source == 'ros' else 'Kamera nonaktif')
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet('background: #F4F5F7; color: #64748B; border-radius: 6px;')
        self.camera_label.setMinimumHeight(180)
        self.camera_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.addWidget(self.camera_label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        if source == 'local':
            self.cap = cv2.VideoCapture(local_device)
            if not self.cap.isOpened():
                self.camera_label.setText('Kamera lokal tidak tersedia')
        if source != 'off':
            self.timer.start(100 if source == 'ros' else 33)

    def show_compressed(self, msg):
        """Called in the Qt thread by GUI ROS polling; invalid JPEG leaves last valid time intact."""
        if self.source != 'ros' or not msg.data:
            return
        try:
            frame = cv2.imdecode(np.frombuffer(bytes(msg.data), dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                self.show_frame(frame)
        except cv2.error:
            return

    def show_frame(self, frame):
        # Retain source detail; resize only the displayed copy to fit the panel.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        q_image = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
        self.frame_pixmap = QPixmap.fromImage(q_image)
        self.resize_frame()
        self.last_frame_time = time.monotonic()

    def resize_frame(self):
        if self.frame_pixmap is not None:
            self.camera_label.setPixmap(self.frame_pixmap.scaled(
                self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_frame()

    def update_frame(self):
        if self.source == 'local' and self.cap is not None and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                self.show_frame(frame)
        if self.last_frame_time is not None and time.monotonic() - self.last_frame_time > 2.0:
            self.frame_pixmap = None
            self.camera_label.clear()
            self.camera_label.setText('Video terputus / frame stale')

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
        super().closeEvent(event)
