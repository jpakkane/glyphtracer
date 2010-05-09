GLyphtracer
(C) 2010 Jussi Pakkanen
https://launchpad.net/glyphtracer


Overview

Glyphtracer takes an image that contains pictures of several letters.
It recognizes all them and lets the user tag each letter
to a Unicode code point. It then converts the images to vector form
and writes them to a FontForge's data format. The font can then
be finalized with FontForge.


Dependencies

Glyphtracer requires PyQt4 and Potrace, which is an image vectorizer.

It has been only tested on Linux. It might work on OSX or Windows.
It might not.


Usage tips

Glyphtracer only processes 1 bit images, but they can be in
any format understood by Qt.

The letter recognition is based on white space. Thus every row
must be separated from other rows by a continuous horizontal strip
of white. If this is not the case (because, for example, your image
is tilted), detection will fail. Similarly letters on a single row
have to be separated by vertical white space. Just give your letters 
lots of "room" on all sides and everything will work.


Contributors

The following people have contributed to this project.

Toshio Ernie Kuratomi
