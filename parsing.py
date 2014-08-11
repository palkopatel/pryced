#!/usr/bin/env python3
# -*- coding: utf-8

# разбор html-кода в поисках характеристик книги

from bs4 import BeautifulSoup
import urllib.request
import subprocess
import re
from pryced import *

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
   title = author = serial = isbn = u''
   if create_flag > 0:
      content = soup.find('div', {'class':'bContentBlock'})
      title = content.find('h1', {'itemprop':'name'}).string.strip()
      # в ISBN еще зачем-то записан год. его надо убрать
      # в общем виде ISBN выглядит так {ISBN<нужное значение>; год}
      isbn = content.find('p', {'itemprop':'isbn'}).string.split(';')[0].strip()
      if isbn.find('ISBN') == 0: # удалить текст в начале строки и убрать пробелы
         isbn = isbn[4:].strip()
      try:
         author = content.find('p', {'itemprop':'author'}).find('a').string
      except:
         try:
            author = content.find('p', {'itemprop':'author'}).string.split(':')[1].strip()
         except:
            # автора нет
            pass
   try:
      content = soup.find('div', {'class':'bSaleColumn'})
      price = content.find('span', {'itemprop':'price'}).string.split('.')[0]
   except:
      price = u'0'

   return (title, author, serial, isbn, u'', price)

def readru_parse_book(soup, create_flag):
   """ разбор страницы с read.ru

   """
   title = author = serial = isbn = u''
   if create_flag > 0:
      title = soup.find('h1').string
      table = soup.find('table', {'id':'book_fields_1'})
      isbn = table.find('td', {'class':'isbn'}).find('span').contents[1].string
      try:
         author = table.find('td', {'class':'author'}).find('a').string
      except:
         author = u''
      try:
         serial = table.find('td', {'class':'series'}).find('a').string
      except:
         serial = u''
   try:
      table = soup.find('table', {'id':'book_fields_3'})
      price_tag = table.find('span', {'class':'price'})
      price = price_tag.contents[1].string.strip()
   except:
      price = u'0'
   return (title, author, serial, isbn, u'', price)

def myshop_parse_book(soup, create_flag):
   """ разбор страницы с my-shop.ru

   """
   if create_flag > 0:
      serial = u''
      try:
         title_tag = soup.find('title').string.split(' | ')
         book_name = title_tag[0].split(' - ')
         title = book_name[0]
         author = book_name[1]
      except:
         author = u''
         title = u''

      # извлечь теги span, найти среди них содержащий слово 'ISBN'
      isbn = u''
      span = soup.findAll('span', attrs={'class':'small1'})
      for span_row in span:
         # случай явного указания автора
         if span_row != None and len(span_row.contents) == 1:
            if span_row.string != None and span_row.string.find(U'ISBN') > -1:
               isbn = span_row.string.split(': ')[1]
   else:
      title = u''
      author = u''
      serial = u''
      isbn = u''
   # извлечь цену из определенно отформатированной ячейки
   price = u'0'
   td = soup.find('td', attrs={'class':'bgcolor_2 list_border'})

   noindex_cnx = td.find('noindex')
   if noindex_cnx != None and len(noindex_cnx.contents) > 0:
      for line in noindex_cnx.contents:
         if isinstance(line, str) and line.find(u'в наличии') > -1:
            b = td.find('b')
            if b != None:
               price = re.search(r'[0-9]+', b.string).group(0)
            break

   return (title, author, serial, isbn, u'', price)

def ukazka_parse_book(soup, create_flag):
   """ разбор страницы с ukazka.ru

   """
   if create_flag > 0:
      title = soup.find('h1').string
      if title[len(title)-1]=='.':
         title = title[0:-1]
      #  найти теги div с определенным атрибутом class
      table = soup.findAll('div', attrs={'class':'lpad20 bot_pad'})
      try:
         author_raw = table[0].contents[0].find('b').contents[0]
         author = convert_author_string(author_raw)
      except:
         author = u''
      try:
         serial = table[9].contents[0].find('a').contents[0]
      except:
         serial = u''
      try:
         isbn = table[2].contents[1].contents[0]
      except:
         isbn = u''
   else:
      title = u''
      author = u''
      serial = u''
      isbn = u''
   try:
      price = soup.find('span', attrs={'class':'price'}).contents[0]
   except:
      price = u'0'
   return (title, author, serial, isbn, u'', price)

