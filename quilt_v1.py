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



# This quilt class will create and return a QPixmap
class OhioStarlightQuilt:
    def __init__(self):
        self.sq_size = 30
        self.sq_num = 20
        self.total_size = self.sq_num * self.sq_size

        self.background_color = QtGui.QColor("white")
        self.guideline_color = QtGui.QColor("lightgrey")
        self.checkerboard_color = QtGui.QColor.fromHsv(255, 85, 160)
        self.center_color = QtGui.QColor.fromHsv(60, 85, 50)
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
        
        
    def draw(self):
        pattern = QtGui.QPixmap(self.total_size, self.total_size)
        pattern.fill(self.background_color)

        self.painter = QtGui.QPainter(pattern)

        pen = QtGui.QPen(self.guideline_color)
        self.painter.setPen(pen)
        for x in range(0, self.total_size, self.sq_size):
            self.painter.drawLine(x, 0, x, self.total_size)
            self.painter.drawLine(0, x, self.total_size, x)

        self.draw_checker_corners(0, 0)
        self.draw_checker_corners(0, 7)
        self.draw_checker_corners(0, 14)
        self.draw_checker_corners(7, 0)
        self.draw_checker_corners(7, 7)
        self.draw_checker_corners(7, 14)
        self.draw_checker_corners(14, 0)
        self.draw_checker_corners(14, 7)
        self.draw_checker_corners(14, 14)

        self.draw_center(2, 2)
        self.draw_center(9, 2)
        self.draw_center(16, 2)
        self.draw_center(2, 9)
        self.draw_center(9, 9)
        self.draw_center(16, 9)
        self.draw_center(2, 16)
        self.draw_center(9, 16)
        self.draw_center(16, 16)

        self.draw_guideline(6, 6)
        self.draw_guideline(13, 6)
        self.draw_guideline(6, 13)
        self.draw_guideline(13, 13)

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


    def draw_center(self, x_offset, y_offset):
        hue = self.center_color.hue()
        saturation = self.center_color.saturation()
        value = self.center_color.value()
        hue = (hue + self.color_adj * (x_offset + y_offset - self.sq_num)) % 360
        adjust_color = QtGui.QColor.fromHsv(hue, saturation, value)

        pen = QtGui.QPen(adjust_color)
        self.painter.setPen(pen)
        brush = QtGui.QBrush(adjust_color)
        self.painter.setBrush(brush)
        self.painter.drawRect(x_offset * self.sq_size,
                              y_offset * self.sq_size,
                              2 * self.sq_size, 2 * self.sq_size)

    def draw_guideline(self, x_offset, y_offset):
        pen = QtGui.QPen(self.center_color)
        self.painter.setPen(pen)
        brush = QtGui.QBrush(self.center_color)
        self.painter.setBrush(brush)
        self.painter.drawRect(x_offset * self.sq_size,
                              y_offset * self.sq_size,
                              self.sq_size, self.sq_size)
        

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

    
        
                      
