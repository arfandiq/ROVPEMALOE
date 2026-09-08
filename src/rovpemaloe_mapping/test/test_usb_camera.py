"""JPEG encoding and reconnect tests without opening a physical camera."""
from unittest.mock import Mock, patch
import cv2
import numpy as np
import rclpy
from rovpemaloe_mapping.nodes.usb_camera import USBCameraNode


def test_jpeg_publish_disconnect_and_reconnect():
    rclpy.init()
    node = USBCameraNode()
    capture = Mock()
    capture.isOpened.return_value = True
    capture.read.return_value = (True, np.full((48, 64, 3), 128, dtype=np.uint8))
    node.publisher = Mock()
    try:
        with patch('rovpemaloe_mapping.nodes.usb_camera.cv2.VideoCapture', return_value=capture) as open_camera:
            node.capture_frame()
            msg = node.publisher.publish.call_args.args[0]
            decoded = cv2.imdecode(np.frombuffer(bytes(msg.data), dtype=np.uint8), cv2.IMREAD_COLOR)
            assert decoded.shape == (48, 64, 3)
            assert 'jpeg' in msg.format
            assert msg.header.stamp.sec > 0
            capture.read.return_value = (False, None)
            node.capture_frame()
            assert node.cap is None
            capture.release.assert_called_once()
            node.capture_frame()
            assert open_camera.call_count == 1  # Respect retry interval, do not busy-loop.
            node.next_open = 0.0
            capture.read.return_value = (True, decoded)
            node.capture_frame()
            assert open_camera.call_count == 2
            assert node.publisher.publish.call_count == 2
    finally:
        node.destroy_node()
        rclpy.shutdown()
