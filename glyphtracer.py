#!/usr/bin/python3
# -*- coding: utf-8 -*-

#    Glyphtracer
#    Copyright (C) 2010-2021 Jussi Pakkanen
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
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from gtlib import *

start_dialog = None
main_win = None
app = None

def calculate_horizontal_sums(image, show_progress):
    (w, h) = (image.width(), image.height())
    if show_progress:
        prog = QtWidgets.QProgressDialog("Vertical splitting", '', 0, h)
        prog.show()
    sums = []
    for j in range(h):
        total = 0
        for i in range(w):
            total += image.pixelIndex(i, j)
        sums.append(total)
        if show_progress:
            prog.setValue(j)
    if show_progress:
        prog.hide()
    return sums

def calculate_cutlines_locations(sums):
    element_strips = []
    cutoff = 0

    if len(sums) == 0:
        return []
    if sums[0] <= cutoff:
        background_strip = True
    else:
        background_strip = False
    strip_start = 0

    for i in range(len(sums)):
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
    rotate = QtGui.QTransform()
    rotate.rotate(90)
    prog = QtWidgets.QProgressDialog("Horizontal splitting", '', 0, len(xstrips))
    prog.show()
    stripnum = 0
    for xs in xstrips:
        (y0, y1) = xs
        cur_image = image.copy(0, y0, w, y1-y0).transformed(rotate)
        ystrips = calculate_cutlines_locations(calculate_horizontal_sums(cur_image, False))
        for ys in ystrips:
            (x0, x1) = ys
            box = LetterBox(QtCore.QRect(x0, y0, x1-x0, y1-y0))
            boxes.append(box)
        prog.setValue(stripnum)
        stripnum += 1
    prog.hide()
    return boxes

class SelectionArea(QtWidgets.QWidget):
    def __init__(self, image, master_widget, parent = None):
        super().__init__(parent)
        self.master = master_widget
        self.original_image = image
        self.set_zoom(1)

        strips = calculate_horizontal_sums(self.image, True)
        hor_lines = calculate_cutlines_locations(strips)
        self.boxes = calculate_letter_boxes(self.image, hor_lines)
        self.active_box = None

        self.selected_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 127))
        self.active_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 127))

    def set_zoom(self, value):
        self.zoom = value
        self.build_zoom_image()
        self.resize(self.image.width(), self.image.height())

    def build_zoom_image(self):
        if self.zoom == 1:
            self.image = self.original_image
        else:
            w = self.original_image.width()
            self.image = self.original_image.scaledToWidth(w/self.zoom)

    def paintEvent(self, event):
        paint = QtGui.QPainter()
        paint.begin(self)
        paint.drawImage(0, 0, self.image)
        pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine)
        paint.setPen(pen)
        for box in self.boxes:
            zoomed_box = self.scale_box(box.r)
            paint.drawRect(zoomed_box)
            if box is self.active_box:
                paint.fillRect(zoomed_box, self.active_brush)
            elif box.taken:
                paint.fillRect(zoomed_box, self.selected_brush)
        paint.end()

    def scale_box(self, box):
        size = box.size()
        p = box.topLeft()
        scaled_size = QtCore.QSize(int(size.width()/self.zoom), int(size.height()/self.zoom))
        scaled_p = QtCore.QPoint(int(p.x()/self.zoom), int(p.y()/self.zoom))
        return QtCore.QRect(scaled_p, scaled_size)

    def find_box(self, unscaled_x, unscaled_y):
        x = unscaled_x*self.zoom
        y = unscaled_y*self.zoom
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

class StartDialog(QtWidgets.QWidget):
    def __init__(self, initial_file_name=None):
        super().__init__()
        self.resize(512, 200)

        self.grid = QtWidgets.QGridLayout()
        self.name_edit = QtWidgets.QLineEdit('MyFont')
        self.file_edit = QtWidgets.QLineEdit()
        self.output_edit = QtWidgets.QLineEdit()
        if initial_file_name is not None:
            self.file_edit.setText(initial_file_name)
            self.set_output_file_from_source(initial_file_name)
        self.file_button = QtWidgets.QPushButton('Browse')
        self.file_button.clicked.connect(self.open_file)

        self.grid.setSpacing(10)
        self.grid.addWidget(QtWidgets.QLabel('Font name'), 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1, 1, 2)
        self.grid.addWidget(QtWidgets.QLabel('Image file'), 1, 0)
        self.grid.addWidget(self.file_edit, 1, 1)
        self.grid.addWidget(self.file_button, 1, 2)
        self.grid.addWidget(QtWidgets.QLabel('Output file'), 2, 0)
        self.grid.addWidget(self.output_edit, 2, 1, 1, 2)

        hbox = QtWidgets.QHBoxLayout()
        about_button = QtWidgets.QPushButton('About')
        about_button.clicked.connect(self.about_message)
        hbox.addWidget(about_button)
        start_button = QtWidgets.QPushButton('Start')
        start_button.clicked.connect(self.start_edit)
        hbox.addWidget(start_button)
        quit_button = QtWidgets.QPushButton('Quit')
        quit_button.clicked.connect(self.quit_app)
        hbox.addWidget(quit_button)
        w = QtWidgets.QWidget()
        w.setLayout(hbox)
        self.grid.addWidget(w, 3, 0, 1, 3)

        self.setLayout(self.grid)

    def quit_app(self):
        global app
        app.quit()

    def open_file(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self)[0]
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
        QtWidgets.QMessageBox.information(self, "About " + program_name,
                                          program_name + ' ' + program_version + \
                                          "\n(C) 2010-2021 Jussi Pakkanen.\nThis program is available under the Gnu General Public License v3 or later.")

    def does_file_exist(self, fname):
        try:
            f = open(fname, 'r')
            return True
        except IOError:
            return False

    def is_image_file_valid(self, im):
        if im.isNull() or im.depth() != 1:
            return False
        return True

    def start_edit(self):
        global main_win, start_dialog
        fname = self.file_edit.text()
        output = self.output_edit.text()
        font_name = self.name_edit.text()
        image = QtGui.QImage(fname)
        if not self.is_image_file_valid(image):
            QtWidgets.QMessageBox.critical(self,
                                           "Error",
                                           "Selected file is not a 1 bit image.")
            return
        if image.hasAlphaChannel():
            QtWidgets.QMessageBox.critical(self,
                                           "Error",
                                           "The image has transparency, which will interfere with tracing. Remove alpha channel and try again.")
            return
        if self.does_file_exist(output):
            if QtWidgets.QMessageBox.critical(self,
                                              "File exists",
                                              "Output file %s already exists." % output,
                                              'Overwrite it', 'Select a different file') != 0:
                return
        start_dialog.hide()
        main_win = EditorWindow(image, font_name, output)
        main_win.show()

