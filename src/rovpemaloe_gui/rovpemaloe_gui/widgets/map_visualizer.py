"""White metric XY trajectory plot matching the operator reference layout."""
import math
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont


class MapVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.trajectory = np.empty((0, 2))
        self.current_position = np.array([0., 0.])
        self.current_heading = 0.0

    def update_trajectory(self, trajectory, position, heading):
        points = np.asarray(trajectory, dtype=float).reshape(-1, 2)
        self.trajectory = points[np.isfinite(points).all(axis=1)]
        self.current_position = np.asarray(position, dtype=float)
        self.current_heading = heading
        self.update()

    def plot_bounds(self):
        # Reference default viewport; expand when real trajectory leaves it.
        if not len(self.trajectory):
            return 0., 2.5, 0., 6.
        return (min(0., math.floor(self.trajectory[:, 0].min() * 2) / 2),
                max(2.5, math.ceil(self.trajectory[:, 0].max() * 2) / 2),
                min(0., math.floor(self.trajectory[:, 1].min())),
                max(6., math.ceil(self.trajectory[:, 1].max())))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)
        painter.setFont(self.font())
        plot = QRectF(66, 22, max(1, self.width()-92), max(1, self.height()-88))
        xmin, xmax, ymin, ymax = self.plot_bounds()

        def point(x, y):
            return QPointF(plot.left() + (x-xmin)/(xmax-xmin)*plot.width(),
                           plot.bottom() - (y-ymin)/(ymax-ymin)*plot.height())

        for x in np.linspace(xmin, xmax, 6):
            pos = point(x, ymin)
            painter.setPen(QPen(QColor('#E2E8F0'), 1))
            painter.drawLine(QPointF(pos.x(), plot.top()), pos)
            painter.setPen(QColor('#333333'))
            painter.drawText(QRectF(pos.x()-30, plot.bottom()+8, 60, 22), Qt.AlignCenter, f'{x:g}')
        for y in np.linspace(ymin, ymax, 7):
            pos = point(xmin, y)
            painter.setPen(QPen(QColor('#E2E8F0'), 1))
            painter.drawLine(pos, QPointF(plot.right(), pos.y()))
            painter.setPen(QColor('#333333'))
            painter.drawText(QRectF(15, pos.y()-11, 42, 22), Qt.AlignRight | Qt.AlignVCenter, f'{y:g}')
        painter.setPen(QPen(QColor('#94A3B8'), 1))
        painter.drawRect(plot)
        painter.drawText(QRectF(plot.left(), plot.bottom()+35, plot.width(), 25), Qt.AlignCenter, 'X Position (m)')
        painter.save()
        painter.translate(16, plot.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-100, -12, 200, 25), Qt.AlignCenter, 'Y Position (m)')
        painter.restore()
        painter.save()
        painter.setClipRect(plot.adjusted(1, 1, -1, -1))
        painter.setPen(QPen(QColor('#14856b'), 2.5))
        for a, b in zip(self.trajectory[:-1], self.trajectory[1:]):
            painter.drawLine(point(*a), point(*b))
        if len(self.trajectory):
            pos = point(*self.trajectory[-1])
            painter.setBrush(QColor('#ed9744'))
            painter.setPen(QPen(QColor('#333333'), 1))
            painter.drawEllipse(pos, 5, 5)
        else:
            painter.setPen(QColor('#888888'))
            painter.drawText(plot, Qt.AlignCenter, 'Menunggu trajectory')
        painter.restore()
