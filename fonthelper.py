#!/usr/bin/python

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from editor import Ui_MainWindow

def evaluate_horizontal_cuts(image):
    (w, h) = (image.width(), image.height())
    sums = []
    for j in xrange(h):
        total = 0
        for i in xrange(w):
            total += image.pixelIndex(i, j)
        sums.append(total)
    print sums
    return sums
    
def calculate_cutlines_locations(sums):
    element_strips = []
    cutoff = 5
    
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


class Window(QWidget):
    def __init__(self, image_file, parent = None):
        QWidget.__init__(self, parent)
        self.resize(640, 480)
        self.image = QImage(image_file)
        strips = evaluate_horizontal_cuts(self.image)
        print calculate_cutlines_locations(strips)

    def paintEvent(self, event):
        paint = QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        paint.end()

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = Window(sys.argv[1])
    myapp.show()
    sys.exit(app.exec_())
