#!/usr/bin/env python3
# -*- coding: utf-8

import sys
try:
    from ctypes import windll
except:
    pass

# номера цветов текста
FG_BLACK     = 0x0000
FG_BLUE      = 0x0001
FG_GREEN     = 0x0002
FG_CYAN      = 0x0003
FG_RED       = 0x0004
FG_MAGENTA   = 0x0005
FG_YELLOW    = 0x0006
FG_GREY      = 0x0007
FG_INTENSITY = 0x0008 # жирность текста
# номера цветов фона
BG_BLACK     = 0x0000
BG_BLUE      = 0x0010
BG_GREEN     = 0x0020
BG_CYAN      = 0x0030
BG_RED       = 0x0040
BG_MAGENTA   = 0x0050
BG_YELLOW    = 0x0060
BG_GREY      = 0x0070
BG_INTENSITY = 0x0080 # жирность фона

try:
    handle = windll.kernel32.GetStdHandle(-11)
except:
    pass

def console_color(color):
   windll.kernel32.SetConsoleTextAttribute(handle, color)


if sys.platform.find(u'win') == -1:
   for i in range(31,48):
      print (u'\033[' + unicode(str(i)) + u'mtest' + unicode(str(i)) + u'\033[0m' +\
         u'\033[' + unicode(str(60+i)) + u'mtest' + unicode(str(60+i)) + u'\033[0m')
else:
   console_color(BG_BLACK)
   for i in range(0,7):
      console_color(i)
      sys.stdout.write(u'test')
      console_color(i|FG_INTENSITY)
      sys.stdout.write(u' itest')
      console_color(i<<4)
      sys.stdout.write(u' btest')
      console_color(BG_BLACK)
      console_color(i<<4|BG_INTENSITY)
      sys.stdout.write(u' bitest')
      console_color(FG_GREY|BG_BLACK)
      print (u' normal')

