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

def ozonru_parse_book(url_name, create_flag):
   """ разбор страницы с ozon.ru

   """
   title = ''
   author = ''
   isbn = ''
   serial = ''
   desc2 = ''

   list0=url_name.split('/')
   if( list0[len(list0)-1] == ''): id=list0[len(list0)-2]
   else: id=list0[len(list0)-1]

   if create_flag > 0:
      url_name='http://www.ozon.ru/webservices/OzonWebSvc.asmx/ItemDetail?ID='+id
      f = urllib2.urlopen(url_name)
      datas = f.read()
      f.close()
      soup = BeautifulSoup(datas)
      try:
         title = soup.find('name').string
         author = soup.find('author').string
         isbn = soup.find('isbn').string
      except:
         desc2 = None
      if title == None: title = '-'
      if author == None: author = '-'
      else: author = convert_author_string(author)
      if isbn == None: isbn = '-'

   url_name='http://www.ozon.ru/webservices/OzonWebSvc.asmx/ItemInfo?ID='+id
   f = urllib2.urlopen(url_name)
   datas = f.read()
   f.close()
   soup = BeautifulSoup(datas)
   try:
      price = soup.find('price').string.split('.')[0]
      availability = soup.find('availability').string
      # не нашел признака отсутствия книги кроме этого тектового поля
      if availability.find(U'Товар отсутствует') != -1:
         price = '0'
   except:
      price = '0'
   return (title, author, serial, isbn, desc2, price)

def readru_parse_book(soup, create_flag):
   """ разбор страницы с read.ru

   """
   title = author = serial = isbn = ''
   if create_flag > 0:
      title = soup.find('h1').string
         # найти таблицу с атрибутом id равным book_fields
      table = soup.find('table', {'class':'book_fields'})
      serial = ''
      isbn = ''
      for row in table.findAll('tr'): # перебрать строки
         for cell in row.findAll('td', {'class':'f'}): # перебрать ячейки в строке
            if cell.string.find(U'Автор') > -1: # найти ячейку с именем автора
               author = row.find('a').string
            elif cell.string.find(U'Серия') > -1: # найти ячейку с названием серии
               serial = row.find('a').string
            elif cell.string.find(U'ISBN') > -1: # найти ячейку с ISBN
               # старый способ извлечение ISBN, который перестал работать 01-03-2011
               # примерно с середины июня 2011 этот способ снова работает
               isbn = row.contents[3].string.replace("\t", "").replace("\n", "").replace("\r", "")
               continue
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
         else:
            continue
         break
   try:
      price_tag = soup.find('span', {'class':'price '})
      pos_end = price_tag.renderContents().find('<')
      price = price_tag.renderContents()[0:pos_end]
      price = price.replace('&nbsp;', '')
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def myshop_parse_book(soup, create_flag):
   """ разбор страницы с my-shop.ru

   """
   if create_flag > 0:
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

      try:
         title_tag = soup.find('title').string.split(' | ')
         book_name = title_tag[0].split(' - ')
         title = book_name[0]
         author = book_name[1]
      except:
         author = ''
         title = ''

      # извлечь теги span, найти среди них содержащий слово 'ISBN'
      isbn = ''
      span = soup.findAll('span', attrs={'class':'small1'})
      for span_row in span:
         # случай явного указания автора
         if len(span_row.contents) == 1:
            if span_row.string.find(U'ISBN') > -1:
               isbn = span_row.string.split(': ')[1]
   else:
      title = ''
      author = ''
      serial = ''
      isbn = ''
   # извлечь цену из определенно отформатированной ячейки
   b = soup.findAll('b')
   not_have = 0
   for price_row in b:
      price_row_str = price_row.string
      try:
         if price_row_str.find(U'Цена:') > -1:
            price = price_row_str.split('&nbsp;')[1]
         if price_row_str.find(U'Сообщить о поступлении в продажу') > -1:
            not_have = 1
      except:
         price = '0'
         continue
   # изощренный способ определения наличия книги
   if not_have == 1:
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
   try:
      price = soup.find('span', attrs={'class':'price'}).string.split('&nbsp;')[0]
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def bolero_parse_book(soup, create_flag):
   """ разбор страницы с bolero.ru

   """
   serial = ''
   if create_flag > 0:
      title_tag = soup.find('title').string.split('-')
      title = title_tag[0].strip()
      author = title_tag[1].strip()
      done = 0
      for table in soup.findAll('table'):
         for row in table.findAll('tr'):
            for cell in row.findAll('td'):
               try:
                  if cell.string.find(U'ISBN') > -1:
                     isbn = row.find('b').string
                     done += 1
                     break
                  if cell.string.find(U'Серия') > -1:
                     serial = row.find('a').string
                     done += 1
                     break
               except:
                  pass
            if done >= 2 :
               break
         if done >= 2:
            break
   else:
      title = ''
      author = ''
      isbn = ''
   price_tag = soup.find('div', attrs={'class':'price'})
   if price_tag != None:
       price = price_tag.contents[0].string.replace('&nbsp;', '')
   else:
       price = '0'
   return (title, author, serial, isbn, '', price)

