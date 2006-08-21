README for Olive
================

What is Olive?
--------------

Olive is a GTK-based graphical frontend for Bazaar Version Control System
(http://bazaar-vcs.org/). It aims to be a user-friendly tool for those who are
not familiar with command line interfaces. Olive is written in Python, so it
can be run under different platforms (Linux and Windows are known to work).

Requirements
------------

 - Python (>= 2.4)
 - GTK (>= 2.8)
 - PyGTK (>= 2.8)
 - Bazaar (>= 0.8.2)

Install on Linux
----------------
 
You just need to run the bundled setup script like this:
 
 # ./setup.py install

If you'd like to install to a different folder, you can:

 $ ./setup.py install --prefix /path/to/the/folder

Be sure to adjust the PATH values if you install to a custom location!

A desktop menu entry is shipped with the application, you'll find Olive in the
Programming category.

Install on Windows
------------------

You can download the dependencies from the following locations:

 - Python: http://www.python.org/download/releases/2.4.3/
 - GTK: http://gladewin32.sourceforge.net/
 - PyGTK: http://www.mapr.ucl.ac.be/~gustin/win32_ports/pygtk.html (pycairo too)
 - Bazaar: http://bazaar-vcs.org/WindowsDownloads (Python-based should be okay)

As an Administrator, you can install Olive with the standard command:

 > c:\Python24\python.exe setup.py install

You can run Olive with this command:

 > c:\Python24\python.exe c:\Python\Scripts\olive-gtk

Reporting bugs
--------------

The official bug tracker of Olive can be found in the Launchpad system. The list
of the opened bugs are here:

 https://launchpad.net/products/olive/+bugs

If you found a bug in Olive, please report it here:

 https://launchpad.net/products/olive/+filebug

Please run olive-gtk from the command line, so you can copy-paste the traceback
of the exceptions.
