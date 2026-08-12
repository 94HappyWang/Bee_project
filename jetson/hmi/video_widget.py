import math
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect


class VideoCanvasWidget(QWidget):
    """Aspect-ratio preserving responsive PyQt Video Canvas with interactive Line A & Line B mouse dragging."""

    # Signal emitted when user drags Line A or Line B endpoints in calibration mode
    lines_changed = pyqtSignal(list, list)  # (line_a, line_b)

    def __init__(self, is_calibration_mode=False, parent=None):
        super().__init__(parent)
        self.is_calibration_mode = is_calibration_mode

        self.current_frame = None
        self.qimage = None

        # Line coordinates in original image space [x1, y1, x2, y2]
        self.line_a = [100, 150, 540, 150]
        self.line_b = [100, 330, 540, 330]

        # Handle dragging state
        self.selected_handle = None  # ('A', 1), ('A', 2), ('B', 1), ('B', 2)
        self.handle_radius = 12

        self.setMinimumSize(400, 300)
        if self.is_calibration_mode:
            self.setMouseTracking(True)

    def set_frame(self, frame: np.ndarray):
        """Receives OpenCV BGR frame and converts to QImage for rendering."""
        if frame is None:
            return
        self.current_frame = frame
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.qimage = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.update()  # Trigger repaint

    def set_lines(self, line_a: list, line_b: list):
        """Sets Line A and Line B coordinates."""
        self.line_a = list(line_a)
        self.line_b = list(line_b)
        self.update()

    def _get_target_draw_rect(self):
        """Calculates centered draw QRect preserving image aspect ratio."""
        if self.qimage is None or self.qimage.isNull():
            return self.rect(), 1.0, 1.0, 0, 0

        fw = self.qimage.width()
        fh = self.qimage.height()
        ww = self.width()
        wh = self.height()

        img_aspect = fw / float(fh) if fh > 0 else 1.0
        widget_aspect = ww / float(wh) if wh > 0 else 1.0

        if widget_aspect > img_aspect:
            target_h = wh
            target_w = int(wh * img_aspect)
            offset_x = (ww - target_w) // 2
            offset_y = 0
        else:
            target_w = ww
            target_h = int(ww / img_aspect)
            offset_x = 0
            offset_y = (wh - target_h) // 2

        target_rect = QRect(offset_x, offset_y, target_w, target_h)
        return target_rect, fw, fh, offset_x, offset_y

    def _frame_to_widget_coords(self, pt):
        """Converts point from frame coordinates to widget canvas coordinates."""
        target_rect, fw, fh, offset_x, offset_y = self._get_target_draw_rect()
        if self.qimage is None or self.qimage.isNull() or fw <= 0 or fh <= 0:
            return QPoint(pt[0], pt[1])

        scale_x = target_rect.width() / float(fw)
        scale_y = target_rect.height() / float(fh)

        return QPoint(int(offset_x + pt[0] * scale_x), int(offset_y + pt[1] * scale_y))

    def _widget_to_frame_coords(self, qpoint):
        """Converts point from widget canvas coordinates to frame coordinates."""
        target_rect, fw, fh, offset_x, offset_y = self._get_target_draw_rect()
        if self.qimage is None or self.qimage.isNull() or target_rect.width() <= 0 or target_rect.height() <= 0:
            return (qpoint.x(), qpoint.y())

        scale_x = fw / float(target_rect.width())
        scale_y = fh / float(target_rect.height())

        cx = int((qpoint.x() - offset_x) * scale_x)
        cy = int((qpoint.y() - offset_y) * scale_y)
        cx = max(0, min(fw, cx))
        cy = max(0, min(fh, cy))
        return (cx, cy)

    def paintEvent(self, event):
        """Custom QPainter rendering event."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        target_rect, fw, fh, offset_x, offset_y = self._get_target_draw_rect()

        # 1. Fill canvas background
        painter.fillRect(self.rect(), QColor("#EAE6DD"))

        # 2. Draw Video Frame (Aspect Ratio Preserved)
        if self.qimage is not None and not self.qimage.isNull():
            painter.drawImage(target_rect, self.qimage)
        else:
            painter.setPen(QColor("#756F67"))
            painter.setFont(QFont("Microsoft JhengHei UI", 14, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "🎥 影像串流連線中...")

        # 3. In Calibration Mode, draw interactive line handles overlay
        if self.is_calibration_mode:
            pA1 = self._frame_to_widget_coords((self.line_a[0], self.line_a[1]))
            pA2 = self._frame_to_widget_coords((self.line_a[2], self.line_a[3]))
            pB1 = self._frame_to_widget_coords((self.line_b[0], self.line_b[1]))
            pB2 = self._frame_to_widget_coords((self.line_b[2], self.line_b[3]))

            # Draw Line A (Soft Slate Blue)
            pen_a = QPen(QColor("#3A86FF"), 3, Qt.DashLine)
            painter.setPen(pen_a)
            painter.drawLine(pA1, pA2)

            # Draw Line B (Muted Sage Green)
            pen_b = QPen(QColor("#2A9D8F"), 3, Qt.DashLine)
            painter.setPen(pen_b)
            painter.drawLine(pB1, pB2)

            # Draw Endpoint Handle Circles
            self._draw_handle(painter, pA1, "Line A (P1)", QColor("#3A86FF"))
            self._draw_handle(painter, pA2, "Line A (P2)", QColor("#3A86FF"))
            self._draw_handle(painter, pB1, "Line B (P1)", QColor("#2A9D8F"))
            self._draw_handle(painter, pB2, "Line B (P2)", QColor("#2A9D8F"))

    def _draw_handle(self, painter, point, label, color):
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(point, self.handle_radius, self.handle_radius)

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Microsoft JhengHei UI", 11, QFont.Bold))
        painter.drawText(point.x() + 15, point.y() + 5, label)

    # --- Mouse Drag Calibration Event Handlers ---
    def mousePressEvent(self, event):
        if not self.is_calibration_mode or event.button() != Qt.LeftButton:
            return

        pos = event.pos()
        pA1 = self._frame_to_widget_coords((self.line_a[0], self.line_a[1]))
        pA2 = self._frame_to_widget_coords((self.line_a[2], self.line_a[3]))
        pB1 = self._frame_to_widget_coords((self.line_b[0], self.line_b[1]))
        pB2 = self._frame_to_widget_coords((self.line_b[2], self.line_b[3]))

        # Check proximity to handles
        if self._dist(pos, pA1) <= self.handle_radius * 1.5:
            self.selected_handle = ('A', 1)
        elif self._dist(pos, pA2) <= self.handle_radius * 1.5:
            self.selected_handle = ('A', 2)
        elif self._dist(pos, pB1) <= self.handle_radius * 1.5:
            self.selected_handle = ('B', 1)
        elif self._dist(pos, pB2) <= self.handle_radius * 1.5:
            self.selected_handle = ('B', 2)

    def mouseMoveEvent(self, event):
        if not self.is_calibration_mode or self.selected_handle is None:
            return

        cx, cy = self._widget_to_frame_coords(event.pos())
        line_type, pt_num = self.selected_handle

        if line_type == 'A':
            if pt_num == 1:
                self.line_a[0], self.line_a[1] = cx, cy
            else:
                self.line_a[2], self.line_a[3] = cx, cy
        elif line_type == 'B':
            if pt_num == 1:
                self.line_b[0], self.line_b[1] = cx, cy
            else:
                self.line_b[2], self.line_b[3] = cx, cy

        self.update()
        self.lines_changed.emit(self.line_a, self.line_b)

    def mouseReleaseEvent(self, event):
        if self.is_calibration_mode and event.button() == Qt.LeftButton:
            self.selected_handle = None

    def _dist(self, p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())
