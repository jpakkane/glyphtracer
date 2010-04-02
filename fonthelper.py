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
    

class Window(QWidget):
    def __init__(self, image_file, parent = None):
        QWidget.__init__(self, parent)
        self.resize(640, 480)
        self.image = QImage(image_file)
        evaluate_horizontal_cuts(self.image)

    def paintEvent(self, event):
        paint = QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        paint.end()
        print self.image.pixelIndex(33, 18)

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = Window(sys.argv[1])
    myapp.show()
    sys.exit(app.exec_())