def labiru_parse_book(soup, create_flag):
   """ разбор страницы с labirint.ru

   """
   serial = ''
   #<div id="product-specs">
   product = soup.find('div', attrs={'id':'product-specs'})
   if create_flag > 0:
      try:
         #<div class="isbn smallbr">ISBN: 978-5-89059-155-5</div>
         isbn = product.find('div', attrs={'class':'isbn smallbr'}).string.split(': ')[1]
      except:
         isbn = ''
      try:
         #<div class="">
         nonames = product.find('div', attrs={'class':''})
         author = nonames.find('a').string
      except:
         author = ''
      try:
         #<meta property="og:title" content="Горы моря и гиганты" />
         title_tag = soup.find('meta', attrs={'property':'og:title'})
         title = title_tag['content']
      except:
         title = ''
   else:
      title = ''
      author = ''
      isbn = ''
   try:
      #<div class="availibility">Наличие: <span class="rang-expected">Ожидается</span></div>
      #<div class="availibility">Наличие: <span class="rang-available">На складе</span></div>
      availibility = product.find('div', attrs={'class':'availibility'})
      available = availibility.find('span', attrs={'class':'rang-available'})
      if available != None:
         #<div class='price_num'>Цена <span class="value">680</span> руб.</div>
         price_div = product.find('div', attrs={'class':'price_num'})
         price = price_div.find('span', attrs={'class':'value'}).string
      else:
         price = '0'
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def bgshop_parse_book(soup, create_flag):
   """ разбор страницы с bgshop.ru

   """
   serial = ''
   product = soup.find('div', attrs={'id':'ctl00_cph_ucGoodCard_pnl_card'})
   if create_flag > 0:
       try:
           title = product.find('span', attrs={'class':'title'}).find('b').string
       except:
           title = ''
       try:
           author = product.find('a', attrs={'class':'author'}).string
       except:
           author = ''
       try:
           isbn = product.find('span', attrs={'id':'ctl00_cph_ucGoodCard_lbl_IsbnAsIs'}).string
       except:
           isbn = ''
   else:
       title = ''
       author = ''
       isbn = ''
   try:
       # хитроумная замена - это борьба с неразрывным пробелом (символ с кодом 160)
       price = soup.find('span', attrs={'class':'price'}).string.split(',')[0].replace(u'\xa0', '')
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def setbook_parse_book(soup, create_flag):
   """ разбор страницы с setbook.ru

   """
   serial = ''
   if create_flag > 0:
       try:
           title = soup.find('div', attrs={'class':'row_product_name'}).string
       except:
           title = ''
       try:
           author = soup.find('div', attrs={'class':'row_product_author'}).find('a').string
       except:
           author = ''
       try:
           isbn = soup.find('div', attrs={'class':'row_product_model'}).string.split(':')[1].replace(' ', '')
       except:
           isbn = ''
   else:
       title = ''
       author = ''
       isbn = ''
   try:
       # '`' - разделитель тысяч
       price = soup.find('div', attrs={'class':'row_product_price'}).string.split(u'\xa0')[0].replace('`', '')
       # быват, что на месте цены стоит надпись 'Нет в продаже'
       if not price.isdigit():
           price = '0'
   except:
      price = '0'
   return (title, author, serial, isbn, '', price)

def test_url(url_name):
   """ функция для тестирования (запуск с аргументом -t <ссылка>)

   """
   if url_name.find(u'ozon.ru') > -1:
      (title, author, serial, isbn, desc2, price) = ozonru_parse_book(url_name, 1)
#   if url_name.find(u'my-shop.ru') > -1:
#      (title, author, serial, isbn, desc2, price) = myshop_parse_book2(url_name, 1)
   else:
      f = urllib2.urlopen(url_name)
      datas = f.read()
      f.close()
      soup = BeautifulSoup(datas)
      if url_name.find(u'read.ru') > -1:
         (title, author, serial, isbn, desc2, price) = readru_parse_book(soup, 1)
      elif url_name.find(u'my-shop.ru') > -1:
         (title, author, serial, isbn, desc2, price) = myshop_parse_book(soup, 1)
      elif url_name.find(u'ukazka.ru') > -1:
         (title, author, serial, isbn, desc2, price) = ukazka_parse_book(soup, 1)
      elif url_name.find(u'bolero.ru') > -1:
         (title, author, serial, isbn, desc2, price) = bolero_parse_book(soup, 1)
      elif url_name.find(u'labirint.ru') > -1:
         (title, author, serial, isbn, desc2, price) = labiru_parse_book(soup, 1)
      elif url_name.find(u'bgshop.ru') > -1:
         (title, author, serial, isbn, desc2, price) = bgshop_parse_book(soup, 1)
      elif url_name.find(u'setbook.ru') > -1:
         (title, author, serial, isbn, desc2, price) = setbook_parse_book(soup, 1)
   print u'title:  ' + title
   print u'author: ' + author
   print u'serial: ' + serial
   print u'isbn:   ' + isbn
   print u'price:  ' + price
   if desc2 == None:
      desc2 = u'ОШИБКА РАЗБОРА!!!'
   print u'desc2:  ' + desc2
   return (title, author, serial, isbn, desc2, price)
