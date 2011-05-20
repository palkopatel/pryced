#!/usr/bin/env python2
# -*- coding: utf-8

# prices watcher (ozon.ru, read.ru)
# скрипт для наблюдения за указанными книгами на ozon.ru, read.ru, my-shop.ru,
# ukazka.ru

try:
   from parsing import *
   from BeautifulSoup import BeautifulSoup
except:
   print u'Для работы нужна библиотека BeautifulSoup\n(Можно найти на сайте: http://code.google.com/p/pryced/downloads/list)\n'
   exit()
import datetime # для datetime.datetime.now()
import sqlite3
import sys
import urllib2

try:
   from ctypes import windll
   handle = windll.kernel32.GetStdHandle(-11)
except:
   pass
# признак запуска на windows-python
win32 = sys.platform.find(u'win')
# cygwin-python за window не считать!
if sys.platform.find(u'cygwin') > -1:
   win32 = -1
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
def console_color(color):
   windll.kernel32.SetConsoleTextAttribute(handle, color)

def connect_to_base():
    """ подключение к базе, создание таблиц

    """
    connect = sqlite3.connect('myozon.db')
    cursor = connect.cursor()
    try:
        cursor.execute('create table IF NOT EXISTS books \
        (id integer primary key AUTOINCREMENT, \
        isbn text, title text, author text)')
        connect.commit()
    except sqlite3.Error, e:
        print u'Ошибка при создании таблицы:', e.args[0]
    try:
        cursor.execute('create table IF NOT EXISTS links \
        (id integer primary key AUTOINCREMENT, \
        book int,\
        urlname text, title text, author text, \
        serial text, desc1 text, desc2 text, \
        timestamp DEFAULT current_timestamp)')
        connect.commit()
    except sqlite3.Error, e:
        print u'Ошибка при создании таблицы:', e.args[0]
    try:
        cursor.execute('create table IF NOT EXISTS prices \
        (id integer primary key AUTOINCREMENT, \
        link int, price int, \
        timestamp DEFAULT current_timestamp)')
        connect.commit()
    except sqlite3.Error, e:
        print u'Ошибка при создании таблицы:', e.args[0]

    # добавление колонки для версии без ISBN
    try:
        connect.execute('ALTER TABLE links ADD COLUMN book int;')
        connect.execute("VACUUM")
    except:
        pass
    cursor.close()
    return connect

def insert_new_book(connect, isbn, title, author):
   """ загрузка новой книги в свою базу

   """
   book_id = 0
   try:
      cursor = connect.cursor()
      cursor.execute('select id from books where isbn like ?', ['%'+isbn+'%'])
      books_data = cursor.fetchall()
      cursor.close()
      if len(books_data) > 0:
         for book_data in books_data:
            book_id = book_data[0]
      else:
         try:
            cursor = connect.cursor()
            cursor.execute( 'insert into books (isbn, title, author) \
               values (?, ?, ?)', (isbn, title, author) )
            book_id = cursor.lastrowid
            cursor.close()
            connect.commit()
         except sqlite3.Error, e:
            print u'Ошибка при выполнении запроса:', e.args[0]
   except sqlite3.Error, e:
      print u'Ошибка при выполнении запроса:', e.args[0]
   return book_id