def bolero_parse_book(soup, create_flag):
   """ разбор страницы с bolero.ru

   """
   serial = u''
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
      title = u''
      author = u''
      isbn = u''
   price_tag = soup.find('div', attrs={'class':'price'})
   if price_tag != None:
       price = price_tag.contents[0].string.replace('&nbsp;', '')
   else:
       price = u'0'
   return (title, author, serial, isbn, u'', price)

def labiru_parse_book(soup, create_flag):
   """ разбор страницы с labirint.ru

   """
   serial = u''
   #<div id="product-specs">
   product = soup.find('div', attrs={'id':'product-specs'})
   if create_flag > 0:
      try:
         #<div class="isbn">ISBN: 978-5-89059-155-5</div>
         isbn = product.find('div', attrs={'class':'isbn'}).string.split(': ')[1]
      except:
         isbn = ''
      try:
         #<div class="authors">
         nonames = product.find('div', attrs={'class':'authors'})
         author = nonames.find('a').string
      except:
         author = ''
      try:
         #<meta property="og:title" content="Горы моря и гиганты" />
         title_tag = soup.find('meta', attrs={'property':'og:title'})
         title = title_tag['content']
      except:
         title = u''
      try:
         serial = product.find('div', attrs={'class':'series'}).find('a').string
      except:
         serial = u''
   else:
      title = u''
      author = u''
      isbn = u''
   try:
      #<div class="prodtitle-availibility rang-available"><span>На складе</span></div>
      #<div class="prodtitle-availibility rang-expected"><span>Ожидается</span></div>
      availibility = soup.find('div', attrs={'class':'prodtitle-availibility rang-available'})
      if availibility == None:
         availibility = soup.find('div', attrs={'class':'prodtitle-availibility rang-expected'})
      available = availibility.find('span')
      if available != None:
         #<span class="buying-price-val-number">399</span> 
         price_tag = product.find('span', attrs={'class':'buying-price-val-number'})
         if price_tag == None:
            price_tag = product.find('span', attrs={'class':'buying-pricenew-val-number'})
         if price_tag == None:
            price_tag = product.find('span', attrs={'class':'buying-priceold-val-number'})
         price = price_tag.string
      else:
         price = u'0'
   except:
      price = u'0'
   return (title, author, serial, isbn, u'', price)

def bgshop_parse_book(soup, create_flag):
   """ разбор страницы с bgshop.ru

   """
   serial = u''
   product = soup.find('div', attrs={'id':'ctl00_cph_ucGoodCard_pnl_card'})
   if create_flag > 0:
       try:
           title = product.find('span', attrs={'class':'title'}).string
       except:
           title = u''
       try:
           author = product.find('a', attrs={'class':'author'}).string
       except:
           author = u''
       try:
           isbn = product.find('span', attrs={'id':'ctl00_cph_ucGoodCard_lbl_IsbnAsIs'}).string
       except:
           isbn = u''
   else:
       title = u''
       author = u''
       isbn = u''
   try:
       # хитроумная замена - это борьба с неразрывным пробелом (символ с кодом 160)
       price = soup.find('span', attrs={'class':'price'}).string.split(',')[0].replace(u'\xa0', '')
   except:
      price = u'0'
   return (title, author, serial, isbn, u'', price)

def setbook_parse_book(soup, create_flag):
   """ разбор страницы с setbook.ru

   """
   serial = u''
   if create_flag > 0:
       try:
           title = soup.find('div', attrs={'class':'row_product_name'}).string
       except:
           title = u''
       try:
           author = soup.find('div', attrs={'class':'row_product_author'}).find('a').string
       except:
           author = u''
       try:
           isbn = soup.find('div', attrs={'class':'row_product_model'}).string.split(':')[1].replace(' ', '')
       except:
           isbn = u''
   else:
       title = u''
       author = u''
       isbn = u''
   try:
       # '`' - разделитель тысяч
       price = soup.find('div', attrs={'class':'row_product_price'}).string.split(u'\xa0')[0].replace('`', '')
       # быват, что на месте цены стоит надпись 'Нет в продаже'
       if not price.isdigit():
           price = u'0'
   except:
      price = u'0'
   return (title, author, serial, isbn, u'', price)

