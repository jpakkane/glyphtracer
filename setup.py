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

from distutils.core import setup
import gtlib

setup(name = gtlib.program_name.lower(),
      version = gtlib.program_version,
      description='A tool for vectorising letters',
      author='Jussi Pakkanen',
      author_email='jpakkane gmail',
      url='https://launchpad.net/glyphtracer',
      py_modules = ['gtlib'],
      scripts = ['glyphtracer'],
      classifiers = ['License :: OSI Approved :: GNU General Public License (GPL)',
                     'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
                     'Topic :: Text Processing :: Fonts',
                     'Environment :: X11 Applications :: Qt',
                     'Intended Audience :: End Users/Desktop',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 2',
                     ]
      )
