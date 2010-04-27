#!/usr/bin/python
# -*- coding: utf-8 -*-

#    Glyphtracer
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

import os, sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from gtlib import *

start_dialog = None
main_win = None

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

class SelectionArea(QWidget):
    def __init__(self, image_file, master_widget, parent = None):
        QWidget.__init__(self, parent)
        self.master = master_widget
        self.image = QImage(image_file)
        self.resize(self.image.width(), self.image.height())
        
        strips = calculate_horizontal_sums(self.image)
        hor_lines = calculate_cutlines_locations(strips)
        self.boxes = calculate_letter_boxes(self.image, hor_lines)
        self.active_box = None

        self.selected_brush = QBrush(QColor(0, 0, 0, 127))
        self.active_brush = QBrush(QColor(255, 0, 0, 127))

    def paintEvent(self, event):
        w = self.image.width()
        paint = QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        paint.setPen(pen)
        for box in self.boxes:
            paint.drawRect(box.r)
            if box is self.active_box:
                paint.fillRect(box.r, self.active_brush)                
            elif box.taken:
                paint.fillRect(box.r, self.selected_brush)
        #paint.setPen(pen)
        paint.end()
        
    def find_box(self, x, y):
        for b in self.boxes:
            if b.contains(x, y):
                return b
        return None
    
    def set_active_box(self, box):
        self.active_box = box
        
    def take_box(self, box):
        box.taken = True
    
    def mousePressEvent(self, me):
        # I could not figure out how to connect
        # to events in some other widget, so
        # we have this ugly hack.
        self.master.user_click(me)
            
class StartDialog(QWidget):
    def __init__(self, initial_file_name=None):
        QWidget.__init__(self)
        self.resize(512, 200)
        
        self.grid = QGridLayout()
        self.name_edit = QLineEdit('MyFont')
        self.file_edit = QLineEdit()
        self.output_edit = QLineEdit()
        if initial_file_name is not None:
            self.file_edit.setText(initial_file_name)
            self.set_output_file_from_source(initial_file_name)
        self.file_button = QPushButton('Browse')
        self.connect(self.file_button, SIGNAL('clicked()'), self.open_file)
        
        self.grid.setSpacing(10)
        self.grid.addWidget(QLabel('Font name'), 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1, 1, 2)
        self.grid.addWidget(QLabel('Image file'), 1, 0)
        self.grid.addWidget(self.file_edit, 1, 1)
        self.grid.addWidget(self.file_button, 1, 2)
        self.grid.addWidget(QLabel('Output file'), 2, 0)
        self.grid.addWidget(self.output_edit, 2, 1, 1, 2)
        
        hbox = QHBoxLayout()
        about_button = QPushButton('About')
        self.connect(about_button, SIGNAL('clicked()'), self.about_message)
        hbox.addWidget(about_button)
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
            self.set_output_file_from_source(fname)
    
    def set_output_file_from_source(self, name):
        parts = str(name).split('.')
        if len(parts) > 1:
            parts = parts[:-1]
        parts.append('sfd')
        self.output_edit.setText('.'.join(parts))
    
    def about_message(self):
        QMessageBox.information(self, "About " + program_name, program_name + " is (C) 2010 Jussi Pakkanen.\nIt is available under the Gnu General Public License v3 or later..")
    
    def does_file_exist(self, fname):
        try:
            f = file(fname, 'r')
            return True
        except IOError:
            return False
    
    def start_edit(self):
        global main_win, start_dialog
        fname = self.file_edit.text()
        output = self.output_edit.text()
        font_name = self.name_edit.text()
        if not is_image_file_valid(fname):
            QMessageBox.critical(self, "Error", "Selected file is not a 1 bit image.")
            return
        if self.does_file_exist(output):
            if QMessageBox.critical(self, "File exists", "Output file %s already exists." % output,\
                                       'Overwrite it', 'Select a different file') != 0:
                return
        start_dialog.hide()
        main_win = EditorWindow(fname, font_name, output)
        main_win.show()

