#!/usr/bin/env python
#    This is a component of aethertool, a command-line interface to aether
#    Copyright 2005 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import getpass, urllib2, ClientForm, tempfile, os, time, webbrowser, sys
import getopt, cgi, re, disorient
import shutil, atexit
from sys import argv

EDITOR = os.environ.get("EDITOR", "vim")

thumb_geometry = "300x300"
config = {}
default_config = 'default'
browser_wait = 5
def add_config(name, root, password=None, thumb_geometry=None):
    config[name] = (root, password, thumb_geometry)

def set_default(name):
    global default_config
    default_config = name

def load_config(config):
    global AETHER_TOP, PASS, thumb_geometry
    #print "load_config", repr(config)
    AETHER_TOP = config[0]
    PASS = config[1] or getpass.getpass()
    thumb_geometry = config[2] or thumb_geometry

rcfile = os.path.join(os.environ.get('HOME', ''), ".aetherrc")
if os.path.exists(rcfile): execfile(rcfile)
else:
    print ("The configuration file %r does not exist.\n"
           "aethertool cannot run without it." % rcfile)
    raise SystemExit

config_name = os.path.splitext(os.path.split(sys.argv[0])[1])[0]
if len(config) == 1: default_config = config.keys()[0]
if not config.has_key(config_name): config_name = default_config

def quote_paranoid(text):
    """ Convert utf-8 string to sequence of lower case English characters. """

    text = text.encode('utf-8')

    result = ''
    for char in text:
        result += chr(ord('a') + ord(char)/16) +\
                  chr(ord('a') + ord(char)%16)

    return result

def webbrowser_open(u):
    os.spawnvp(os.P_NOWAIT, "firefox", ["firefox", u])
    time.sleep(browser_wait)

def get_edit_form(page):
    url = AETHER_TOP + "?action=edit&password=%s&name=%s" % (PASS, page)
    forms = ClientForm.ParseResponse(urllib2.urlopen(url))
    for f in forms:
        try:
            action = f.get_value("action")
        except ClientForm.ControlNotFoundError:
            continue
        if action == "edit":
            return f
    print "Required form not found.  AETHER_TOP or password may be incorrect."

def get_current_text(page):
    f = get_edit_form(page)
    return f.get_value("text")

def save_text(page, newtext):
    f = get_edit_form(page)
    f['text'] = newtext
    return f.click("save")

def preview_text(page, newtext):
    return """<HTML><BODY onload="document.forms[0].submit()"
    <DIV style="display: none">
    <FORM method=post accept-charset=\"utf-8\" action=\"%s\">
        <input type=hidden name=action value=edit>
        <input type=hidden name=password value=\"%s\">
        <input name=newname value=\"%s\">
        <input name=name value=\"%s\">
        <input name=hasnewname value=yes>
        <textarea name=text>%s</textarea>
        <input type=submit name=preview>
    </form>
    </DIV>
    Submitting updated text...
    </body>""" % (
    cgi.escape(AETHER_TOP, True),
    cgi.escape(PASS, True),
    cgi.escape(page, True),
    cgi.escape(page, True),
    cgi.escape(newtext, True))

def upload_file(page, local, remote, quiet=0):
#    if not quiet:
#        if os.path.basename(local) == remote:
#            print "uploading %s on page %s" % (remote, page)
#        else:
#            print "uploading %s as %s on page %s" % (local, remote, page)
    qPASS = quote_paranoid(PASS)
    qpage = quote_paranoid(page)
    url = AETHER_TOP + "?action=attachments&password=%s&name=%s" % (qPASS,qpage)
    forms = ClientForm.ParseResponse(urllib2.urlopen(url))
    f = forms[0]
    f.add_file(open(local, "rb"), filename=remote, name="file")
    u = f.click("attach")
    urllib2.urlopen(u)
    if not quiet:
        print "Uploaded file is:"
        print "   [page %s] [file %s]" % (page, remote)
        print "   " + AETHER_TOP + "-files/%s/%s" % (page, remote)

def put_page(page, filename):
    u = save_text(page, open(filename).read())
    urllib2.urlopen(u)

def edit_page(page):
    t = get_current_text(page)

    name = os.path.join(tempdir, page.replace("/", "_") + ".ae")
    fd = open(name, "w")
    fd.write(t)
    fd.close()

    hname = os.path.join(tempdir, "submit.html")

    pid = os.spawnvp(os.P_NOWAIT, EDITOR, [EDITOR, name])

    ost = os.stat(name)
    while 1:
        nst = os.stat(name)
        if ost.st_mtime != nst.st_mtime:
            ost = nst
            new_text = open(name).read()
            u = preview_text(page, new_text)
            hfd = open(hname, "w")
            hfd.write(u)
            hfd.close()
            webbrowser_open(hname) 
        sts = os.waitpid(0, os.P_NOWAIT)
        if sts[0] == pid:
            break
        time.sleep(1)
    os.unlink(name)

