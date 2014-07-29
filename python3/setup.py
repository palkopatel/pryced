#!/usr/bin/env python2
# -*- coding: utf-8

from distutils.core import setup
import py2exe
import matplotlib

setup(
   windows=['gpryced.py'],
   options={'py2exe': {"includes" : ["matplotlib.backends.backend_tkagg"]}},
   data_files=matplotlib.get_py2exe_datafiles()
)