class EditorWindow(QWidget):
    def __init__(self, image_file, font_name, sfd_file, parent=None):
        QWidget.__init__(self)
        self.resize(640, 400)
        self.active_glyph = 0
        self.glyphlist = []
        self.font_name = font_name
        self.sfd_file = sfd_file
        
        self.setWindowTitle(program_name + ': ' + image_file)
        
        self.grid = QGridLayout()
        self.area = SelectionArea(image_file, self)
        sa = QScrollArea()
        sa.setWidget(self.area)
        self.grid.addWidget(sa, 0, 0, 1, 6)
        
        b = QPushButton('Previous glyph')
        self.connect(b, SIGNAL('clicked()'), self.previous_button)
        self.grid.addWidget(b, 1, 1, 1, 1)
        b = QPushButton('Next glyph')
        self.connect(b, SIGNAL('clicked()'), self.next_button)
        self.grid.addWidget(b, 1, 2, 1, 1)
        
        self.grid.addWidget(QLabel('Glyph:'), 1, 3, 1, 1)
        self.glyph_label = QLabel()
        self.glyph_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.grid.addWidget(self.glyph_label, 1, 4, 1, 1)
        self.save = QPushButton('Generate SFD file')
        self.connect(self.save, SIGNAL('clicked()'), self.generate_sfd)
        self.grid.addWidget(self.save, 1, 5, 1, 1)
        
        self.combo = QComboBox()
        self.build_combo()
        self.connect(self.combo, SIGNAL('activated(int)'), self.glyph_set_changed)
        self.grid.addWidget(self.combo, 1, 0, 1, 1)
        
        self.setLayout(self.grid)
        
    def build_combo(self):
        self.groups = {}
        for name, glyphs in glyph_groups:
            self.groups[name] = [data_to_glyphinfo(x) for x in glyphs]
            self.combo.addItem(name)
        self.glyph_set_changed(0)
    
    def user_click(self, mouse_event):
        (x, y) = (mouse_event.x(), mouse_event.y())
        newbox = self.area.find_box(x, y)
        if newbox:
            self.unselect(newbox)
            self.area.take_box(newbox)
            oldbox = self.glyphlist[self.active_glyph].box
            if oldbox is not None:
                oldbox.taken = False
            self.glyphlist[self.active_glyph].box = newbox
            self.go_to_next_glyph() 
        
    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Space:
            forward = True
        else:
            forward = False
        self.go_to_next_glyph(forward)
        
    def next_button(self):
        self.go_to_next_glyph(True)
    
    def previous_button(self):
        self.go_to_next_glyph(False)
        
    def go_to_next_glyph(self, forward=True):
        if forward:
            shift = 1
        else:
            shift = -1
        gs = len(self.glyphlist)
        self.active_glyph = (self.active_glyph + shift + gs) % gs
        self.glyph_info_changed()
        
    def glyph_set_changed(self, i):
        self.active_glyph = 0
        self.glyphlist = self.groups[str(self.combo.currentText())]
        self.glyph_info_changed()

    def glyph_info_changed(self):
        self.set_glyph_info()
        self.area.set_active_box(self.glyphlist[self.active_glyph].box)
        self.area.repaint()
        
        
    def set_glyph_info(self):
        g = self.glyphlist[self.active_glyph]
        text = u'%s (%s)' % (unicode(g.name), unichr(g.codepoint))
        self.glyph_label.setText(text)
        
    def unselect(self, box):
        box.taken = False
        for name in self.groups.keys():
            for g in self.groups[name]:
                if g.box is box:
                    g.box = None
                    return
        
    def get_selected_glyphs(self):
        selected = []
        for name in self.groups.keys():
            selected += filter(lambda x: x.box is not None, self.groups[name])
        return selected
        
    def generate_sfd(self):
        selected = self.get_selected_glyphs()
        if len(selected) == 0:
            QMessageBox.critical(self, "Error", "No glyphs selected, can not generate sfd file.\n")
            return
        try:
            write_sfd(self.sfd_file, self.font_name, self.area.image, selected)
        except Exception, e:
            QMessageBox.critical(self, "Error", "Sfd generation failed:\n" + str(e))
            return
            
        QMessageBox.information(self, "Success", "Sfd file successfully generated.")
        
def start_program():
    global start_dialog
    app = QApplication(sys.argv)
    if not i_haz_potrace():
        QMessageBox.critical(None, program_name, "Potrace executable not in path, exiting.")
        sys.exit(127)
    if len(sys.argv) > 1:
        start_dialog = StartDialog(sys.argv[1])
    else:
        start_dialog = StartDialog()
    start_dialog.setWindowTitle(program_name)
    start_dialog.show()
    sys.exit(app.exec_())

def test_edwin():
    app = QApplication(sys.argv)
    bob = EditorWindow(sys.argv[1], 'temporary_out.sfd', 'MyFont')
    bob.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    start_program()
    #test_edwin()
