#   This is a component of aethertool, a command-line interface to aether
#   Copyright 2005-2021 Jeff Epler <jepler@unpythonic.net>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3 as published by
#   the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#   more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

# This program is a new implementation of the method described at
#  http://sylvana.net/jpegcrop/exif_orientation.html
# and in the "jpegexiforient.c" source code.

EXIF_MAGIC = "\xff\xd8\xff\xe1"  #  JPEG SOI + Exif APP1
EXIF_MAGIC_2 = "Exif\0\0"

import struct


def read_2(f):
    return ord(f.read(1)) * 256 + ord(f.read(1))


def exif_orientation(f, set=None):
    if set:
        f = open(f, "rb+")
    else:
        f = open(f, "rb")

    buf = f.read(4)
    # print `buf`
    if buf != EXIF_MAGIC:
        return

    length = read_2(f)
    # print `length`
    if length <= 20:
        return

    buf = f.read(6)
    # print `buf`
    if buf != EXIF_MAGIC_2:
        return

    buf = f.read(length - 8)
    # print `buf[:2]`
    if buf[:2] == "II":
        is_motorola, order = 0, "<"
    elif buf[:2] == "MM":
        is_motorola, order = 1, ">"
    else:
        return

    decode_4 = lambda i: struct.unpack(order + "I", buf[i : i + 4])[0]
    decode_2 = lambda i: struct.unpack(order + "H", buf[i : i + 2])[0]
    # print "here", repr(buf[2:4])
    if is_motorola:
        if buf[2:4] != "\0\x2a":
            return
    else:
        if buf[2:4] != "\x2a\0":
            return

    offset = decode_4(4)
    # print offset
    if offset > length - 2:
        return

    number_of_tags = decode_2(offset)
    offset += 2
    # print "here", offset, length

    while 1:
        if offset > length - 12:
            return
        tagnum = decode_2(offset)
        # print "loop", offset, length, tagnum
        if tagnum == 0x112:
            break
        number_of_tags -= 1
        if not number_of_tags:
            return 0
        offset += 12

    if not set:
        # print repr(buf[offset:offset+12])
        return decode_2(offset + 8)
    else:
        if is_motorola:
            new_tag = "\0\3" "\0\0\0\1" "\0" + chr(set) + "\0\0"
        else:
            new_tag = "\3\0" "\1\0\0\0" + chr(set) + "\0" "\0\0"
    f.seek(4 + 2 + 6 + 2 + offset)
    f.write(new_tag)
    f.seek(0, 2)
    # print "replaced"


def clear_exif_orientation(x):
    return exif_orientation(x, 1)


descr = {
    1: "Normal",
    2: "Mirrored left-to-right",
    3: "Rotated 180 degrees",
    4: "Mirrored top-to-bottom",
    5: "Mirrored along top-left diagonal",
    6: "Rotated 90 degrees",
    7: "Mirrored along top-right diagonal",
    8: "Rotated 270 degrees",
}

if __name__ == "__main__":
    import sys

    if sys.argv[1] == "-c":
        clear_exif_orientation(sys.argv[2])
        print("Orientation cleared")
    else:
        print(descr.get(exif_orientation(sys.argv[1]), "Invalid orientation"))
# vim:sw=4:sts=4:et
