import sys
import random
import math
from PySide6 import QtCore, QtWidgets, QtGui

# A quilt is an M x N rectangle of squares
# Each square is I x I pixels
# The leaf level patterns are lists of polygons of a particular color,
# aka list of Elements.
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

    def re_color(self, hue, saturation, value):
        coords = list(map(lambda pt: (pt.x(), pt.y()), self.coords))
        return Element(self.height, self.width, coords, hue,
                       saturation, value)

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

    def rotate_point(self, pt, angle):
        if angle == 90:
            return (self.width - pt.y(), pt.x())
        elif angle == 180:
            return (self.width - pt.x(), self.height - pt.y())
        elif angle == 270:
            return (pt.y() , self.height - pt.x())
        else:
            return (pt.x(), pt.y())

    def rotate(self, angle):
        coords = list(map(lambda pt: self.rotate_point(pt, angle), self.coords))
        return Element(self.height, self.width, coords, self.color.hue(),
                       self.color.saturation(), self.color.value())

# This quilt class will create and return a QPixmap
class QuiltPattern:
    def __init__(self, sq_size, sq_num):
        self.sq_size = sq_size
        self.sq_num = sq_num
        self.total_size = self.sq_num * self.sq_size

        # Our pattern is a map from quilt coordinate (x, y) -> [Element]
        self.pattern = {}

        self.background_color = QtGui.QColor("white")
        self.guideline_color = QtGui.QColor("lightgrey")

    def copy_pattern(self, dest_ul, wh, source_ul, elem_map = lambda x: x):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + i, source_ul[1] + j)
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = list(map(elem_map, self.pattern[source]))

    def horizontal_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + (wh[0] - 1 - i), source_ul[1] + j)
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = list(map(lambda el: el.horizontal_flip(), self.pattern[source]))

    def vertical_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + i, source_ul[1] + (wh[1] - 1 - j))
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = list(map(lambda el: el.vertical_flip(), self.pattern[source]))

    def both_flip(self, dest_ul, wh, source_ul):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                source = (source_ul[0] + (wh[0] - 1 - i),
                          source_ul[1] + (wh[1] - 1 - j))
                dest = (dest_ul[0] + i, dest_ul[1] + j)
                if source in self.pattern:
                    self.pattern[dest] = list(map(lambda el: el.both_flip(), self.pattern[source]))

    # Example for rotation
    #
    #              i
    #        0 | 1 | 2 | 3
    #      -----------------
    #    0 | a | b | c | d |
    #      -----------------
    # j  1 | e | f | g | h |
    #      -----------------
    #    2 | i | j | k | l |
    #      -----------------

                    
    def rotate(self, dest_ul, wh, source_ul, angle):
        if angle == 90:
            # rotate((2, 1), (2, 2), (0, 0), 90)
            # means "put a, b, e, f where h, l, g, k currently are"
            # Note that destination space, including wh, is rotated
            # wrt source space
            # (i = 0, j = 0): (2, 1) <- (0, 1), (2+i, 1+j) <- (0+j, wh[0]-1-i)
            # (i = 0, j = 1): (2, 2) <- (1, 1), (2+i, 1+j) <- (0+j, wh[0]-1-i)
            # (i = 1, j = 0): (3, 1) <- (0, 0), (2+i, 1+j) <- (0+j, wh[0]-1-i)
            # (i = 1, j = 1): (3, 2) <- (1, 0), (2+i, 1+j) <- (0+j, wh[0]-1-i)
            #
            for i in range(0, wh[0]):
                for j in range(0, wh[1]):
                    source = (source_ul[0] + j,
                              source_ul[1] + (wh[0] - 1 - i))
                    dest = (dest_ul[0] + i, dest_ul[1] + j)
                    if source in self.pattern:
                        self.pattern[dest] = list(map(lambda el: el.rotate(angle), self.pattern[source]))
        elif angle == 180:
            # rotate((3, 1), (2, 2), (0, 0), 180)
            # means "put a, b, e, f where l, k, h, g currently are"
            # Note that destination space, including wh, is rotated
            # wrt source space
            # (i = 0, j = 0): (2, 1) <- (1, 1), (3-(wh[0]-1)+i, 1+j) <- (0+wh[0]-1-i, wh[1]-1-j)
            # (i = 0, j = 1): (2, 2) <- (1, 0), (3-(wh[0]-1)+i, 1+j) <- (0+wh[0]-1-i, wh[1]-1-j)
            # (i = 1, j = 0): (3, 1) <- (0, 1), (3-(wh[0]-1)+i, 1+j) <- (0+wh[0]-1-i, wh[1]-1-j)
            # (i = 1, j = 1): (3, 2) <- (0, 0), (3-(wh[0]-1)+i, 1+j) <- (0+wh[0]-1-i, wh[1]-1-j)
            #
            for i in range(0, wh[0]):
                for j in range(0, wh[1]):
                    source = (source_ul[0] + (wh[0] - 1 - i),
                              source_ul[1] + (wh[1] - 1 - j))
                    dest = (dest_ul[0] - (wh[0] - 1) + i, dest_ul[1] + j)
                    if source in self.pattern:
                        self.pattern[dest] = list(map(lambda el: el.rotate(angle), self.pattern[source]))
        elif angle == 270:
            # rotate((3, 2), (2, 2), (0, 0), 270)
            # means "put a, b, e, f where k, g, l, h currently are"
            # Note that destination space, including wh, is rotated
            # wrt source space
            # (i = 0, j = 0): (2, 1) <- (1, 0), (3-(wh[0]-1)+i, 2-(wh[1]-1)+j) <- (0+wh[1]-1-j, 0+i)
            # (i = 0, j = 1): (2, 2) <- (0, 0), (3-(wh[0]-1)+i, 2-(wh[1]-1)+j) <- (0+wh[1]-1-j, 0+i)
            # (i = 1, j = 0): (3, 1) <- (1, 1), (3-(wh[0]-1)+i, 2-(wh[1]-1)+j) <- (0+wh[1]-1-j, 0+i)
            # (i = 1, j = 1): (3, 2) <- (0, 1), (3-(wh[0]-1)+i, 2-(wh[1]-1)+j) <- (0+wh[1]-1-j, 0+i)
            #
            for i in range(0, wh[0]):
                for j in range(0, wh[1]):
                    source = (source_ul[0] + (wh[1] - 1 - j),
                              source_ul[1] + i)
                    dest = (dest_ul[0] - (wh[0] - 1) + i, dest_ul[1] - (wh[1] - 1) + j)
                    if source in self.pattern:
                        self.pattern[dest] = list(map(lambda el: el.rotate(angle), self.pattern[source]))
        else:
             for i in range(0, wh[0]):
                for j in range(0, wh[1]):
                    source = (source_ul[0] + i, source_ul[1] + j)
                    dest = (dest_ul[0] + i, dest_ul[1] + j)
                    if source in self.pattern:
                        self.pattern[dest] = self.pattern[source]

    def modify(self, source_ul, wh, elem_map):
        for i in range(0, wh[0]):
            for j in range(0, wh[1]):
                pos = (source_ul[0] + i, source_ul[1] + j)
                if pos in self.pattern:
                    self.pattern[pos] = list(map(elem_map, self.pattern[pos]))


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
        for coord, elems in self.pattern.items():
            for el in elems:
                self.draw_element(coord[0], coord[1], el)

    def pattern_to_pixmap(self):
        pixmap = QtGui.QPixmap(self.total_size, self.total_size)
        pixmap.fill(self.background_color)

        self.painter = QtGui.QPainter(pixmap)

        pen = QtGui.QPen(self.guideline_color)
        self.painter.setPen(pen)
        for x in range(0, self.total_size, self.sq_size):
            self.painter.drawLine(x, 0, x, self.total_size)
            self.painter.drawLine(0, x, self.total_size, x)

        self.draw_pattern()
       
        self.painter.end()

        return pixmap

