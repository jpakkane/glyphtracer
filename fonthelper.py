#!/usr/bin/python
# -*- coding: utf-8 -*-

#    Fonthelper
#    Copyright (C) 2010 Jussi Pakkanen
#                                     
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or   
#    (at your option) any later version.                                 
#                                                                        
#    This program is distributed in the hope that it will be useful,     
#    but WITHOUT ANY WARRANTY; without even the implied warranty of      
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       
#    GNU General Public License for more details.                        
#                                                                        
#    You should have received a copy of the GNU General Public License   
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, tempfile
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from fhlib import *

start_dialog = None
main_win = None

#from editor import Ui_MainWindow

def is_image_file_valid(fname):
    im = QImage(fname)
    if im.isNull() or im.depth() != 1:
        return False
    return True

def calculate_horizontal_sums(image):
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
        (y0, y1) = xs
        cur_image = image.copy(0, y0, w, y1-y0).transformed(rotate)
        ystrips = calculate_cutlines_locations(calculate_horizontal_sums(cur_image))
        for ys in ystrips:
            (x0, x1) = ys
            box = LetterBox(QRect(x0, y0, x1-x0, y1-y0))
            boxes.append(box)
    return boxes


class LetterBox():
    def __init__(self, rectangle):
        self.r = rectangle
        self.taken = False

class Window(QWidget):
    def __init__(self, image_file, parent = None):
        QWidget.__init__(self, parent)
        self.resize(640, 480)
        self.image = QImage(image_file)
        strips = calculate_horizontal_sums(self.image)
        hor_lines = calculate_cutlines_locations(strips)
        self.boxes = calculate_letter_boxes(self.image, hor_lines)

    def paintEvent(self, event):
        w = self.image.width()
        paint = QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        paint.setPen(pen)
        b = QBrush(QColor(0, 0, 0, 127))
        for box in self.boxes:
            paint.drawRect(box.r)
            if box.taken:
                paint.fillRect(box.r, b)
        #paint.setPen(pen)
        paint.end()

     
class StartDialog(QWidget):
    def __init__(self, initial_file_name=None):
        QWidget.__init__(self)
        self.resize(512, 200)
        
        self.grid = QGridLayout()
        self.name_edit = QLineEdit('Foobar')
        self.file_edit = QLineEdit()
        if initial_file_name is not None:
            self.file_edit.setText(initial_file_name)
        self.file_button = QPushButton('Browse')
        self.connect(self.file_button, SIGNAL('clicked()'), self.open_file)
        self.combo = QComboBox()
        self.combo.addItem('Regular')
        self.combo.addItem('Bold')
        self.combo.addItem('Italic')
        self.combo.addItem('BoldItalic')
        
        self.grid.setSpacing(10)
        self.grid.addWidget(QLabel('Font name'), 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1, 1, 2)
        self.grid.addWidget(QLabel('Type'), 1, 0)
        self.grid.addWidget(self.combo, 1, 1, 1, 2)
        self.grid.addWidget(QLabel('Image file'), 2, 0)
        self.grid.addWidget(self.file_edit, 2, 1)
        self.grid.addWidget(self.file_button, 2, 2)
        
        hbox = QHBoxLayout()
        start_button = QPushButton('Start')
        self.connect(start_button, SIGNAL('clicked()'), self.start_edit)
        hbox.addWidget(start_button)
        quit_button = QPushButton('Quit')
        self.connect(quit_button, SIGNAL('clicked()'), qApp, SLOT('quit()'))
        hbox.addWidget(quit_button)
        w = QWidget()
        w.setLayout(hbox)
        self.grid.addWidget(w, 3, 0, 1, 3)
        
        self.setLayout(self.grid)
        
    def open_file(self):
        fname = QFileDialog.getOpenFileName(self)
        if fname is not None and fname != '':
            self.file_edit.setText(fname)    
    
    def start_edit(self):
        global main_win, start_dialog
        fname = self.file_edit.text()
        if not is_image_file_valid(fname):
            QMessageBox.critical(self, "Error", "Selected file is not a 1 bit image.")
            return
        start_dialog.hide()
        main_win = Window(fname)
        main_win.show()

class EditorWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.resize(512, 200)
        
        self.grid = QGridLayout()
        sa = QScrollArea()
        self.grid.addWidget(sa, 0, 0, 1, 4)
        
        self.combo = QComboBox()
        self.combo.addItem('fo')
        self.grid.addWidget(self.combo, 1, 0, 1, 1)
        
        self.grid.addWidget(QLabel('Glyph:'), 1, 1, 1, 1)
        self.glyphname = QLabel()
        self.grid.addWidget(self.glyphname, 1, 2, 1, 1)
        self.save = QPushButton('Generate SFD file')
        self.grid.addWidget(self.save, 1, 3, 1, 1)
        
        self.setLayout(self.grid)
        
def start_program():
    global start_dialog
    app = QApplication(sys.argv)
    #myapp = Window(sys.argv[1])
    if len(sys.argv) > 1:
        start_dialog = StartDialog(sys.argv[1])
    else:
        start_dialog = StartDialog()
    start_dialog.show()
    sys.exit(app.exec_())

def test_edwin():
    app = QApplication(sys.argv)
    bob = EditorWindow()
    bob.show()
    sys.exit(app.exec_())


def test_potrace():
    image = QImage(sys.argv[1])
    tfile = tempfile.NamedTemporaryFile(suffix='.pgm')
    tempname = tfile.name
    tfile.close()
    if not image.save(tempname):
        print "Danger!"
    points = potrace_image(tempname)
    os.unlink(tempname)
    write_sfd(file('test_out.sfd', 'w'), points)
    
if __name__ == "__main__":
    #start_program()
    #test_potrace()
    test_edwin()
