#!/usr/bin/python
# Copyright(c) 2011 Jonathan D. Lettvin, All Rights Reserved.
# Author: jlettvin@gmail.com (Jonathan D. Lettvin)
###############################################################################
__docformat__ = 'restructuredtext'
__version__ = '$Id: browseISO.py 1 2011-03-11 10:30 Jonathan D. Lettvin $'
"""
browsISO.py implements a browser for ISO files as if they were disks.
Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

browseISO.py uses gtk.FileChooserDialog to select an ISO file from a folder,
mounts the ISO file, and browses the contents with a preferred browser.
When browser window closes, ISO file is unmounted and resources are released.
Control and source information is passed around in a dictionary.

Tested on linux 9.10 with gnome desktop and python 2.6.4.

Requirements:
  sudo apt-get install gtk pygtk
  sudo apt-get install fuseiso
  sudo adduser <your login name> fuse

Warning and Error message examples:
  Xlib:  extension "RANDR" missing on display ":0.0".
  ** (process:2683): WARNING **: Couldn't change nice value of process.
  fusermount: entry for /home/$loginname/.browseISO not found in /etc/mtab
  Child returned 1
"""

__date__       = "20110311"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"

# TODO Fix warning and error messages.

###############################################################################
try:
  lib='sys'; import sys
  lib='os'; import os
  lib='pygtk'; import pygtk
  pygtk.require('2.0')
  lib='gtk'; import gtk
  lib='subprocess'; import subprocess
  if gtk.pygtk_version < (2,3,90):
     raise "PyGtk 2.3.90 or later required for this script."
  lib='subprocess.call'; from subprocess import call
  lib='optparse.OptionParser'; from optparse import OptionParser
except Exception, e: print e, "\nexcept:", sys.exc_info()[0], sys.exc_info()[1]
except: print "Unable to import", lib; sys.exit(1)

###############################################################################
class exploreISO(object):
  def __init__(self, dictionary):
    """__init__: Acquire run-time information from the caller."""
    self.dictionary = dictionary
    (
        self.mount,
        self.directory,
        self.browser,
        self.thumb,
        self.isoname,
        self.verbose,
        self.cleanup ) = (
        self.dictionary['mount'],
        self.dictionary['directory'],
        self.dictionary['browser'],
        self.dictionary['thumb'],
        self.dictionary['visited'],
        self.dictionary['verbose'],
        self.dictionary['cleanup']
        )

  def __del__(self):
    """__del__: unmount mounted ISO, and conditional thumbnail removal."""
    if os.path.ismount(self.mount):
      self.run('fusermount -u %s' % (self.mount))
    """Prevent accidental global clobbering by detecting substring."""
    legitimate = 0 < self.thumb.find('.thumbnails/normal')
    if legitimate and self.cleanup and os.path.isdir(self.thumb):
      self.run('rm -f %s/*' % self.thumb)
    assert not os.path.ismount(self.mount), (
        '%s still in use.' % (self.mount))

  def run(self, command):
    """Generic service method to run external commands in a shell."""
    try:
      if self.verbose: print command
      retcode = call(command, shell=True)
      if retcode < 0:
        print >>sys.stderr, "Child was terminated by signal", -retcode
      elif retcode > 0:
        print >>sys.stderr, "Child returned", retcode
    except OSError, e:
      print >>sys.stderr, "Execution failed:", e

  def __call__(self):
    """__call__: set up ISO file choice dialog, and call browser on choice."""
    dialog = gtk.FileChooserDialog(
        "Search for ISO file archive", None, gtk.FILE_CHOOSER_ACTION_OPEN,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)

    """Tell dialog to find all files in the ISO file directory."""
    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    """Remember this directory, and set the ISO file containing directory."""
    home = dialog.get_current_folder_uri()
    dialog.set_current_folder_uri(self.directory)
    """Remember the last selected ISO file."""
    if self.isoname: dialog.select_filename(self.isoname)
    if self.verbose:
      print dialog.get_current_folder_uri(), 'is the current directory.'
    """Activate chooser, and get response."""
    response = dialog.run()
    iso = ''
    if response == gtk.RESPONSE_OK:
      iso = dialog.get_filename()
      if self.verbose:
        print iso, 'selected'
    elif response == gtk.RESPONSE_CANCEL:
      if self.verbose:
        print 'Closed, no files selected'

    if iso and iso[-4:] != '.iso':
      if self.verbose:
        print iso, 'is illegal.'
      iso = ''

    """Return to the remembered directory."""
    dialog.set_current_folder_uri(home)
    """Make window disappear by hiding, and waiting for gtk events to flush."""
    dialog.hide()
    while gtk.events_pending(): gtk.main_iteration()
    """Cleanup to avoid memory leaks."""
    dialog.destroy()

    if iso:
      self.dictionary['visited'] = self.isoname = iso
      """Make default mount point off user's home dir."""
      if not os.path.exists(self.mount): os.mkdir(self.mount)
      assert os.path.isdir(self.mount), (
          '%s is not a directory.  Cannot mount' % (self.mount))
      assert not os.path.ismount(self.mount), (
          '%s already in use.' % (self.mount))
      """Mount the chosen ISO, and browse."""
      self.run('fuseiso %s %s' % (self.isoname, self.mount))
      self.run('%s %s' % (self.browser, self.mount))

      """Tell caller an ISO was chosen."""
      return True, self.isoname
    return False, self.isoname