def knigaru_parse_book(soup, create_flag):
   """ разбор страницы с kniga.ru

   """
   serial = u''
   title = u''
   author = u''
   isbn = u''
   desc2 = u''
   productDescription = soup.find('div', attrs={'id':'productDescription'})
   if create_flag > 0:
       try:
           title = productDescription.find('h1').string
       except:
           title = u''
       try:
           author = productDescription.find('span', attrs={'id':'authorsList'}).find('a').string
       except:
           author = u''
       properties = productDescription.find('div', attrs={'id':'properties'})

       # извлечь цену из определенно отформатированной ячейки
       fields = properties.findAll('p')
       for row in fields:
          try:
              row_str = row.find('span', attrs={'class':'fieldName'}).string
              try:
                 if row_str.find(U'ISBN:') > -1:
                    isbn = row.contents[1].strip()
              except:
                 pass
              try:
                 if row_str.find(U'Серия:') > -1:
                    serial = row.find('a').string
              except:
                 pass
          except:
             continue
   try:
       buyArea = productDescription.find('div', attrs={'id':'buyArea'})
       price = buyArea.find('p', attrs={'id':'normalPrice'}).find('span').string
       try:
           desc2 = buyArea.find('p', attrs={'class':'normalPrice'}).find('span').string.split(' ')[0]
       except:
           pass
   except:
      price = u'0'
   return (title, author, serial, isbn, desc2, price)

def booksru_parse_book(soup, create_flag):
   """ разбор страницы с books.ru

   """
   serial = u''
   title = u''
   author = u''
   isbn = u''
   desc2 = u''

   if create_flag > 0:
      try:
         bookInfo = soup.find('td', attrs={'class':'book-info'})
         try:
            author_raw = bookInfo.find('p', attrs={'class':'author'})
            aLink = author_raw.find('a')
            if aLink != None:
               author = aLink.string.strip()
            else:
               author = author_raw.string.strip()
         except:
            pass
         try:
            title = bookInfo.find('h1', attrs={'class':'item fn'}).string.strip()
         except:
            pass
         try:
            isbnData = bookInfo.find('ul', attrs={'class':'isbn-list'})
            isbn = isbnData.find('li', attrs={'class':'first'}).find('span').string
         except:
            pass
            
         addData = bookInfo.find('div', attrs={'class':'additional_data'})
         # извлечь цену из определенно отформатированной ячейки
         fields = addData.findAll('tr')
         for row in fields:
            try:
               td = row.findAll('td')
               if td[0].string.strip().find(U'Издательство:') > -1:
                 pubisher = td[1].find('a').string.strip()
               elif td[0].string.strip().find(U'Серия:') > -1:
                 serial = td[1].find('a').string.strip()
            except:
               continue
      except:
         pass
   try:
      price = soup.find('span', attrs={'class':'yspan'}).contents[0].string.strip()
   except:
      price = u'0'
   return (title, author, serial, isbn, desc2, price)
   
def test_url(url_name):
   """ функция для тестирования (запуск с аргументом -t <ссылка>)

   """
   try:
    #   if url_name.find(u'ozon.ru') > -1:
    #      (title, author, serial, isbn, desc2, price) = ozonru_parse_book(url_name, 1)
    #   if url_name.find(u'my-shop.ru') > -1:
    #      (title, author, serial, isbn, desc2, price) = myshop_parse_book2(url_name, 1)
    #   else:
       opener = urllib.request.build_opener()
       # 'Referer' нужен, чтобы обмануть "умные" сайты (setbook.ru), 
       # которые умеют определять страну и дают цену не в рублях
       opener.addheaders = [('Referer', url_name),
         ('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'),
         ('Accept-Language', 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'),
         ('Accept-Charset', 'Accept-Charset: windows-1251,utf-8;q=0.7,*;q=0.3')]
       f = opener.open(url_name)
#          f = urllib.request.urlopen(url_name) 
       datas = f.read()
       f.close()
       soup = BeautifulSoup(datas)
       if url_name.find(u'ozon.ru') > -1:
          (title, author, serial, isbn, desc2, price) = ozonru_parse_book(soup, 1)
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
       elif url_name.find(u'kniga.ru') > -1:
          (title, author, serial, isbn, desc2, price) = knigaru_parse_book(soup, 1)
       elif url_name.find(u'books.ru') > -1:
          (title, author, serial, isbn, desc2, price) = booksru_parse_book(soup, 1)
       print (u'title:  ' + title)
       print (u'author: ' + author)
       print (u'serial: ' + serial)
       print (u'isbn:   ' + isbn)
       print (u'price:  ' + price)
       if desc2 == None:
          desc2 = (u'ОШИБКА РАЗБОРА!!!')
       print (u'desc2:  ' + desc2)
       return (title, author, serial, isbn, desc2, price)
   except Exception as e:
       print (e)

