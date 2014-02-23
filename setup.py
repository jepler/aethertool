#!/usr/bin/python

from distutils.core import setup

import os
def require_module(m):
    try:
        __import__(m)
    except ImportError:
        print "Warning: The required module %r is not available." % m
        print "The software will probably not work without it."
        return False

def require_program(s):
    for el in os.environ['PATH'].split(os.pathsep):
        j = os.path.join(el, s)
        if os.access(j, os.F_OK | os.X_OK):
            return True
    print "Warning: The required external program %r is not available." % s
    print "The software will probably not work without it."
    return False

for m in ("Image",):
    require_module(m)

for p in ("pngcrush", "jpegtran"):
    require_program(p)

setup(name="aethertool", version="0.7",
    author="Jeff Epler", author_email = "jepler@unpythonic.net",
    py_modules=['disorient'],
    scripts=['aethertool'],
    url="http://emergent.unpy.net/software/aethertool/",
    license="GPL",
)
# vim:sw=4:sts=4:et
