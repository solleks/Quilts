import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))


# A quilt is an M x N rectangle of squares
# Each square is I x I pixels
# The leaf level patterns are polygons of a particular color
# Transformations apply to J x J squares
# Patterns are built up in dependency order (not checked).

# E.g. Basic shapes are square S1 and triangle T1
# Grid point (0, 0) contains S1
# Grid point (1, 1) is a copy of (0, 0)
# Grid point (2, 0) contains T1
# Grid point (3, 0) contains (2, 0) horizontally flipped
# Grid point (2, 1) contains (2, 0) vertically flipped
# Grid point (3, 1) contains (3, 0) vertically flipped
# Grid points (4, 0) .. (5, 1) contain (0, 0) .. (1, 1) horizontally flipped
# Grid points (0, 2) .. (1, 3) contains (2, 0) .. (3, 1) rotated CW 90 deg.

class Element:
    def __init__(self, height, width, coords, hue, saturation, value):
        # height and width of bounding box
        self.height = height
        self.width = width
        self.coords = list(map(lambda c: QtCore.QPoint(c[0], c[1]), coords))
        self.color = QtGui.QColor.fromHsv(hue, saturation, value)

    def horizontal_flip(self):
        coords = list(map(lambda pt: (self.width - pt.x(), pt.y()),
                          self.coords))
        return Element(self.height, self.width, coords, self.color.hue(),
                       self.color.saturation(), self.color.value())

    def vertical_flip(self):
        coords = list(map(lambda pt: (pt.x(), self.height - pt.y()),
                          self.coords))
        return Element(self.height, self.width, coords, self.color.hue(),
                       self.color.saturation(), self.color.value())

    def both_flip(self):
        coords = list(map(lambda pt: (self.width - pt.x(),
                                      self.height - pt.y()),
                          self.coords))
        return Element(self.height, self.width, coords, self.color.hue(),
                       self.color.saturation(), self.color.value()) 

