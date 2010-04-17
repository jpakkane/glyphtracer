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

sfd_header = """SplineFontDB: 3.0
FontName: %s
FullName: %s
FamilyName: %s
Weight: Medium
Copyright: Originally scanned fith FontHelper
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
BeginChars: 65536 2

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