def isimage(f):
    ext = os.path.splitext(f)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
        return True
    return False

def get_orient(f):
    return disorient.exif_orientation(f) or 1

def optimize(f):
    ext = os.path.splitext(f)[1].lower()
    t = os.path.join(tempdir, "optimized" + ext)
    if ext in ['.jpg', '.jpeg']:
        command = ['jpegtran', '-optimize', '-progressive',
            '-copy', 'all', '-outfile', t]
        o = get_orient(f)
        if o == 8:
            command.extend(['-rotate', '270'])
        elif o == 6:
            command.extend(['-rotate', '90'])
        command.append(f)
        #print "Optimize: %s" % (" ".join(command))
        os.spawnvp(os.P_WAIT, command[0], command)
        if o in (6, 8): disorient.clear_exif_orientation(t)
        return t
    if ext in ['.png']:
        #print "Optimize: pngcrush"
        os.spawnvp(os.P_WAIT, "pngcrush", ["pngcrush", "-q", "-reduce", f, t])
        return t
    # XXX convert gif to png?
    return f

tempdir = tempfile.mkdtemp()
atexit.register(shutil.rmtree, tempdir)

def usage(exitcode=1):
    print """\
Usage:
    %(name)s pagename
        Edit the page 'pagename'.  Use '' (the empty page) to edit the front
        page.  To preview the changes in your browser, save the file.
        Use the browser's save button in the browser to save the changes.
    %(name)s -p pagename < contents
        Put new contents to 'pagename' from standard input.
    %(name)s -n [-k suffix] blogpage
        Create a new blog entry on 'blogpage', optonally with 'suffix' added
        to the name of the created page.
    %(name)s -u [-t] [-g WxH] pagename file[=localfile] file...
        Upload files to 'pagename'.  Create thumbnails unless -t is specified.
        Use -g to specify the maximum thumbnail size, currently %(thumbsize)s.
    %(name)s -c configname [other usage from above]
        Use the configuration 'configname' instead of the default

The configuration file ~/.aetherrc looks like this:
    add_config('configname', 'http://www.example.com/index.cgi', 'password')
    set_default('configname')
The configuration is guessed from the script's name, otherwise the value
given by set_default is used.  If only one call to add_configuration is
present, then that configuration is the default.\
""" % {'name': os.path.basename(sys.argv[0]), 'thumbsize': thumb_geometry}
    raise SystemExit, exitcode
try:
    opts, args = getopt.getopt(argv[1:], "+tnuk:g:c:h?")
except getopt.GetoptError, detail:
    print >> sys.stderr, "%s:" % os.path.basename(sys.argv[0]), detail
    usage()
do_new_entry = do_upload = False
do_thumbnail = True
for k, v in opts:
    if k == "-c": config_name = v
    if k == "-p": do_put = not do_put
    if k == "-n": do_new_entry = not do_new_entry
    if k == "-u": do_upload = not do_upload
    if k == "-t": do_thumbnail = not do_thumbnail
    if k == "-k": suffix = "-" + v.replace(" ", "-")
    if k == "-g": thumb_geometry = v
    if k == "-?" or k == "-h": usage(0)


load_config(config[config_name])

if do_upload:
    page = args[0]
    for filename in args[1:]:
        if "=" in filename:
            remote, local = filename.split("=", 1)
        else:
            remote = os.path.basename(filename)
	    if not re.search('[a-z]', remote): remote = remote.lower()
            local = filename
	if isimage(remote):
	    local = optimize(local)
        upload_file(page, local, remote)
        if do_thumbnail and isimage(remote):
            base, ext = os.path.splitext(remote)
            thumb = base + "-small" + ext
            localthumb = os.path.join(tempdir, "thumb" + ext)
            print "Creating thumbnail for", remote
            os.spawnvp(os.P_WAIT, "convert", 
                ["convert", "-geometry", thumb_geometry, local, localthumb])
            localthumb = optimize(localthumb)
            upload_file(page, localthumb, thumb, True)
else:
    if do_new_entry:
        if args:
            page = args[0] + "/0" + str(int(time.time())) + suffix
        else:
            page = "0" + str(int(time.time())) + suffix
    else:
        if args:
            page = args[0]
        else:
            page = "sandbox"
    page = page.strip("/")
    edit_page(page)

# vim:sw=4:sts=4:et
