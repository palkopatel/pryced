#!/usr/bin/env python
# -*- coding: utf-8

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
        cursor.execute('create table links \
        (id integer primary key AUTOINCREMENT, \
        urlname text, title text, author text, \
        serial text, desc1 text, desc2 text, \
        timestamp DEFAULT current_timestamp)')
    except sqlite3.Error, e:
        print "message on create table:", e.args[0]
    try:
        cursor.execute('create table prices \
        (id integer primary key AUTOINCREMENT, \
        link int, price int, \
        timestamp DEFAULT current_timestamp)')
    except sqlite3.Error, e:
        print "message on create table:", e.args[0]
    return (connect, cursor)

def load_link(url_name, create_flag):
   """ загрузка новой книги в свою базу
   
   """
   f = urllib2.urlopen(url_name) 
   datas = f.read()
   f.close()
   soup = BeautifulSoup(datas)
   if create_flag > 0:
      (connect, cursor) = connect_to_base()
      try:
         fields = soup.find('title').string.split(' | ')
         cursor.execute( 'insert into links (urlname, title, author, serial, desc1, desc2) values (?, ?, ?, ?, ?, ?)', 
                         (url_name, fields[1], fields[2], fields[3], fields[4], fields[0]) )
         cursor.close()
         connect.commit()
         connect.close()
         print "commit link ok."
      except sqlite3.Error, e:
         print "An error occurred:", e.args[0]
   return soup.find('big').string

def load_new_price(now_day):
   """ получение и сохранение в свою базу текущих цен для имеющихся книг
   
   """
   (connect, cursor) = connect_to_base()
      # перебор книг в базе
   cursor.execute('select links.id, links.urlname, links.author || ", " || links.title \
                        , min(prices.price)\
                   from links \
                   join prices on links.id = prices.link \
                   group by links.id, links.author, links.title')
   rows = cursor.fetchall()
   results = []
   for row in rows:
         # получение текущей цены с сайта
      price = load_link(row[1], 0)
      print row[1] + ' : ' + row[2] + U'  : сейчас: ' + str(price) + U' : минимум: ' + str(row[3])
      results.insert(0, (now_day, row[0], price) )
   cursor.close()

   cursor = connect.cursor()
      # сохранение текущих цен в базе
   for price in results:
      cursor.execute( 'insert into prices (timestamp, link, price) values (?, ?, ?)', price )
   connect.commit()
   connect.close()
   print "commit prices ok."
   
   return results

def usage_message():
   """ сообщение о правильном использовании
   
   """
   print 'usage:',  sys.argv[0], '-a <urlname> | -g'

try:
       # значение даты для вставки в базу
   now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

   if sys.argv[1] == '-a': # добавление ссылки на книгу в базу
      print( sys.argv[2], ' ', load_link(sys.argv[2], 1) )
   elif sys.argv[1] == '-g': # добавление текущих цен в базу
      try:
         load_new_price(now_day)
      except sqlite3.Error, e:
         print "An error occurred:", e.args[0]
   else:
      usage_message()
except Exception, e:
   usage_message()
   print e