# This quilt class will create and return a QPixmap
class OhioStarlightQuilt:
    def __init__(self):
        self.sq_size = 30
        self.sq_num = 20
        self.total_size = self.sq_num * self.sq_size

        # Our pattern is a map from quilt coordinate (x, y) -> Element
        self.pattern = {}

        self.background_color = QtGui.QColor("white")
        self.guideline_color = QtGui.QColor("lightgrey")
        self.checkerboard_color = QtGui.QColor.fromHsv(255, 85, 160)
        self.hourglass_color = QtGui.QColor.fromHsv(210, 85, 255)

        # An factor to vary the color by depending on position
        self.color_adj = 3

        self.ul_triangle = [QtCore.QPoint(0, 0),
                            QtCore.QPoint(self.sq_size, 0),
                            QtCore.QPoint(0, self.sq_size),
                            QtCore.QPoint(0, 0)]
        self.ur_triangle = [QtCore.QPoint(0, 0),
                            QtCore.QPoint(self.sq_size, 0),
                            QtCore.QPoint(self.sq_size, self.sq_size),
                            QtCore.QPoint(0, 0)]
        self.ll_triangle = [QtCore.QPoint(0, 0),
                            QtCore.QPoint(self.sq_size, self.sq_size),
                            QtCore.QPoint(0, self.sq_size),
                            QtCore.QPoint(0, 0)]
        self.lr_triangle = [QtCore.QPoint(0, self.sq_size),
                            QtCore.QPoint(self.sq_size, 0),
                            QtCore.QPoint(self.sq_size, self.sq_size),
                            QtCore.QPoint(0, self.sq_size)]

        self.center_element = Element(self.sq_size, self.sq_size,
                                      [(0, 0), (0, self.sq_size),
                                       (self.sq_size, self.sq_size),
                                       (self.sq_size, 0), (0, 0)],
                                      60, 85, 50)

        # self.checker_element = Element(self.sq_size, self.sq_size,
          #                            [(0, 0), (0, self.sq_size),
          #                             (self.sq_size, self.sq_size),
           #                            (self.sq_size, 0), (0, 0)],
            #                           255, 85, 160)
        self.checker_element = Element(self.sq_size, self.sq_size,
                                      [(0, 0), (0, self.sq_size),
                                       (self.sq_size//2, self.sq_size),
                                       (self.sq_size//2, self.sq_size//2),
                                       (self.sq_size, self.sq_size//2),
                                       (self.sq_size, 0), (0, 0)],
                                       255, 85, 160)

        
    def copy_pattern(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + i, source_ul[1] + j)
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = self.pattern[source]

    def horizontal_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + (wh[0] - 1 - i), source_ul[1] + j)
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = self.pattern[source].horizontal_flip()

    def vertical_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + i, source_ul[1] + (wh[1] - 1 - j))
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = self.pattern[source].vertical_flip()

    def both_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + (wh[0] - 1 - i),
                          source_ul[1] + (wh[1] - 1 - j))
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = self.pattern[source].both_flip()   

    def draw_element(self, x_offset, y_offset, elem):
        pen = QtGui.QPen(elem.color)
        self.painter.setPen(pen)
        brush = QtGui.QBrush(elem.color)
        self.painter.setBrush(brush)

        offset_point = QtCore.QPoint(x_offset * self.sq_size,
                                     y_offset * self.sq_size)
        pts = list(map(lambda pt: pt + offset_point, elem.coords))
        self.painter.drawPolygon(pts)
                    
    def draw_pattern(self):
        for coord, elem in self.pattern.items():
            self.draw_element(coord[0], coord[1], elem)
        
    def draw(self):
        # Start transition to Element representation.
        self.pattern[(0, 0)] = self.checker_element

        self.copy_pattern((1, 1), (1, 1), (0, 0))
        self.horizontal_flip((4, 0), (2, 2), (0, 0))
        self.vertical_flip((0, 4), (2, 2), (0, 0))
        self.both_flip((4, 4), (2, 2), (0, 0))
        
        self.pattern[(2, 2)] = self.center_element
        self.pattern[(2, 3)] = self.center_element
        self.pattern[(3, 2)] = self.center_element
        self.pattern[(3, 3)] = self.center_element

        self.copy_pattern((9, 2), (2, 2), (2, 2))
        self.copy_pattern((16, 2), (2, 2), (2, 2))
        self.copy_pattern((2, 9), (2, 2), (2, 2))
        self.copy_pattern((9, 9), (2, 2), (2, 2))
        self.copy_pattern((16, 9), (2, 2), (2, 2))
        self.copy_pattern((2, 16), (2, 2), (2, 2))
        self.copy_pattern((9, 16), (2, 2), (2, 2))
        self.copy_pattern((16, 16), (2, 2), (2, 2))

        self.copy_pattern((6, 6), (1, 1), (2, 2))
        self.copy_pattern((6, 13), (1, 1), (2, 2))
        self.copy_pattern((13, 6), (1, 1), (2, 2))
        self.copy_pattern((13, 13), (1, 1), (2, 2))

        
        pattern = QtGui.QPixmap(self.total_size, self.total_size)
        pattern.fill(self.background_color)

        self.painter = QtGui.QPainter(pattern)

        pen = QtGui.QPen(self.guideline_color)
        self.painter.setPen(pen)
        for x in range(0, self.total_size, self.sq_size):
            self.painter.drawLine(x, 0, x, self.total_size)
            self.painter.drawLine(0, x, self.total_size, x)

        self.draw_pattern()

        # self.draw_checker_corners(0, 0)
        self.draw_checker_corners(0, 7)
        self.draw_checker_corners(0, 14)
        self.draw_checker_corners(7, 0)
        self.draw_checker_corners(7, 7)
        self.draw_checker_corners(7, 14)
        self.draw_checker_corners(14, 0)
        self.draw_checker_corners(14, 7)
        self.draw_checker_corners(14, 14)

        self.draw_hourglasses(0, 0)
        self.draw_hourglasses(0, 7)
        self.draw_hourglasses(0, 14)
        self.draw_hourglasses(7, 0)
        self.draw_hourglasses(7, 7)
        self.draw_hourglasses(7, 14)
        self.draw_hourglasses(14, 0)
        self.draw_hourglasses(14, 7)
        self.draw_hourglasses(14, 14)
        
        self.painter.end()

        return pattern

    def draw_checker_corners(self, x_offset, y_offset):
        self.draw_checker_pair(x_offset, y_offset, parity="Even")
        self.draw_checker_pair(x_offset + 4, y_offset, parity="Odd")
        self.draw_checker_pair(x_offset, y_offset + 4, parity="Odd")
        self.draw_checker_pair(x_offset + 4, y_offset + 4, parity="Even")
        
    
    def draw_checker_pair(self, x_offset, y_offset, parity):
        if parity == "Even":
            self.draw_checker_dark(x_offset, y_offset)
            self.draw_checker_dark(x_offset + 1, y_offset + 1)
        else:
            self.draw_checker_dark(x_offset + 1, y_offset)
            self.draw_checker_dark(x_offset, y_offset + 1)

    def draw_checker_dark(self, x_offset, y_offset):
        hue = self.checkerboard_color.hue()
        saturation = self.checkerboard_color.saturation()
        value = self.checkerboard_color.value()
        hue = (hue + self.color_adj * (x_offset + y_offset - self.sq_num)) % 360
        adjust_color = QtGui.QColor.fromHsv(hue, saturation, value)

        pen = QtGui.QPen(adjust_color)
        self.painter.setPen(pen)
        brush = QtGui.QBrush(adjust_color)
        self.painter.setBrush(brush)
        self.painter.drawRect(x_offset * self.sq_size,
                              y_offset * self.sq_size,
                              self.sq_size, self.sq_size)

    def draw_hourglasses(self, x_offset, y_offset):
        self.draw_hourglass(x_offset + 2, y_offset, parity="Odd")
        self.draw_hourglass(x_offset, y_offset + 2, parity="Even")
        self.draw_hourglass(x_offset + 4, y_offset + 2, parity="Even")
        self.draw_hourglass(x_offset + 2, y_offset + 4, parity="Odd")
        
    def draw_hourglass(self, x_offset, y_offset, parity):
        if parity == "Even":
            self.draw_hourglass_poly(x_offset, y_offset, corner="UR")
            self.draw_hourglass_poly(x_offset + 1, y_offset, corner="UL")
            self.draw_hourglass_poly(x_offset, y_offset + 1, corner="LR")
            self.draw_hourglass_poly(x_offset + 1, y_offset + 1, corner="LL")
        else:
            self.draw_hourglass_poly(x_offset, y_offset, corner="LL")
            self.draw_hourglass_poly(x_offset + 1, y_offset, corner="LR")
            self.draw_hourglass_poly(x_offset, y_offset + 1, corner="UL")
            self.draw_hourglass_poly(x_offset + 1, y_offset + 1, corner="UR")

    def draw_hourglass_poly(self, x_offset, y_offset, corner):
        hue = self.hourglass_color.hue()
        saturation = self.hourglass_color.saturation()
        value = self.hourglass_color.value()
        hue = (hue + self.color_adj * (x_offset + y_offset - self.sq_num)) % 360
        adjust_color = QtGui.QColor.fromHsv(hue, saturation, value)

        pen = QtGui.QPen(adjust_color)
        self.painter.setPen(pen)
        brush = QtGui.QBrush(adjust_color)
        self.painter.setBrush(brush)

        offset_point = QtCore.QPoint(x_offset * self.sq_size,
                                     y_offset * self.sq_size)
        if corner == "UL":
            pts = list(map(lambda pt: pt + offset_point, self.ul_triangle))
            self.painter.drawPolygon(pts)
        elif corner == "UR":
            pts = list(map(lambda pt: pt + offset_point, self.ur_triangle))
            self.painter.drawPolygon(pts)
        elif corner == "LL":
            pts = list(map(lambda pt: pt + offset_point, self.ll_triangle))
            self.painter.drawPolygon(pts)
        else:
            pts = list(map(lambda pt: pt + offset_point, self.lr_triangle))
            self.painter.drawPolygon(pts)


# A simple drawing window with a QPainter and a QPixmap

class QuiltWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quilt Pattern")
        self.setGeometry(100, 100, 800, 800)

        self.quilt = OhioStarlightQuilt()
        self.canvas = self.quilt.draw()

        self.label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setPixmap(self.canvas)
        self.setCentralWidget(self.label)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = QuiltWindow()
    window.show()

    sys.exit(app.exec())

    
        
                      
