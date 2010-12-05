#!/usr/bin/env python2
# -*- coding: utf-8

# ozon.ru prices watcher 
# скрипт для наблюдения за указанными книгами на ozon.ru

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
        print U'Ошибка при создании таблицы:', e.args[0]
    try:
        cursor.execute('create table IF NOT EXISTS prices \
        (id integer primary key AUTOINCREMENT, \
        link int, price int, \
        timestamp DEFAULT current_timestamp)')
        connect.commit()
    except sqlite3.Error, e:
        print U'Ошибка при создании таблицы:', e.args[0]
    cursor.close()
    return connect

def load_link(connect, now_day, url_name, create_flag):
   """ загрузка новой книги в свою базу
   
   """
   try:
      if create_flag > 0:
         cursor = connect.cursor()
            # проверить нет ли уже такой ссылки в базе
         cursor.execute('select author, title from links where urlname like ?', ['%'+url_name+'%'])
         data = cursor.fetchall()
         cursor.close()
         if len(data) > 0:
            print U'Ссылка на "' + data[0][0] + '. ' + data[0][1] + U'" уже существует в базе!'
            return '';
      f = urllib2.urlopen(url_name) 
      datas = f.read()
      f.close()
      soup = BeautifulSoup(datas)
      if create_flag > 0:
         try:
            fields = soup.find('title').string.split(' | ')
            desc2 = fields[0]
            title = fields[1]
            author = fields[2]
            try:
               serial = fields[3] 
               desc1 = fields[4]
            except:
               serial = ''
               try:
                  desc1 = fields[3]
               except:
                  desc1 = ''
            cursor = connect.cursor()
            cursor.execute( 'insert into links (urlname, title, author, serial, desc1, desc2) values (?, ?, ?, ?, ?, ?)', 
                            (url_name, title, author, serial, desc1, desc2) )
            cursor.close()
            connect.commit()
            print U'Ссылка на "' + author + U'. ' + title + U'" добавлена в базу.'
         except sqlite3.Error, e:
            print U'Ошибка при выполнении запроса:', e.args[0]
      return soup.find('big').string
   except Exception, e:
      print e
      return ''

def insert_new_price_into_db(connect, results):
   """ сохранение в свою базу цен для книг в списке results
   
   """
   cursor = connect.cursor()
      # сохранение текущих цен в базе
   for price in results:
      cursor.execute( 'insert into prices (timestamp, link, price) values (?, ?, ?)', price )
   cursor.close()
   connect.commit()
   print U'Цены обновлены.'

def load_new_price(connect, now_day, insert_mode):
   """ получение текущих цен для имеющихся книг
   "   сохранение цен в свою базу при insert_mode == 1
   
   """
   cursor = connect.cursor()
      # перебор книг в базе
   cursor.execute('select links.id, links.urlname, links.author || ", " || links.title \
                        , min(prices.price), max(prices.price)\
                   from links \
                   left join prices on links.id = prices.link \
                   group by links.id, links.author, links.title \
                   order by links.author, links.title')
   rows = cursor.fetchall()
   results = []
   for row in rows:
      color_sym = U''
      if insert_mode == 1: # получение текущей цены с сайта
         price = load_link(connect, now_day, row[1], 0)
         if int(price) <= int(row[3]): color_sym = U'\033[1;35m'
      else: price = 0
      print row[1], U':', row[2], U':',\
            color_sym, U'сейчас: ' + str(price), U'\033[1;m,',\
            U'минимум: ' + str(row[3]), U',',\
            U'максимум: ' + str(row[4])
      results.insert(0, (now_day, row[0], price) )
   cursor.close()
   if insert_mode == 1: insert_new_price_into_db(connect, results)

def add_new_book(connect, now_day, url_name):
   """ добавление ссылки на книгу в базу
   
   """
   price = load_link(connect, now_day, url_name, 1)
      # загрузка прошла без осложнений
   if len(price) > 0:
      results = []
      cursor = connect.cursor()
      cursor.execute('select id from links where urlname like ?', ['%'+url_name+'%'] )
      data = cursor.fetchall()
      cursor.close()
      results.insert(0, (now_day, data[0][0], price) )
      insert_new_price_into_db(connect, results)
      print sys.argv[2], U' : цена сейчас: ', price


def usage_message():
   """ сообщение о правильном использовании
   
   """
   print U'использование:',\
         sys.argv[0], U'{-a <ссылка на книгу на ozon.ru> |',\
          '-g | -s}\n\t-a <ссылка на книгу на ozon.ru> - добавить книгу в базу',\
          '\n\t-g - получить текущие цены с сайта и сохранить их в базу'\
          '\n\t-s - получить цены с сайта, не сохраняя их в базу'

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
         print U'Ошибка при выполнении:', e.args[0]
   else:
      usage_message()
   connect.close()
except Exception, e:
   usage_message()
   print e

