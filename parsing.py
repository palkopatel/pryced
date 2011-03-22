#!/usr/bin/env python2
# -*- coding: utf-8

# разбор html-кода в поисках характеристик книги

from BeautifulSoup import BeautifulSoup
import urllib2
import subprocess

def convert_author_string(author_raw):
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
   return author

def ozonru_parse_book(soup, create_flag):
   """ разбор страницы с ozon.ru
   
   """
   if create_flag > 0:
      fields = soup.find('title').string.split(' | ')
      desc2 = fields[0]
      title = fields[1]
      author_raw = fields[2]
      author = convert_author_string(author_raw)
      try:
         serial = fields[3] 
      except:
         serial = ''
      
      # поиск ISBN в теге div
      isbn = ''
      for div_row in soup.find('div', attrs={'class':'detail_p small'}):
         if div_row.string != None and len(div_row.string) > 4:
            if div_row.string.find(U'ISBN') != -1:
               isbn = div_row.string.split('&nbsp;')[3]
   else:
      title = ''
      author = ''
      serial = ''
      isbn = ''
      desc2 = ''
   
   price = soup.find('big').string
   if price == None: price = '0'

   return (title, author, serial, isbn, desc2, price)

def readru_parse_book(soup, create_flag):
   """ разбор страницы с read.ru
   
   """
   title = author = serial = isbn = ''
   if create_flag > 0:
      title = soup.find('h1').string
         # найти таблицу с атрибутом id равным book_fields
      table = soup.find('table', {'id':'book_fields'})
      serial = ''
      isbn = ''
      for row in table.findAll('tr'): # перебрать строки
         for cell in row.findAll('td', {'class':'f'}): # перебрать ячейки в строке
            if cell.string.find(U'Автор') > -1: # найти ячейку с именем автора
               author = row.find('a').string
            elif cell.string.find(U'Серия') > -1: # найти ячейку с названием серии
               serial = row.find('a').string
            elif cell.string.find(U'ISBN') > -1: # найти ячейку с ISBN
               # ISBN спрятали в картинке. надо ее загрузить и распознать
               # 1) сначала получить ссылку
               piclink = row.contents[3].find('img')['src']
               # 2) загрузить картинку
               urlpic = urllib2.urlopen('http://read.ru' + piclink)
               localFile = open('tmp~', 'wb')
               localFile.write(urlpic.read())
               localFile.close()
               # 3) распознать картинку с помощью gocr
               try:
                  p1 = subprocess.Popen(["pngtopnm", 'tmp~'], stdout=subprocess.PIPE)
               except OSError, e:
                 if e.errno == 2:
                    print(u'\033[31mДля обработки ISBN надо установить пакет "netpbm" с утилитой "pngtopnm!"\033[0m')
                 else:
                    print e
                 break
               try:
                  p2 = subprocess.Popen(["gocr", "-"], stdin=p1.stdout, stdout=subprocess.PIPE)
               except OSError, e:
                 if e.errno == 2:
                    print(u'\033[31mДля распознавания ISBN надо установить пакет "gocr"!"\033[0m')
                 else:
                    print e
                 break
               p1.stdout.close()
               output = p2.communicate()[0]
               # срезать в выводе "лишние" символы
               isbn = output.replace(" ", "").replace("\n", "")
               # старый способ извлечение ISBN, который перестал работать 01-03-2011
               #isbn = row.contents[3].string.replace("\t", "").replace("\n", "").replace("\r", "")
         else:
            continue
         break
   try:
      price_tag = soup.find('span', {'class':'price '})
      pos_end = price_tag.renderContents().find('<')
      price = price_tag.renderContents()[0:pos_end]
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def myshop_parse_book(soup, create_flag):
   """ разбор страницы с my-shop.ru
   
   """
   if create_flag > 0:
      # найти первую форму с атрибутом name равным form1,
      # разбить на отдельные ячейки и извлечь из 0-й ячейки тег h1
      try:
         form = soup.find('form', attrs={'name':'form1'})
         td = form.findAll('td')
         title = td[0].find('h1').string
      except:
         title = ''
      # извлечь теги 'td' без атрибутов, в каждом найти контекст со словом 'Серия'
      try:
         serial = ''
         td2 = soup.findAll(lambda tag: len(tag.attrs) == 0 and tag.name == 'td')
         for td2_row in td2:
            i = 0
            for cnt in td2_row.contents:
               i += 1
               try:
                  if cnt.find(U'Серия') > -1:
                     serial = td2_row.contents[i].string
                     break
               except:
                  pass
      except:
         serial = ''
      # извлечь теги span, найти среди них содержащий слово 'Автор'
      # и получить в нем имя автора из тега 'a'
      author = ''
      isbn = ''
      span = soup.findAll('span', attrs={'class':'small1'})
      for span_row in span:
         # случай явного указания автора
         if len(span_row.contents) == 1:
            if span_row.string.find(U'Автор') > -1:
               author = span_row.string.split(': ')[1]
            elif span_row.string.find(U'ISBN') > -1:
               isbn = span_row.string.split(': ')[1]
         # случай, когда автор указан ссылкой
         elif len(span_row.contents) > 1:
            try:
               if span_row.contents[0].find(U'Автор') > -1:
                  author = span_row.find('a').string
            except:
               pass
   else:
      title = ''
      author = ''
      serial = ''
      isbn = ''
   # извлечь цену из определенно отформатированной ячейки
   b = soup.findAll('b')
   for price_row in b:
      price_row_str = price_row.string
      try:
         if price_row_str.find(U'Цена:') > -1:
            price = price_row_str.split('&nbsp;')[1]
      except:
         price = '0'
   return (title, author, serial, isbn, '', price)

