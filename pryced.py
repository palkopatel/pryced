#!/usr/bin/env python2
# -*- coding: utf-8

# prices watcher (ozon.ru, read.ru)
# скрипт для наблюдения за указанными книгами на ozon.ru и read.ru

from parsing import *
from BeautifulSoup import BeautifulSoup
import datetime # для datetime.datetime.now()
import sqlite3
import sys
import urllib2

def connect_to_base():
    """ подключение к базе, создание таблиц
    
    """
    connect = sqlite3.connect('myozon.db')
    cursor = connect.cursor()
    try:
        cursor.execute('create table IF NOT EXISTS links \
        (id integer primary key AUTOINCREMENT, \
        urlname text, title text, author text, \
        serial text, desc1 text, desc2 text, \
        timestamp DEFAULT current_timestamp)')
        connect.commit()
    except sqlite3.Error, e:
        print 'Ошибка при создании таблицы:', e.args[0]
    try:
        cursor.execute('create table IF NOT EXISTS prices \
        (id integer primary key AUTOINCREMENT, \
        link int, price int, \
        timestamp DEFAULT current_timestamp)')
        connect.commit()
    except sqlite3.Error, e:
        print 'Ошибка при создании таблицы:', e.args[0]
    cursor.close()
    return connect

def load_link(connect, now_day, url_name, create_flag):
   """ загрузка новой книги в свою базу
   
   """
   try:
      if create_flag > 0:
         cursor = connect.cursor()
            # проверить нет ли уже такой ссылки в базе
         cursor.execute('select author, title from links where urlname like ?',\
                        ['%'+url_name+'%'])
         data = cursor.fetchall()
         cursor.close()
         if len(data) > 0:
            print U'Ссылка на "' + data[0][0] + U'. ' + data[0][1] + \
                  U'" уже существует в базе!'
            return 0;
      f = urllib2.urlopen(url_name) 
      datas = f.read()
      f.close()
      soup = BeautifulSoup(datas)
      if url_name.find(U'ozon.ru') > -1:
         (title, author, serial, desc1, desc2, price) = ozonru_parse_book(soup)
      elif url_name.find(U'read.ru') > -1: 
         (title, author, serial, desc1, desc2, price) = readru_parse_book(soup)
      else:
         return 0
      if create_flag > 0:
         try:
            cursor = connect.cursor()
            cursor.execute( 'insert into links \
               (urlname, title, author, serial, desc1, desc2) \
               values (?, ?, ?, ?, ?, ?)', \
               (url_name, title, author, serial, desc1, desc2) )
            cursor.close()
            connect.commit()
            print U'Ссылка на "' + author + U'. ' + title + U'" добавлена в базу.'
         except sqlite3.Error, e:
            print 'Ошибка при выполнении запроса:', e.args[0]
      return int(price)
   except Exception, e:
      print e
      return 0

def insert_new_price_into_db(connect, results):
   """ сохранение в свою базу цен для книг в списке results
   
   """
   cursor = connect.cursor()
      # сохранение текущих цен в базе
   for price in results:
      cursor.execute( 'insert into prices (timestamp, link, price) values (?, ?, ?)', price )
   cursor.close()
   connect.commit()
   print 'Цены обновлены.'

def load_new_price(connect, now_day, insert_mode):
   """ получение текущих цен для имеющихся книг
   "   сохранение цен в свою базу при insert_mode == 1
   
   """
   cursor = connect.cursor()
      # перебор книг в базе
   cursor.execute('select links.id, links.urlname, links.author || ", " || links.title \
                        , ifnull(min(prices.price),0)\
                        , ifnull(max(prices.price),0)\
                   from links \
                   left join prices on links.id = prices.link \
                   group by links.id, links.author, links.title \
                   order by links.author, links.title, links.urlname')
   rows = cursor.fetchall()
   results = []
   for row in rows:
      color_sym = ''
      if insert_mode == 1: # получение текущей цены с сайта
         price = load_link(connect, now_day, row[1], 0)
         if price != 0 :
            if price < int(row[3]): color_sym = U'\033[1;35m'
            elif price == int(row[3]): color_sym = '\033[1;36m'
      else: price = 0
         # сокращенное название сайта с подцветкой
      if row[1].find(U'ozon.ru') > -1:
         site = U'\033[1;46mozon.ru\033[1;m'
      elif row[1].find(U'read.ru') > -1: 
         site = U'\033[1;43mread.ru\033[1;m'
      else:
         site = 'none'
      print site + U': ' + row[2] + U';',\
            color_sym + U'сейчас: ' + str(price) + U'\033[1;m,',\
            U'минимум: ' + str(row[3]) + U',',\
            U'максимум: ' + str(row[4]) + U'; ' + row[1]
      if insert_mode == 1 and price != 0: 
         results.insert(0, (now_day, row[0], price) )
   cursor.close()
   if len(results) > 0:
      insert_new_price_into_db(connect, results)

def add_new_book(connect, now_day, url_name):
   """ добавление ссылки на книгу в базу
   
   """
   price = load_link(connect, now_day, url_name, 1)
      # загрузка прошла без осложнений
   if price > 0:
      results = []
      cursor = connect.cursor()
      cursor.execute('select id from links where urlname like ?', ['%'+url_name+'%'] )
      data = cursor.fetchall()
      cursor.close()
      results.insert(0, (now_day, data[0][0], price) )
      insert_new_price_into_db(connect, results)
      print sys.argv[2] + U': цена сейчас:', str(price)

def usage_message():
   """ сообщение о правильном использовании
   
   """
   print 'использование:',\
         sys.argv[0], '{-a <ссылка на книгу> |',\
          '-g | -s}\n\t-a <ссылка на книгу> - добавить книгу в базу',\
          '\n\t-g - получить текущие цены и сохранить их в базу'\
          '\n\t-s - получить цены, не сохраняя их в базу'

try:
       # значение даты для вставки в базу
   now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   connect = connect_to_base()
   if len(sys.argv) > 2:
      if sys.argv[1] == '-a': # добавление ссылки на книгу в базу
         add_new_book(connect, now_day, sys.argv[2])
   elif len(sys.argv) > 1 and (sys.argv[1] == '-g' or sys.argv[1] == '-s'): # добавление текущих цен в базу
      try:
         if sys.argv[1] == '-g': insert_mode = 1
         else: insert_mode = 0
         load_new_price(connect, now_day, insert_mode)
      except sqlite3.Error, e:
         print 'Ошибка при выполнении:', e.args[0]
   else:
      usage_message()
   connect.close()
except Exception, e:
   usage_message()
   print e