def load_link(connect, now_day, url_name, create_flag):
   """ загрузка новой ссылки на книгу в свою базу
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
            print u'Ссылка на "' + data[0][0] + u'. ' + data[0][1] + \
                  u'" уже существует в базе!'
            return 0;
      f = urllib2.urlopen(url_name) 
      datas = f.read()
      f.close()
      soup = BeautifulSoup(datas)
      if url_name.find(u'ozon.ru') > -1:
         (title, author, serial, isbn, desc2, price) = ozonru_parse_book(soup, create_flag)
      elif url_name.find(u'read.ru') > -1: 
         (title, author, serial, isbn, desc2, price) = readru_parse_book(soup, create_flag)
      elif url_name.find(u'my-shop.ru') > -1: 
         (title, author, serial, isbn, desc2, price) = myshop_parse_book(soup, create_flag)
      elif url_name.find(u'ukazka.ru') > -1: 
         (title, author, serial, isbn, desc2, price) = ukazka_parse_book(soup, create_flag)
      else:
         return 0
      if create_flag > 0:
         try:
            book_id = insert_new_book(connect, isbn, title, author)
            cursor = connect.cursor()
            cursor.execute( 'insert into links \
               (book, urlname, title, author, serial) \
               values (?, ?, ?, ?, ?)', \
               (book_id, url_name, title, author, serial) )
            cursor.close()
            connect.commit()
            print u'Ссылка на "' + author + u'. ' + \
               title + u'" добавлена в базу.'
         except sqlite3.Error, e:
            print u'Ошибка при выполнении запроса:', e.args[0]
      return int(float(price.replace(',', '.')))
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
   print u'Цены обновлены.'

def load_new_price(connect, now_day, insert_mode):
   """ получение текущих цен для имеющихся книг
   "   сохранение цен в свою базу при insert_mode == 1

   """
   cursor = connect.cursor()
      # перебор книг в базе
   cursor.execute('select links.id, links.urlname, links.author || ", " || links.title \
                        , ifnull(min(prices.price),0)\
                        , ifnull(max(prices.price),0)\
                        , links.author, links.title\
                   from links \
                   left join prices on links.id = prices.link \
                   group by links.id, links.author, links.title \
                   order by links.author, links.title, links.urlname')
   rows = cursor.fetchall()
   results = []
   for row in rows:
      color_sym = u''
      color_price = -1
      if insert_mode > 0: # получение текущей цены с сайта
         price = load_link(connect, now_day, row[1], 0)
         if price != 0 :
            if price < int(row[3]): 
               if win32 == -1:
                  color_sym = u'\033[1;35m'
               else:
                  color_price = FG_RED|FG_INTENSITY|BG_BLACK
            elif price == int(row[3]):
               if win32 == -1:
                  color_sym = u'\033[1;36m'
               else:
                  color_price = FG_CYAN|FG_INTENSITY|BG_BLACK
      else: price = 0
         # сокращенное название сайта с подсветкой
      if win32 == -1:
         if row[1].find(u'ozon.ru') > -1:
            site = u'\033[1;46mozon.ru\033[0m: '
         elif row[1].find(U'read.ru') > -1:
            site = u'\033[1;43mread.ru\033[0m: '
         elif row[1].find(U'my-shop.ru') > -1: 
            site = u'\033[1;47mmy-shop\033[0m: '
         elif row[1].find(U'ukazka.ru') > -1: 
            site = u'\033[1;44mukazka \033[0m: '
         else:
            site = u'none'
         sys.stdout.write(site)
         close_color = u'\033[0m'
      else:
         if row[1].find(u'ozon.ru') > -1:
            site = u'ozon.ru'
            colornum = FG_GREY|FG_INTENSITY|BG_CYAN|BG_INTENSITY
         elif row[1].find(U'read.ru') > -1:
            site = u'read.ru'
            colornum = FG_GREY|FG_INTENSITY|BG_YELLOW
         elif row[1].find(U'my-shop.ru') > -1: 
            site = u'my-shop'
            colornum = FG_BLACK|BG_GREY|BG_INTENSITY
         elif row[1].find(U'ukazka.ru') > -1: 
            site = u'ukazka '
            colornum = FG_GREY|BG_BLUE|BG_INTENSITY
         else:
            site = u'none'
         console_color(colornum)
         sys.stdout.write(site+u': ')
         console_color(FG_GREY|BG_BLACK)
         color_sym = close_color = u''
      if win32 == -1:
         print(row[2] + u';' + color_sym + \
               u' сейчас: ' + unicode(str(price)) + close_color + \
               u', минимум: ' + unicode(str(row[3])) + \
               u', максимум: ' + unicode(str(row[4])) + u'; ' + row[1])
      else:
         sys.stdout.write(row[2] + u';' + color_sym)
         if color_price > 0:
            console_color(color_price)
         sys.stdout.write(u' сейчас: ' + unicode(str(price)) + close_color )
         console_color(FG_GREY|BG_BLACK)
         print(u', минимум: ' + unicode(str(row[3])) + \
               u', максимум: ' + unicode(str(row[4])) + u'; ' + row[1])
      if insert_mode == 1:
         if price != 0: 
            results.insert(0, (now_day, row[0], price) )
      else:
         results.insert(len(results), (row[0], row[1], row[3], row[4], row[5], row[6], price) )
   cursor.close()
   if insert_mode == 1 and len(results) > 0:
      insert_new_price_into_db(connect, results)
   else:
      return results

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
      print sys.argv[2] + u': цена сейчас:', str(price)

def usage_message():
   """ сообщение о правильном использовании

   """
   msg = u'использование: ' + \
         unicode(sys.argv[0]) + u' {-a <ссылка на книгу> | -g | -s}' + \
         u'\n\t-a <ссылка на книгу> - добавить книгу в базу' +\
         u'\n\t-g - получить текущие цены и сохранить их в базу' +\
         u'\n\t-s - получить цены, не сохраняя их в базу'
   print msg

if __name__ == "__main__":
   try:
          # значение даты для вставки в базу
      now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      connect = connect_to_base()
      if len(sys.argv) > 2:
         if sys.argv[1] == '-a': # добавление ссылки на книгу в базу
            add_new_book(connect, now_day, sys.argv[2])
         elif sys.argv[1] == '-t': # проба ссылки
            test_url(sys.argv[2])
      elif len(sys.argv) > 1 and (sys.argv[1] == '-g' or sys.argv[1] == '-s'): # добавление текущих цен в базу
         try:
            if sys.argv[1] == '-g': insert_mode = 1
            else: insert_mode = 0
            load_new_price(connect, now_day, insert_mode)
         except sqlite3.Error, e:
            print u'Ошибка при выполнении:', e.args[0]
      else:
         usage_message()
      connect.close()
   except Exception, e:
      usage_message()
      print e
