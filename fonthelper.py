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

import os, sys, subprocess, tempfile
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


def potrace_image(image):
    pass

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
        global main_win
        fname = self.file_edit.text()
        if not is_image_file_valid(fname):
            QMessageBox.critical(self, "Error", "Selected file is not a 1 bit image.")
            return
        start_dialog.hide()
        main_win = Window(fname)
        main_win.show()
        
def start_program():
    app = QApplication(sys.argv)
    #myapp = Window(sys.argv[1])
    if len(sys.argv) > 1:
        start_dialog = StartDialog(sys.argv[1])
    else:
        start_dialog = StartDialog()
    start_dialog.show()
    sys.exit(app.exec_())

def integerise(command_line):
    return [int(x) for x in command_line.split()[0:-1]]
    

def parse_postscript(commands):
    point_sets = []
    points = []
    assert(commands[0].endswith('moveto'))
    for cmd in commands:
        if cmd.endswith('moveto'):
            assert(len(points) == 0)
            points.append(integerise(cmd))
        elif cmd.endswith('rcurveto'):
            points.append(integerise(cmd))
        elif cmd.endswith('rlineto'):
            points.append(integerise(cmd))
        elif cmd.endswith('closepath'):
            point_sets.append(points)
            points = []
        else:
            raise RuntimeError('Unknown PostScript command: ' + cmd)
    assert(len(points) == 0)
    return point_sets

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
    
def potrace_image(filename):
    p = subprocess.Popen('potrace -c --eps -q ' + filename + ' -o -', shell=True, stdout=subprocess.PIPE)
    (so, se) = p.communicate()
    lines = so.split('\n')
    while not lines[0].endswith('moveto'):
        lines.pop(0)
    while not lines[-1].endswith('closepath'):
        lines.pop()
    pointset = parse_postscript(lines)
    pointset = map(convert_points, pointset)
    return pointset

def convert_points(pointlist):
    pointlist = to_absolute(pointlist)
    return pointlist
    #pointlist.reverse()
    #return [flip_point(x) for x in pointlist]

def to_absolute(pointlist):
    starting_point = pointlist[0]
    assert(len(starting_point) == 2)
    converted = [starting_point]
    current_point = starting_point
    for p in pointlist[1:]:
        newp = []
        if len(p) == 2:
            newp = [current_point[0] + p[0], current_point[1] + p[1]]
        elif len(p) == 6:
            newp = [0]*6
            newp[0] = current_point[0] + p[0]
            newp[1] = current_point[1] + p[1]
            newp[2] = newp[0] + p[2]
            newp[3] = newp[1] + p[3]
            newp[4] = newp[2] + p[4]
            newp[5] = newp[3] + p[5]
        else:
            raise RuntimeError('Unknown pixel size error.')
#        for i in range(len(p)/2):
#            current_point = [current_point[0] - p[i*2], current_point[1] - p[i*2+1]]
#            p[i*2] = current_point[0]
#            p[i*2+1] = current_point[1]
        converted.append(newp)
        current_point = [newp[-2], newp[-1]]
    return converted

def flip_point(p):
    if len(p) == 2:
        return p
    elif len(p) == 6:
        return [p[2], p[3], p[0], p[1], p[4], p[5]]
    else:
        raise RuntimeError('Unknown pixel size error.')
  

def write_sfd(ofile, points):
    font_name = 'dummy'
    full_name = 'dummy'
    family_name = 'dummy'
    num_letters = len(points)
    ofile.write(sfd_header % (font_name, full_name, family_name, num_letters))
    
    # for letter in xxx
    letter_name = 'a'
    width = 672
    location1 =  97
    location2 = 97
    location3 = 0
    ofile.write(letter_header % (letter_name, location1, location2, location3, width))
    for curve in points:
        fp = curve[0]
        assert(len(fp) == 2)
        ofile.write("%d %d m 0\n" % tuple(fp))

        for i in xrange(1, len(curve)):
            point = curve[i]
            ofile.write(' ')
            ofile.write(' '.join([str(x) for x in point]))
            # Print move commands.
            if len(point) == 6:
                if i < len(curve)-1 and len(curve[i+1]) == 2:
                    flags = 2
                else:
                    flags = 0
                ofile.write(' c %d\n' % flags)
            elif len(point) == 2:
                if i < len(curve)-1 and len(curve[i+1]) == 2:
                    flags = 1
                else:
                    flags = 2
                ofile.write(' l %d\n' % flags)
            else:
                raise RuntimeError('Incorrect amount of points: %d' % len(points))
    ofile.write(letter_footer)
    ofile.write(sfd_footer)

if __name__ == "__main__":
    #start_program()
    test_potrace()
