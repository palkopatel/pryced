#!/usr/bin/env python2
# -*- coding: utf-8

# разбор html-кода в поисках характеристик книги

from BeautifulSoup import BeautifulSoup
import urllib2

def ozonru_parse_book(soup):
   """ разбор страницы с ozon.ru
   
   """
   fields = soup.find('title').string.split(' | ')
   desc2 = fields[0]
   title = fields[1]
   author_raw = fields[2]
      # фамилия автора идет в конце (везде в коде страницы),
      # поэтому надо ее переставить в начало для "хорошей" сортировки
   author_list = author_raw.split(' ')
   author = ''
   try:
         # перестановка в списке
      author_list.insert(0, author_list.pop(len(author_list)-1))
         # перенос содержимого списка в строку
      first = 1
      for name_part in author_list:
         if first == 0: author += ' '
         else: first = 0
         author += name_part
   except:
      pass
   try:
      serial = fields[3] 
      desc1 = fields[4]
   except:
      serial = ''
      try:
         desc1 = fields[3]
      except:
         desc1 = ''
   price = soup.find('big').string
   if price == None: price = '0'
   return (title, author, serial, desc1, desc2, price)

def readru_parse_book(soup):
   """ разбор страницы с read.ru
   
   """
   title = soup.find('h1').string
      # найти таблицу с атрибутом id равным book_fields
   table = soup.find('table', {'id':'book_fields'})
   serial = ''
   for row in table.findAll('tr'): # перебрать строки
      for cell in row.findAll('td', {'class':'f'}): # перебрать ячейки в строке
         if cell.string.find(U'Автор') > -1: # найти ячейку с именем автора
            author = row.find('a').string
         if cell.string.find(U'Серия') > -1: # найти ячейку с названием серии
            serial = row.find('a').string
   price_tag = soup.find('span', {'class':'price '})
   pos_end = price_tag.renderContents().find('<')
   price = price_tag.renderContents()[0:pos_end]
   return (title, author, serial, '', '', price)