class OhioStarlightQuilt(QuiltPattern):
    def __init__(self):
        super().__init__(30, 20)
        
        self.center_element = Element(self.sq_size, self.sq_size,
                                      [(0, 0), (0, self.sq_size),
                                       (self.sq_size, self.sq_size),
                                       (self.sq_size, 0), (0, 0)],
                                      60, 85, 50)

        self.checker_element = Element(self.sq_size, self.sq_size,
                                      [(0, 0), (0, self.sq_size),
                                       (self.sq_size//2, self.sq_size),
                                       (self.sq_size//2, self.sq_size//2),
                                       (self.sq_size, self.sq_size//2),
                                       (self.sq_size, 0), (0, 0)],
                                       255, 85, 160)

        self.triangle_element = Element(self.sq_size, self.sq_size,
                                        [(0, 0), (self.sq_size, self.sq_size),
                                         (0, self.sq_size), (0, 0)],
                                        210, 85, 255)

    # TODO: Make the pattern of drawing into a data structure and/or file
    # format.
    def draw(self):
        # Define basic checkerboard pair.
        self.pattern[(0, 0)] = [self.checker_element]
        self.copy_pattern((1, 1), (1, 1), (0, 0))

        # Copy and flip checkerboard.
        self.horizontal_flip((4, 0), (2, 2), (0, 0))
        self.vertical_flip((0, 4), (2, 2), (0, 0))
        self.both_flip((4, 4), (2, 2), (0, 0))

        # Define basic hourglass pattern made up of triangles.
        self.pattern[(2, 0)] = [self.triangle_element]
        self.pattern[(2, 1)] = [self.triangle_element.vertical_flip().re_color(15, 85, 230)]
        self.pattern[(3, 0)] = [self.triangle_element.horizontal_flip().re_color(5, 85, 220)]
        self.pattern[(3, 1)] = [self.triangle_element.both_flip().re_color(220, 85, 240)]

        # Rotate hourglass pattern to three remaining sides of center.
        self.rotate((4, 2), (2, 2), (2, 0), 90)
        self.rotate((3, 4), (2, 2), (2, 0), 180)
        self.rotate((1, 3), (2, 2), (2, 0), 270)

        # Define center blocks.
        self.pattern[(2, 2)] = [self.center_element]
        self.horizontal_flip((3, 2), (1, 1), (2, 2))
        self.vertical_flip((2, 3), (2, 1), (2, 2))

        # Copy center color to grid intersections.
        self.copy_pattern((6, 6), (1, 1), (2, 2))
        self.horizontal_flip((13, 6), (1, 1), (6, 6))
        self.vertical_flip((6, 13), (1, 1), (6, 6))
        self.both_flip((13, 13), (1, 1), (6, 6))

        # Copy combination pattern to eight new locations.
        self.copy_pattern((0, 7), (6, 6), (0, 0))
        self.copy_pattern((0, 14), (6, 6), (0, 0))
        self.copy_pattern((7, 0), (6, 6), (0, 0))
        self.copy_pattern((7, 7), (6, 6), (0, 0))
        self.copy_pattern((7, 14), (6, 6), (0, 0))
        self.copy_pattern((14, 0), (6, 6), (0, 0))
        self.copy_pattern((14, 7), (6, 6), (0, 0))
        self.copy_pattern((14, 14), (6, 6), (0, 0))

        return self.pattern_to_pixmap()


class MichiganStarlightQuilt(OhioStarlightQuilt):
    def __init__(self):
        super().__init__()
        
        self.center_element = Element(self.sq_size, self.sq_size,
                                      [(self.sq_size, 0),
                                       (self.sq_size, self.sq_size),
                                       (0, self.sq_size),
                                       (self.sq_size, 0)],
                                      60, 85, 140)

        # Produce a quarter circle of points from 3*pi/2 to 2*pi.
        arc = [(round(self.sq_size * (math.cos(math.pi * (1.5 + i/24.0)))),
                round(-self.sq_size * (math.sin(math.pi * (1.5 + i/24.0)))))
               for i in range(0, 13)]
        arc.append((0, 0))
        arc.append((0, self.sq_size))
        
        self.checker_element = Element(self.sq_size, self.sq_size, arc,
                                       255, 85, 160)

        # Produce a quarter circle of points from pi to 3*pi/2.
        arc = [(round(self.sq_size * (1.0 + math.cos(math.pi * (1.0 + i/24.0)))),
                round(-self.sq_size * (math.sin(math.pi * (1.0 + i/24.0)))))
               for i in range(0, 13)]
        arc.append((0, self.sq_size))
        arc.append((0, 0))
        
        self.triangle_element = Element(self.sq_size, self.sq_size, arc,
                                        210, 85, 255)


class DoubleChurnQuilt(QuiltPattern):
    def __init__(self):
        super().__init__(30, 15)
        
        self.solid_square = Element(self.sq_size, self.sq_size,
                                    [(0, 0), (0, self.sq_size),
                                     (self.sq_size, self.sq_size),
                                     (self.sq_size, 0), (0, 0)],
                                    60, 85, 0)

        self.solid_triangle = Element(self.sq_size, self.sq_size,
                                      [(0, self.sq_size),
                                       (self.sq_size, self.sq_size),
                                       (self.sq_size, 0), (0, self.sq_size)],
                                      60, 85, 0)

        self.half_block = Element(self.sq_size, self.sq_size,
                                  [(0, self.sq_size//2),
                                   (self.sq_size, self.sq_size//2),
                                   (self.sq_size, self.sq_size),
                                   (0, self.sq_size), (0, self.sq_size//2)],
                                  220, 85, 230)

    def draw(self):
        self.pattern[(0, 0)] = [self.solid_triangle]
        self.copy_pattern((1, 1), (1, 1), (0, 0))
        self.horizontal_flip((3, 0), (2, 2), (0, 0))
        self.vertical_flip((0, 3), (2, 2), (0, 0))
        self.both_flip((3, 3), (2, 2), (0, 0))

        self.pattern[(2, 2)] = [self.solid_square]

        # Make three half blocks in a row
        self.pattern[(1, 0)] = [self.half_block]
        self.pattern[(2, 0)] = [self.half_block]
        self.pattern[(3, 0)] = [self.half_block]

        self.rotate((4, 1), (1, 3), (1, 0), 90)
        self.rotate((3, 4), (3, 1), (1, 0), 180)
        self.rotate((0, 3), (1, 3), (1, 0), 270)

        # Make single half blocks
        self.pattern[(2, 1)] = [self.half_block]

        self.rotate((3, 2), (1, 1), (2, 1), 90)
        self.rotate((2, 3), (1, 1), (2, 1), 180)
        self.rotate((1, 2), (1, 1), (2, 1), 270)

        def map_color(elem, hue):
            saturation = elem.color.saturation()
            value = elem.color.value()
            return elem.re_color(hue, saturation, value)
        
        # Copy combination pattern to eight new locations.
        self.copy_pattern((0, 5), (5, 5), (0, 0), lambda elem: map_color(elem, 40))
        self.copy_pattern((0, 10), (5, 5), (0, 0), lambda elem: map_color(elem, 345))
        self.copy_pattern((5, 0), (5, 5), (0, 0), lambda elem: map_color(elem, 290))
        self.copy_pattern((5, 5), (5, 5), (0, 0), lambda elem: map_color(elem, 5))
        self.copy_pattern((5, 10), (5, 5), (0, 0), lambda elem: map_color(elem, 90))
        self.copy_pattern((10, 0), (5, 5), (0, 0), lambda elem: map_color(elem, 115))
        self.copy_pattern((10, 5), (5, 5), (0, 0), lambda elem: map_color(elem, 185))
        self.copy_pattern((10, 10), (5, 5), (0, 0), lambda elem: map_color(elem, 50))
        
        return self.pattern_to_pixmap()


class CarpentersStarQuilt(QuiltPattern):
    def __init__(self):
        super().__init__(100, 8)
        
        self.solid_triangle_ll = Element(self.sq_size, self.sq_size,
                                         [(0, 0), (0, self.sq_size),
                                          (self.sq_size, self.sq_size), (0, 0)],
                                         120, 85, 230)
        self.solid_triangle_ur = Element(self.sq_size, self.sq_size,
                                         [(0, 0), (self.sq_size, 0),
                                          (self.sq_size, self.sq_size), (0, 0)],
                                         175, 85, 230)


    def draw(self):
        self.pattern[(1, 1)] = [self.solid_triangle_ll, self.solid_triangle_ur]
        self.copy_pattern((2, 1), (1, 1), (1, 1))
        self.copy_pattern((1, 2), (1, 1), (1, 1))
        self.copy_pattern((3, 3), (1, 1), (1, 1))
        
        self.pattern[(2, 0)] = [self.solid_triangle_ll]
        self.horizontal_flip((3, 0), (1, 1), (2, 0))
        self.both_flip((3, 1), (1, 1), (3, 0))
        self.copy_pattern((3, 2), (1, 1), (2, 0))

        self.pattern[(0, 2)] = [self.solid_triangle_ur]
        self.vertical_flip((0, 3), (1, 1), (0, 2))
        self.horizontal_flip((1, 3), (1, 1), (0, 2))
        self.copy_pattern((2, 3), (1, 1), (0, 2))

        self.horizontal_flip((4, 0), (4, 4), (0, 0))
        self.vertical_flip((0, 4), (8, 4), (0, 0))

        self.modify((0, 0), (8, 8), (lambda el: el.re_color(random.randint(0, 359), 85, 230)))
        
        return self.pattern_to_pixmap()

    
class ReducingStarQuilt(QuiltPattern):
    def __init__(self):
        super().__init__(16, 64)
        
        self.solid_triangle1 = Element(self.sq_size, self.sq_size,
                                       [(0, 0), (0, self.sq_size),
                                        (self.sq_size//4, self.sq_size), (0, 0)],
                                       175, 85, 230)
        self.solid_quadrilateral1 = Element(self.sq_size, self.sq_size,
                                            [(0, 0), (0, self.sq_size),
                                             (self.sq_size//2, self.sq_size),
                                             (self.sq_size//4, 0), (0, 0)],
                                            175, 85, 230)
        self.solid_quadrilateral2 = Element(self.sq_size, self.sq_size,
                                            [(0, 0), (0, self.sq_size),
                                             (3*self.sq_size//4, self.sq_size),
                                             (self.sq_size//2, 0), (0, 0)],
                                            175, 85, 230)
        self.solid_quadrilateral3 = Element(self.sq_size, self.sq_size,
                                            [(0, 0), (0, self.sq_size),
                                             (self.sq_size, self.sq_size),
                                             (3*self.sq_size//4, 0), (0, 0)],
                                            175, 85, 230)
        self.solid_square1 = Element(self.sq_size, self.sq_size,
                                     [(0, 0), (0, self.sq_size),
                                      (self.sq_size, self.sq_size),
                                      (self.sq_size, 0), (0, 0)],
                                     175, 85, 230)
        self.solid_square2 = Element(self.sq_size, self.sq_size,
                                     [(0, 0), (0, self.sq_size),
                                      (self.sq_size, self.sq_size),
                                      (self.sq_size, 0), (0, 0)],
                                     99, 85, 180)

        self.diagonal1 = Element(self.sq_size, self.sq_size,
                                 [(0, 0), (0, self.sq_size),
                                  (self.sq_size, self.sq_size), (0, 0)],
                                 175, 85, 230)

        self.diagonal2 = Element(self.sq_size, self.sq_size,
                                 [(0, 0), (self.sq_size, 0),
                                  (self.sq_size, self.sq_size), (0, 0)],
                                 99, 85, 180)

        self.odd_corner1 = Element(self.sq_size, self.sq_size,
                                   [(0, self.sq_size), (self.sq_size, self.sq_size),
                                    (self.sq_size//2, self.sq_size//2),
                                    (0, 3*self.sq_size//4),
                                    (0, self.sq_size)],
                                   175, 85, 230)

        self.odd_corner2 = Element(self.sq_size, self.sq_size,
                                   [(self.sq_size, 0), (self.sq_size, self.sq_size),
                                    (self.sq_size//2, self.sq_size//2),
                                    (3*self.sq_size//4, 0), (self.sq_size, 0)],
                                   99, 85, 180)
        

    def draw(self):
        # Diagonal sides
        self.pattern[(32, 0)] = [self.solid_triangle1]
        self.pattern[(32, 1)] = [self.solid_quadrilateral1]
        self.pattern[(32, 2)] = [self.solid_quadrilateral2]
        self.pattern[(32, 3)] = [self.solid_quadrilateral3]
        self.copy_pattern((33, 4), (1, 4), (32, 0))
        self.copy_pattern((34, 8), (2, 8), (32, 0))
        self.copy_pattern((36, 16), (4, 9), (32, 0))

        self.horizontal_flip((25, 0), (7, 32), (32, 0))
        self.modify((25, 0), (7, 32), (lambda el: el.re_color(99, 85, 180)))

        self.rotate((36, 25), (28, 14), (25, 0), 90)
        self.rotate((38, 36), (14, 28), (25, 0), 180)
        self.rotate((27, 38), (28, 14), (25, 0), 270)

        # Squares
        for y in range(4, 31):
            self.pattern[(32, y)] = [self.solid_square1]
            self.pattern[(31, 63 - y)] = [self.solid_square1]
            self.pattern[(31, y)] = [self.solid_square2]
            self.pattern[(32, 63 - y)] = [self.solid_square2]

        for y in range(8, 30):
            self.pattern[(33, y)] = [self.solid_square1]
            self.pattern[(30, 63 - y)] = [self.solid_square1]
            self.pattern[(33, 63 - y)] = [self.solid_square2]
            self.pattern[(30, y)] = [self.solid_square2]

        for y in range(12, 29):
            self.pattern[(34, y)] = [self.solid_square1]
            self.pattern[(29, 63 - y)] = [self.solid_square1]
            self.pattern[(34, 63 - y)] = [self.solid_square2]
            self.pattern[(29, y)] = [self.solid_square2]

        for y in range(16, 28):
            self.pattern[(35, y)] = [self.solid_square1]
            self.pattern[(28, 63 - y)] = [self.solid_square1]
            self.pattern[(35, 63 - y)] = [self.solid_square2]
            self.pattern[(28, y)] = [self.solid_square2]
        
        for y in range(20, 27):
            self.pattern[(36, y)] = [self.solid_square1]
            self.pattern[(27, 63 - y)] = [self.solid_square1]
            self.pattern[(36, 63 - y)] = [self.solid_square2]
            self.pattern[(27, y)] = [self.solid_square2]

        for y in range(24, 26):
            self.pattern[(37, y)] = [self.solid_square1]
            self.pattern[(26, 63 - y)] = [self.solid_square1]
            self.pattern[(37, 63 - y)] = [self.solid_square2]
            self.pattern[(26, y)] = [self.solid_square2]

        for x in range(4, 31):
            self.pattern[(x, 31)] = [self.solid_square1]
            self.pattern[(63 - x, 32)] = [self.solid_square1]
            self.pattern[(x, 32)] = [self.solid_square2]
            self.pattern[(63 - x, 31)] = [self.solid_square2]

        for x in range(8, 30):
            self.pattern[(x, 30)] = [self.solid_square1]
            self.pattern[(63 - x, 33)] = [self.solid_square1]
            self.pattern[(x, 33)] = [self.solid_square2]
            self.pattern[(63 - x, 30)] = [self.solid_square2]

        for x in range(12, 29):
            self.pattern[(x, 29)] = [self.solid_square1]
            self.pattern[(63 - x, 34)] = [self.solid_square1]
            self.pattern[(x, 34)] = [self.solid_square2]
            self.pattern[(63 - x, 29)] = [self.solid_square2]

        for x in range(16, 28):
            self.pattern[(x, 28)] = [self.solid_square1]
            self.pattern[(63 - x, 35)] = [self.solid_square1]
            self.pattern[(x, 35)] = [self.solid_square2]
            self.pattern[(63 - x, 28)] = [self.solid_square2]

        for x in range(20, 27):
            self.pattern[(x, 27)] = [self.solid_square1]
            self.pattern[(63 - x, 36)] = [self.solid_square1]
            self.pattern[(x, 36)] = [self.solid_square2]
            self.pattern[(63 - x, 27)] = [self.solid_square2]

        for x in range(24, 26):
            self.pattern[(x, 26)] = [self.solid_square1]
            self.pattern[(63 - x, 37)] = [self.solid_square1]
            self.pattern[(x, 37)] = [self.solid_square2]
            self.pattern[(63 - x, 26)] = [self.solid_square2]

        # Diagonals
        self.pattern[(31, 31)] = [self.diagonal1, self.diagonal2]
        self.rotate((32, 31), (1, 1), (31, 31), 90)
        self.rotate((32, 32), (1, 1), (31, 31), 180)
        self.rotate((31, 32), (1, 1), (31, 31), 270)

        for d in range(1, 6):
            self.copy_pattern((31 - d, 31 - d), (1, 1), (31, 31))
            self.copy_pattern((32 + d, 31 - d), (1, 1), (32, 31))
            self.copy_pattern((32 + d, 32 + d), (1, 1), (32, 32))
            self.copy_pattern((31 - d, 32 + d), (1, 1), (31, 32))

        self.pattern[(25, 25)] = [self.odd_corner1, self.odd_corner2]
        self.rotate((38, 25), (1, 1), (25, 25), 90)
        self.rotate((38, 38), (1, 1), (25, 25), 180)
        self.rotate((25, 38), (1, 1), (25, 25), 270)
            
        return self.pattern_to_pixmap()

class NewStarQuilt(QuiltPattern):
    def __init__(self):
        super().__init__(1, 800)

        self.width = 0.15

        def star_shape1(ox, oy, size):
            return [(ox, oy - size + 1),
                    (ox, oy),
                    (ox - round(self.width * size), oy - round(self.width * size)),
                    (ox, oy - size + 1)]

        def star_shape2(ox, oy, size):
            return [(ox, oy - size + 1),
                    (ox, oy),
                    (ox + round(self.width * size), oy - round(self.width * size)),
                    (ox, oy - size + 1)]

        def star_shape3(ox, oy, size):
            return [(ox + size - 1, oy),
                    (ox, oy),
                    (ox + round(self.width * size), oy - round(self.width * size)),
                    (ox + size - 1, oy)]

        def star_shape4(ox, oy, size):
            return [(ox + size - 1, oy),
                    (ox, oy),
                    (ox + round(self.width * size), oy + round(self.width * size)),
                    (ox + size - 1, oy)]
        
        def star_shape5(ox, oy, size):
            return [(ox, oy + size - 1),
                    (ox, oy),
                    (ox + round(self.width * size), oy + round(self.width * size)),
                    (ox, oy + size - 1)]

        def star_shape6(ox, oy, size):
            return [(ox, oy + size - 1),
                    (ox, oy),
                    (ox - round(self.width * size), oy + round(self.width * size)),
                    (ox, oy + size -1)]

        def star_shape7(ox, oy, size):
            return [(ox - size + 1, oy),
                    (ox, oy),
                    (ox - round(self.width * size), oy + round(self.width * size)),
                    (ox - size + 1, oy)]
        
        def star_shape8(ox, oy, size):
            return [(ox - size + 1, oy),
                    (ox, oy),
                    (ox - round(self.width * size), oy - round(self.width * size)),
                    (ox - size + 1, oy)]


        def green_piece(coords):
            return Element(self.sq_size, self.sq_size, coords, 99, 85, 180)

        def blue_piece(coords):
            return Element(self.sq_size, self.sq_size, coords, 175, 85, 230)

        def one_star(x, y, size):
            return [green_piece(star_shape1(x, y, size)),
                    blue_piece(star_shape2(x+1, y, size)),
                    green_piece(star_shape3(x+1, y, size)),
                    blue_piece(star_shape4(x+1, y+1, size)),
                    green_piece(star_shape5(x+1, y+1, size)),
                    blue_piece(star_shape6(x, y+1, size)),
                    green_piece(star_shape7(x, y+1, size)),
                    blue_piece(star_shape8(x, y, size))]

        self.large_star = one_star(399, 399, 400)

        self.medium_star1 = one_star(180, 180, 150)
        self.medium_star2 = one_star(620, 180, 150)
        self.medium_star3 = one_star(620, 620, 150)
        self.medium_star4 = one_star(180, 620, 150)

        self.small_star1 = one_star(90, 90, 50)
        self.small_star2 = one_star(270, 90, 50)
        self.small_star3 = one_star(90, 270, 50)
        self.small_star4 = one_star(530, 90, 50)
        self.small_star5 = one_star(710, 90, 50)
        self.small_star6 = one_star(710, 270, 50)
        self.small_star7 = one_star(710, 530, 50)
        self.small_star8 = one_star(710, 710, 50)
        self.small_star9 = one_star(520, 710, 50)
        self.small_star10 = one_star(270, 710, 50)
        self.small_star11 = one_star(90, 710, 50)
        self.small_star12 = one_star(90, 530, 50)

    def draw(self):
        self.pattern[(0, 0)] = self.large_star + self.medium_star1 + self.medium_star2 + self.medium_star3 + self.medium_star4 + self.small_star1 + self.small_star2 + self.small_star3 + self.small_star4 + self.small_star5 + self.small_star6 + self.small_star7 + self.small_star8 + self.small_star9 + self.small_star10 + self.small_star11 + self.small_star12
        
        return self.pattern_to_pixmap()

    
# A simple drawing window with a QPainter and a QPixmap

class QuiltWindow(QtWidgets.QMainWindow):
    def __init__(self, arg):
        super().__init__()
        self.setWindowTitle("Quilt Pattern")
        self.setGeometry(100, 100, 800, 800)

        if arg == '1':
            self.quilt = OhioStarlightQuilt()
        elif arg == '2':
            self.quilt = MichiganStarlightQuilt()
        elif arg == '3':
            self.quilt = DoubleChurnQuilt()
        elif arg == '4':
            self.quilt = CarpentersStarQuilt()
        elif arg == '5':
            self.quilt = ReducingStarQuilt()
        else:
            self.quilt = NewStarQuilt()
        self.canvas = self.quilt.draw()

        self.label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setPixmap(self.canvas)
        self.setCentralWidget(self.label)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = QuiltWindow(sys.argv[1] if len(sys.argv) > 1 else '1')
    window.show()

    sys.exit(app.exec())