###############################################################################
class Requirements:
  """Requirements enables testing the system for presence of applications."""
  """This simple approach is probably naive."""
  def __init__(self):
    pass

  def __call__(self, apps):
    for app in apps:
      command = ['which', app]
      p = subprocess.Popen(command, stdout=subprocess.PIPE)
      name = p.communicate()[0]
      assert len(name), ('Missing app (try sudo apt-get install %s)' % app)

# MAIN ########################################################################
if __name__ == '__main__':
    """browseISO.py:__main__"""
    try:
      browserList = ['nautilus', 'google-chrome', 'thunar']
      home = os.getenv('HOME')
      homeMount = home + '/.browseISO'
      homeThumb = home + '/.thumbnails/normal'

      """Handle command-line parameters"""
      parser = OptionParser(
        usage ="""%prog [-v] [{other options}]""",
        version ="%prog 0.01",
        description ="Browse files in ISO files"
      )
      parser.add_option(
          "-b", "--browser", type=str, default='thunar',
          help=str(browserList))
      parser.add_option(
          "-c", "--cleanup", action="store_true", default=False,
          help="remove thumbnails")
      parser.add_option(
          "-m", "--mount", type=str, default=homeMount,
          help="iso mount point (usually ~/.browseISO).")
      parser.add_option(
          "-v", "--verbose", action="store_true", default=False,
          help="trace activity")
      (opts,args) = parser.parse_args()

      if not args: args = ['.']
      musthave = Requirements()
      musthave(('fuseiso', 'fusermount'))
      assert opts.browser in browserList, (
          '%s: Unknown browser.' % (opts.browser))

      prefix = ("http://", "file://")
      for arg in args:
        if arg[:6] in prefix:
          directory = arg
        else:
          directory = 'file://' + os.path.abspath(arg)
        isoname = ''
        while True:
          dictionary = {
              'browser': opts.browser,
              'cleanup': opts.cleanup,
              'directory': directory,
              'mount': opts.mount,
              'thumb': homeThumb,
              'verbose': opts.verbose,
              'visited': isoname
              }
          if opts.verbose: print dictionary
          explore = exploreISO(dictionary)
          running, isoname = explore()
          del explore
          if not running: break
    except Exception, e:
        print e, "\nexception:", sys.exc_info()[0], sys.exc_info()[1]
    except: pass
###############################################################################