class EditorWindow(QtWidgets.QWidget):
    def __init__(self, image, font_name, sfd_file, parent=None):
        super().__init__()
        self.active_glyph = 0
        self.glyphlist = []
        self.font_name = font_name
        self.sfd_file = sfd_file

        self.set_nice_windowsize(image)

        self.setWindowTitle(program_name + ': ' + font_name)

        self.grid = QtWidgets.QGridLayout()
        self.area = SelectionArea(image, self)
        sa = QtWidgets.QScrollArea()
        sa.setWidget(self.area)
        self.grid.addWidget(sa, 0, 0, 1, 6)

        b = QtWidgets.QPushButton('Previous glyph')
        b.clicked.connect(self.previous_button)
        self.grid.addWidget(b, 1, 1, 1, 1)
        b = QtWidgets.QPushButton('Next glyph')
        b.clicked.connect(self.next_button)
        self.grid.addWidget(b, 1, 2, 1, 1)

        self.glyph_text = QtWidgets.QLabel('Glyph:')
        self.glyph_text.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.grid.addWidget(self.glyph_text, 1, 3, 1, 1)
        self.save = QtWidgets.QPushButton('Generate SFD file')
        self.save.clicked.connect(self.generate_sfd)
        self.grid.addWidget(self.save, 1, 5, 1, 1)

        self.combo = QtWidgets.QComboBox()
        self.build_glyph_combo()
        self.combo.activated.connect(self.glyph_set_changed)
        self.grid.addWidget(self.combo, 1, 0, 1, 1)

        self.zoomlevel = QtWidgets.QSpinBox()
        self.zoomlevel.setMaximum(5)
        self.zoomlevel.setMinimum(1)
        self.zoomlevel.setSingleStep(1)
        self.zoomlevel.setPrefix('Zoom level: ')
        self.zoomlevel.valueChanged.connect(self.zoom_changed)
        self.grid.addWidget(self.zoomlevel, 1, 4, 1, 1)

        self.setLayout(self.grid)

    def set_nice_windowsize(self, image):
        global app
        w = image.width()
        h = image.height()
        desk = app.desktop()
        rect = desk.screenGeometry(desk.primaryScreen())
        screen_width = rect.width()
        screen_height = rect.height()
        final_width = min(0.9*screen_width, w+50)
        final_height = min(0.9*screen_height, h+100)
        self.resize(final_width, final_height)

    def build_glyph_combo(self):
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

    def zoom_changed(self, value):
        self.area.set_zoom(value)
        self.area.repaint()

    def set_glyph_info(self):
        g = self.glyphlist[self.active_glyph]
        info_text = 'Glyph %d/%d: %s (%s)' % \
        (self.active_glyph+1, len(self.glyphlist), g.name, chr(g.codepoint))
        self.glyph_text.setText(info_text)

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
            QtWidgets.QMessageBox.critical(self, "Error", "No glyphs selected, can not generate sfd file.\n")
            return
        try:
            write_sfd(self.sfd_file, self.font_name, self.area.image, selected)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", "Sfd generation failed:\n" + str(e))
            return

        QtWidgets.QMessageBox.information(self, "Success", "Sfd file successfully generated.")

def start_program(arguments):
    global start_dialog, app
    app = QtWidgets.QApplication(arguments)
    if not i_haz_potrace():
        QtWidgets.QMessageBox.critical(None, program_name, "Potrace executable not in path, exiting.")
        sys.exit(127)
    if len(arguments) > 1:
        start_dialog = StartDialog(arguments[1])
    else:
        start_dialog = StartDialog()
    start_dialog.setWindowTitle(program_name)
    start_dialog.show()
    sys.exit(app.exec_())

def test_edwin():
    global app
    app = QtWidgets.QApplication(sys.argv)
    bob = EditorWindow(sys.argv[1], 'temporary_out.sfd', 'MyFont')
    bob.show()
    sys.exit(app.exec_())

def test_progress():
    import time
    app = QtWidgets.QApplication(sys.argv)
    prog = QtWidgets.QProgressDialog("Testing progressbar", '', 0, 100)
    prog.show()
    for i in range(100):
        time.sleep(0.1)
        prog.setValue(i)

if __name__ == "__main__":
    start_program(sys.argv)
    #test_progress()
    #test_edwin()
