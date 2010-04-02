#!/usr/bin/python

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from editor import Ui_MainWindow

class Window(QWidget):
    def __init__(self, image_file, parent = None):
        QWidget.__init__(self, parent)
        self.resize(640, 480)
        self.image = QPixmap(image_file)

    def paintEvent(self, event):
        paint = QPainter()
        paint.begin(self)
        paint.drawPixmap(0, 0, self.image)
        paint.end()

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = Window(sys.argv[1])
    myapp.show()
    sys.exit(app.exec_())
