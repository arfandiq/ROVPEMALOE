#!/usr/bin/env python3
"""RPi USB camera -> JPEG ROS topic; independent from vehicle control."""
import math
import time

import cv2
import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CompressedImage


class USBCameraNode(Node):
    def __init__(self):
        super().__init__('usb_camera')
        for name, default in dict(device='/dev/video0', width=1920, height=1080,
                                  fps=30.0, jpeg_quality=85, reconnect_interval=2.0,
                                  image_topic='/rovpemaloe/camera/image/compressed').items():
            self.declare_parameter(name, default)
            setattr(self, name, self.get_parameter(name).value)
        if not (1 <= self.width <= 4096 and 1 <= self.height <= 2160
                and math.isfinite(self.fps) and 0 < self.fps <= 60
                and 1 <= self.jpeg_quality <= 100
                and math.isfinite(self.reconnect_interval) and self.reconnect_interval > 0):
            raise ValueError('Invalid camera dimensions, fps, JPEG quality or reconnect interval')
        self.cap = None
        self.next_open = 0.0
        self.last_frame_size = None
        self.publisher = self.create_publisher(
            CompressedImage, self.image_topic,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
        self.timer = self.create_timer(
            1.0 / self.fps, self.capture_frame, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.get_logger().info(f'USB camera {self.device} -> {self.image_topic} (JPEG)')

    def _close_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.last_frame_size = None

    def capture_frame(self):
        if self.cap is None and time.monotonic() < self.next_open:
            return
        try:
            if self.cap is None:
                device = int(self.device) if self.device.isdecimal() else self.device
                self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
                if not self.cap.isOpened():
                    raise RuntimeError(f'Cannot open {self.device}')
                # V380 exposes Full HD through MJPEG, not its raw YUYV mode.
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, frame = self.cap.read()
            stamp = self.get_clock().now().to_msg()
            if not ok or frame is None:
                raise RuntimeError('Camera disconnected or frame unavailable')
            height, width = frame.shape[:2]
            if self.last_frame_size != (width, height):
                self.last_frame_size = (width, height)
                self.get_logger().info(
                    f'Camera frame: {width}x{height}; requested '
                    f'{self.width}x{self.height} at {self.fps:g} FPS (MJPG)')
                if (width, height) != (self.width, self.height):
                    self.get_logger().warning('Camera did not deliver the requested resolution')
            ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            if not ok:
                raise RuntimeError('JPEG encoding failed')
            msg = CompressedImage()
            msg.header.stamp = stamp
            msg.header.frame_id = 'camera_optical_frame'
            msg.format = 'bgr8; jpeg compressed bgr8'
            msg.data = encoded.tobytes()
            self.publisher.publish(msg)
        except (cv2.error, RuntimeError) as exc:
            self.get_logger().warning(f'{exc}; retry in {self.reconnect_interval}s')
            self._close_camera()
            self.next_open = time.monotonic() + self.reconnect_interval

    def destroy_node(self):
        self.timer.cancel()
        self._close_camera()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = USBCameraNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
