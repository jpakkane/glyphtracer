#!/usr/bin/python

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from editor import Ui_MainWindow

def calculate_horizontal_cuts(image):
    (w, h) = (image.width(), image.height())
    sums = []
    for j in xrange(h):
        total = 0
        for i in xrange(w):
            total += image.pixelIndex(i, j)
        sums.append(total)
    return sums
    
def calculate_cutlines_locations(sums):
    element_strips = []
    cutoff = 0
    
    if sums[0] <= cutoff:
        background_strip = True
    else:
        background_strip = False
    strip_start = 0
    
    for i in xrange(len(sums)):
        if sums[i] <= cutoff:
            background = True
        else:
            background = False
        if background == background_strip:
            continue
        
        # We crossed a region.
        if background:
           strip_end = i-1;
           element_strips.append((strip_start, strip_end))
        strip_start = i
        background_strip = background
          
    if strip_start < len(sums) and not background_strip:
        strip_end = len(sums) - 1
        element_strips.append((strip_start, strip_end))
    return element_strips

def calculate_letter_boxes(image, xstrips):
    boxes = []
    (w, h) = (image.width(), image.height())
    rotate = QMatrix().rotate(90)
    for xs in xstrips:
        print xs
        (y0, y1) = xs
        cur_image = image.copy(0, y0, w, y1-y0).transformed(rotate)
        print "Size", cur_image.width(), cur_image.height()
        ystrips = calculate_cutlines_locations(calculate_horizontal_cuts(cur_image))
        for ys in ystrips:
            (x0, x1) = ys
            boxes.append(QRect(x0, y0, x1-x0, y1-y0))
    return boxes


class Window(QWidget):
    def __init__(self, image_file, parent = None):
        QWidget.__init__(self, parent)
        self.resize(640, 480)
        self.image = QImage(image_file)
        strips = calculate_horizontal_cuts(self.image)
        self.hor_lines = calculate_cutlines_locations(strips)
        self.boxes = calculate_letter_boxes(self.image, self.hor_lines)

    def paintEvent(self, event):
        w = self.image.width()
        paint = QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        paint.setPen(pen)
        for box in self.boxes:
            paint.drawRect(box)

        paint.end()

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = Window(sys.argv[1])
    myapp.show()
    sys.exit(app.exec_())
