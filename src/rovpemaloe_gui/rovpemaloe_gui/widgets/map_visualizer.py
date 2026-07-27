"""2D trajectory map visualizer widget."""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
import numpy as np


class MapVisualizer(QWidget):
    """Visualize 2D trajectory map using dead reckoning."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet('background-color: #1a1a1a;')
        self.trajectory = np.array([]).reshape(0, 2)
        self.current_position = np.array([0.0, 0.0])
        self.current_heading = 0.0

        # Map parameters
        self.scale_pixels_per_meter = 50  # pixels per meter
        self.grid_size = 0.5  # meter

    def update_trajectory(self, trajectory, position, heading):
        """Update trajectory and current state."""
        self.trajectory = trajectory
        self.current_position = position
        self.current_heading = heading
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw map visualization."""
        painter = QPainter(self)
        w, h = self.width(), self.height()
        center_x, center_y = w // 2, h // 2

        # Clear background
        painter.fillRect(0, 0, w, h, QColor(26, 26, 26))

        # Draw grid
        self.draw_grid(painter, w, h, center_x, center_y)

        # Draw trajectory
        if len(self.trajectory) > 0:
            self.draw_trajectory(painter, center_x, center_y)

        # Draw current position and heading
        self.draw_current_state(painter, center_x, center_y)

        # Draw scale indicator
        self.draw_scale(painter, w, h)

        # Draw axis labels
        self.draw_labels(painter, w, h)

    def draw_grid(self, painter, w, h, cx, cy):
        """Draw background grid."""
        pen = QPen(QColor(60, 60, 60))
        pen.setWidth(1)
        painter.setPen(pen)

        grid_pixels = int(self.grid_size * self.scale_pixels_per_meter)
        for x in range(0, w, grid_pixels):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_pixels):
            painter.drawLine(0, y, w, y)

        # Draw center axes
        pen.setColor(QColor(100, 100, 100))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(cx, 0, cx, h)  # Vertical
        painter.drawLine(0, cy, w, cy)  # Horizontal

    def draw_trajectory(self, painter, cx, cy):
        """Draw trajectory line."""
        pen = QPen(QColor(0, 200, 100))
        pen.setWidth(2)
        painter.setPen(pen)

        points = self.trajectory
        for i in range(1, len(points)):
            x1 = cx + points[i-1, 0] * self.scale_pixels_per_meter
            y1 = cy - points[i-1, 1] * self.scale_pixels_per_meter
            x2 = cx + points[i, 0] * self.scale_pixels_per_meter
            y2 = cy - points[i, 1] * self.scale_pixels_per_meter
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def draw_current_state(self, painter, cx, cy):
        """Draw current position and heading arrow."""
        x = cx + self.current_position[0] * self.scale_pixels_per_meter
        y = cy - self.current_position[1] * self.scale_pixels_per_meter

        # Draw position as circle
        brush = QBrush(QColor(255, 100, 0))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x) - 8, int(y) - 8, 16, 16)

        # Draw heading arrow
        angle_rad = np.radians(self.current_heading)
        arrow_length = 30
        end_x = x + arrow_length * np.cos(angle_rad)
        end_y = y - arrow_length * np.sin(angle_rad)

        pen = QPen(QColor(255, 100, 0))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(int(x), int(y), int(end_x), int(end_y))

        # Draw arrow head
        arrow_size = 10
        p1_x = end_x - arrow_size * np.cos(angle_rad - np.pi/6)
        p1_y = end_y + arrow_size * np.sin(angle_rad - np.pi/6)
        p2_x = end_x - arrow_size * np.cos(angle_rad + np.pi/6)
        p2_y = end_y + arrow_size * np.sin(angle_rad + np.pi/6)

        painter.drawLine(int(end_x), int(end_y), int(p1_x), int(p1_y))
        painter.drawLine(int(end_x), int(end_y), int(p2_x), int(p2_y))

    def draw_scale(self, painter, w, h):
        """Draw scale indicator."""
        scale_meters = 1.0
        scale_pixels = int(scale_meters * self.scale_pixels_per_meter)

        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(2)
        painter.setPen(pen)

        margin = 20
        x = w - margin - scale_pixels
        y = h - margin

        painter.drawLine(x, y, x + scale_pixels, y)
        painter.drawLine(x, y - 5, x, y + 5)
        painter.drawLine(x + scale_pixels, y - 5, x + scale_pixels, y + 5)

        # Label
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(x, y + 20, '1 m')

    def draw_labels(self, painter, w, h):
        """Draw axis labels."""
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))

        # X axis label (East)
        painter.drawText(w - 40, h // 2 - 10, '+X (East)')

        # Y axis label (North)
        painter.drawText(w // 2 + 10, 20, '+Y (North)')
