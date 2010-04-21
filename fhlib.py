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

# Fonthelper library files and stuff

import os, subprocess, tempfile

# These are read only lists that define different glyph groups.
# In the future they may be parsed from a conf file.
lowercase_list = [('a', 97), ('b', 98), ('c', 99), ('d', 100), ('e', 101), ('f', 102),\
                  ('g', 103), ('h', 104), ('i', 105), ('j', 106), ('k', 107), ('l', 108),\
                  ('m', 109), ('n', 110), ('o', 111), ('p', 112), ('q', 113), ('r', 114),\
                  ('s', 115), ('t', 116), ('u', 117), ('v', 118), ('w', 119), ('x', 120),\
                  ('y', 121), ('z', 122)]
number_list = [('zero', 48), ('one', 49), ('two', 50), ('three', 51), ('four', 52), ('five', 52),\
               ('six', 53), ('seven', 54), ('eight', 55), ('nine', 56)]

glyph_groups = [('lowercase', lowercase_list), ('numbers', number_list)]

sfd_header = """SplineFontDB: 3.0
FontName: %s
FullName: %s
FamilyName: %s
Weight: Medium
Copyright: Originally scanned with FontHelper
UComments: "No comments" 
Version: 001.000
ItalicAngle: 0
UnderlinePosition: -100
UnderlineWidth: 50
Ascent: 800
Descent: 200
LayerCount: 2
Layer: 0 0 "Back"  1
Layer: 1 0 "Fore"  0
NeedsXUIDChange: 1
XUID: [1021 397 1238052781 15881202]
OS2Version: 0
OS2_WeightWidthSlopeOnly: 0
OS2_UseTypoMetrics: 1
CreationTime: 1270926697
ModificationTime: 1271540628
OS2TypoAscent: 0
OS2TypoAOffset: 1
OS2TypoDescent: 0
OS2TypoDOffset: 1
OS2TypoLinegap: 0
OS2WinAscent: 0
OS2WinAOffset: 1
OS2WinDescent: 0
OS2WinDOffset: 1
HheadAscent: 0
HheadAOffset: 1
HheadDescent: 0
HheadDOffset: 1
OS2Vendor: 'FoHe'
DEI: 91125
Encoding: UnicodeBmp
UnicodeInterp: none
NameList: Adobe Glyph List
DisplaySize: -36
AntiAlias: 1
FitToEm: 1
WinInfo: 57 19 19
BeginChars: 65536 %d

"""

sfd_footer = """EndChars
EndSplineFont
"""

letter_header = """StartChar: %s
Encoding: %d %d %d
Width: %d
VWidth: 0
Flags: HW
LayerCount: 2
Fore
SplineSet
"""

letter_footer = """EndSplineSet
EndChar
"""


class LetterBox():
    def __init__(self, rectangle):
        self.r = rectangle
        self.taken = False
    
    def contains(self, x, y):
        return self.r.contains(x, y)

class GlyphInfo():
    def __init__(self, name, codepoint):
        self.name = name
        self.codepoint = codepoint
        self.box = None

def data_to_glyphinfo(data):
    return GlyphInfo(data[0], data[1])


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

def crop_and_trace(image, box):
    tfile = tempfile.NamedTemporaryFile(suffix='.pgm')
    tempname = tfile.name
    tfile.close()
    cropped = image.copy(box)
    if not cropped.save(tempname):
        raise RuntimeError('Could not save cropped image')
    points = potrace_image(tempname)
    os.unlink(tempname)
    return points
    

def convert_points(pointlist):
    pointlist = to_absolute(pointlist)
    return flip_curve(pointlist)

def to_absolute(pointlist):
    starting_point = pointlist[0]
    assert(len(starting_point) == 2)
    converted = [starting_point]
    current_point = starting_point
    for p in pointlist[1:]:
        if len(p) == 2:
            newp = [current_point[0] + p[0], current_point[1] + p[1]]
        elif len(p) == 6:
            newp = [0]*6
            newp[0] = current_point[0] + p[0]
            newp[1] = current_point[1] + p[1]
            newp[2] = current_point[0] + p[2]
            newp[3] = current_point[1] + p[3]
            newp[4] = current_point[0] + p[4]
            newp[5] = current_point[1] + p[5]
        else:
            raise RuntimeError('Unknown point size error.')
        converted.append(newp)
        current_point = [newp[-2], newp[-1]]
    return converted

def flip_curve(curve):
    first = curve[0]
    last = curve[-1]
    assert(first[0] == last[-2])
    assert(first[1] == last[-1])
    flipped = [first]
    for i in range(len(curve))[:0:-1]:
        curp = curve[i]
        if i == 0:
            prevp = first
        else:
            prevp = curve[i-1]
        if len(curp) == 6:
            newp = curp[2:4] + curp[0:2] + prevp[-2:]
        elif len(curp) == 2:
            newp = prevp[-2:]
        flipped.append(newp)
    return flipped

def process_glyph(ofile, image, glyph):
    width = 672
    location3 = 0
    ofile.write(letter_header % (glyph.name, glyph.codepoint, glyph.codepoint, location3, width))
    points = crop_and_trace(image, glyph.box.r)
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
                raise RuntimeError('Incorrect amount of points: %d' % len(point))
    ofile.write(letter_footer)
    

def write_sfd(ofilename, image, glyphs):
    ofile = file(ofilename, 'w')
    font_name = 'dummy'
    full_name = 'dummy'
    family_name = 'dummy'
    num_letters = len(glyphs)
    ofile.write(sfd_header % (font_name, full_name, family_name, num_letters))

    for glyph in glyphs:
        process_glyph(ofile, image, glyph)
    
    ofile.write(sfd_footer)