def ukazka_parse_book(soup, create_flag):
   """ разбор страницы с ukazka.ru
   
   """
   if create_flag > 0:
      #  найти тег h1 с определенным атрибутом class
      title = soup.find('h1', attrs={'class':'bot_pad0'}).string
      if title[len(title)-1]=='.':
         title = title[0:-1]
      #  найти теги div с определенным атрибутом class
      table = soup.findAll('div', attrs={'class':'lpad20 bot_pad'})
      try:
         author_raw = table[0].contents[0].find('b').contents[0]
         author = convert_author_string(author_raw)
      except:
         author = ''
      try:
         serial = table[9].contents[0].find('a').contents[0]
      except:
         serial = ''
      try:
         isbn = table[2].contents[1].contents[0]
      except:
         isbn = ''
   else:
      title = ''
      author = ''
      serial = ''
      isbn = ''
   price = soup.find('span', attrs={'class':'price'}).string.split('&nbsp;')[0]
   return (title, author, serial, isbn, '', price)

def test_url(url_name):
   """ функция для тестирования (запуск с аргументом -t <ссылка>)
   
   """
   f = urllib2.urlopen(url_name)
   datas = f.read()
   f.close()
   soup = BeautifulSoup(datas)
   if url_name.find(u'ozon.ru') > -1:
      (title, author, serial, isbn, desc2, price) = ozonru_parse_book(soup, 1)
   elif url_name.find(u'read.ru') > -1: 
      (title, author, serial, isbn, desc2, price) = readru_parse_book(soup, 1)
   elif url_name.find(u'my-shop.ru') > -1: 
      (title, author, serial, isbn, desc2, price) = myshop_parse_book(soup, 1)
   elif url_name.find(u'ukazka') > -1: 
      (title, author, serial, isbn, desc2, price) = ukazka_parse_book(soup, 1)
   print u'title:  ' + title
   print u'author: ' + author
   print u'serial: ' + serial
   print u'isbn:   ' + isbn
   print u'price:  ' + price
   print u'desc2:  ' + desc2

