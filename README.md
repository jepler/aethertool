# This is aethertool, a command-line tool for aether websites
Copyright (C) 2005-2021 Jeff Epler <jepler@unpythonic.net>

## REQUIREMENTS

 *  Python 3.x  to execute the scripts
 *  convert     to resize images
 *  pngcrush    to improve the compression of png images
 *  jpegtran    to improve the compression of jpeg images and perform lossless rotation of digital camera pictures when EXIF orientation data is available


## INSTALLATION

To do a single-user installation:
```
pip install .
```
This may require configuration of your $PATH.

Aethertool can also be used "in place" without installation.
    

## USAGE

For help with commandline options, use "aethertool.py -h".  For help on the
configuration syntax, use "aethertool.py -c help".


# BUGS

Aethertool assumes that your browser is called "firefox"; it should use
the webbrowser module instead

Aethertool assumes the command used to invoke the editor doesn't exit
until the user is done editing the file.  This can cause problems if the
editor naturally starts in the background.

If the user does a 'write and exit' sequence, the file the browser loads
to submit page changes may be removed too early, and the last edit lost.


# COPYRIGHT

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License version 3 as published by the Free
Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
