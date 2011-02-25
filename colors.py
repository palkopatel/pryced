#!/usr/bin/env python2
# -*- coding: utf-8

for i in range(31,48):
  print U'\033[' + str(i) + 'mtest' + str(i) + '\033[0m' +\
  '\033[' + str(60+i) + 'mtest' + str(60+i) + '\033[0m'