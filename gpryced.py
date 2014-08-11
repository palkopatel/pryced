#!/usr/bin/env python3
# -*- coding: utf-8

import sys
import datetime # для datetime.datetime.now()

from pryced import *

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from numpy import arange

import matplotlib
matplotlib.use('gtk3agg')
from matplotlib import pyplot as plt
#import matplotlib.pyplot as plt
#import matplotlib.dates
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvasGTK
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

import time
import matplotlib as mpl

mpl.rcParams['lines.linewidth'] = 1.5
mpl.rcParams['lines.antialiased'] = True
mpl.rcParams['legend.frameon'] = False
mpl.rcParams['legend.fontsize'] = 'medium'
mpl.rcParams['axes.grid'] = True
mpl.rcParams['figure.subplot.left'] = 0.03
mpl.rcParams['figure.subplot.bottom'] = 0.1
mpl.rcParams['figure.subplot.right'] = 0.99
mpl.rcParams['figure.subplot.top'] = 0.93

# распечатать все названия параметров графиков
#for param in matplotlib.rcParams.keys(): print param

# номера полей в таблице с книгами
F_NAME = 0
F_PRICE_MIN = 1
F_PRICE_MAX = 2
F_PRICE_CUR = 3
F_BOOK_ID = 4
F_SITEICON = 5
F_FAVICON = 6
F_TIMESTAMP = 7
F_UNIXSEC = 8
F_FG_TIMESTAMP = 9
F_FG_PRICE_CUR = 10
F_ISBN = 11
F_LINK_ID = 12
F_IS_VISIBLE = 13
F_STATE = 14

# вывод всех методов класса (иногда нужно для отладки)
#import inspect
#res = inspect.getmembers(model)
#for item in res: print item

class App(object):

   def onCut(widget, action):
      event = widget.treeview.get_selection()
      model_pre, iter_src = event.get_selected()
      try:
         # конвертировать модель и узел (для модели-фильтра)
         widget.iter_src = model_pre.convert_iter_to_child_iter(iter_src)
         model = model_pre.get_model()
         # не копировать с верхнего уровня
         if len(model.get_path(widget.iter_src)) == 1:
            return
         widget.builder.get_object("toolbuttonPaste").set_sensitive(1)
      except:
         print ('no cut!')

   def onPaste(widget, action):
         # копировать нечего
         if widget.iter_src == None:
            return
         event = widget.treeview.get_selection()
         model_pre, iter_dest_pre = event.get_selected()
         # конвертировать модель и узел (для модели-фильтра)
         iter_dest = model_pre.convert_iter_to_child_iter(iter_dest_pre)
         model = model_pre.get_model()
         # вставлять разрешено только в первый уровень
         if len(model.get_path(iter_dest)) != 1:
            return
         # не вставлять в своего же родителя
         if model.iter_parent(widget.iter_src) != iter_dest :
            try:
               book_id = model[iter_dest][F_BOOK_ID]
               link_id = model[widget.iter_src][F_LINK_ID]
               cursor = widget.connect.cursor()
               cursor.execute( 'update links set book=? where id=?', (book_id, link_id) )
               cursor.close()
               widget.connect.commit()
               model.append(iter_dest, model[model.get_path(widget.iter_src)])
               model.remove(widget.iter_src)
               widget.iter_src = None
               widget.builder.get_object("toolbuttonPaste").set_sensitive(0)
            except sqlite3.Error as e:
               print (u'Ошибка при выполнении запроса:', e.args[0])

   def onEditBook(widget, action):
      event = widget.treeview.get_selection()
      model_pre, iter_src_pre = event.get_selected()
      # конвертировать модель и узел (для модели-фильтра)
      widget.iter_edit = model_pre.convert_iter_to_child_iter(iter_src_pre)
      widget.model_edit = model = model_pre.get_model()

      # редактировать только в первый уровень
      if len(model.get_path(widget.iter_edit)) != 1:
          return

      if widget.book_dlg == None:
          widget.builder.add_from_file("glade/book_edit_dialog.glade")
          widget.book_dlg = widget.builder.get_object("book_edit_dialog")
          widget.builder.connect_signals(widget)

      book_id = model[widget.iter_edit][F_BOOK_ID]
      widget.builder.get_object("tfBookId").set_text(str(book_id))
      cursor = widget.connect.cursor()
      cursor.execute('select books.isbn, \
                        books.author, books.title \
                     from books \
                     where books.id =?', [book_id])
      rows = cursor.fetchall()
      # на самом деле тут одна запись
      for row in rows:
          widget.builder.get_object("tfISBN").set_text(row[0])
          widget.builder.get_object("tfAuthor").set_text(row[1])
          widget.builder.get_object("tfTitle").set_text(row[2])
          break
      widget.book_dlg.show()
      widget.book_dlg.run()
      widget.book_dlg.hide()
      
   def onEditSave(widget, event):
       try:
           isbn = widget.builder.get_object("tfISBN").get_text()
           author = widget.builder.get_object("tfAuthor").get_text()
           title = widget.builder.get_object("tfTitle").get_text()
           book_id = int(widget.builder.get_object("tfBookId").get_text())
           try:
               # обновить в базе
               cursor = widget.connect.cursor()
               cursor.execute( 'update books set isbn=?, author=?, title=? where id=?', (isbn, author, title, book_id) )
               cursor.close()
               widget.connect.commit()
               # обновить на экране (в модели)
               widget.model_edit.set(widget.iter_edit, F_NAME, author + ', ' + title)
               widget.model_edit.set(widget.iter_edit, F_ISBN, isbn)
           except sqlite3.Error as e:
               print (e.args[0])
               print (u'Сбой обновления книги в базе')
       except:
           print (u'Сбой чтения значений из полей')

   def onRowActivated(widget, cell, point, render_cell):
      model = widget.treeview.get_model()
      # узел дерева второго уровня вложенности - ссылка на книгу
      if len(point) == 2:
         try:
            cell.set_text(model.get_value(model.get_iter(point), F_NAME))
         except:
            print (u'Сбой в таблице!')
      elif len(point) == 1:
         widget.onEditBook(None)
         
   def onCursorChanged(widget, treeview):
      gtk_tree_selection = treeview.get_selection()
      if gtk_tree_selection.count_selected_rows() > 0:
         (model, iter_sel) = gtk_tree_selection.get_selected()
         # брать только книги, а не ссылки
         if len(model.get_path(iter_sel)) == 1:
            book_id = model.get_value(iter_sel, F_BOOK_ID)
            if widget.book_id != book_id:
               title = model.get_value(iter_sel, F_NAME)
               widget.update_graphs(book_id, title)
               widget.book_id = book_id
   
   def update_graphs(widget, book_id, title):
      try:
         for ax in widget.figure.axes:
            widget.figure.delaxes(ax)
      except:
          pass

      cursor = widget.connect.cursor()
      links = cursor.execute('select links.id, links.urlname \
         from links \
         join books on books.id=links.book\
         where books.id=?', [book_id] )
      ids = []
      for link in links:
         try:
             site_name = link[1].split('/')[2].replace('www.', '').replace('.ru', '')
         except:
             site_name = link[1]
         ids.append([link[0], site_name])

      min_price = 0
      cursor = widget.connect.cursor()
      query = 'select price, timestamp \
               from prices where link = ? \
               order by timestamp desc \
               LIMIT 200'
      for link in ids:
         rows = cursor.execute( query, [link[0]] )
         rows = cursor.fetchall()
         x = []
         y = []
         for row in rows:
            timestamp = row[1]
            timestamp1 = datetime.datetime(*time.strptime(row[1], "%Y-%m-%d %H:%M:%S")[0:5])
            #timestamp = matplotlib.dates.date2num(timestamp1)
            x.append(timestamp1)
            y.append(row[0])
            if int(row[0]) < min_price or min_price == 0:
                min_price = int(row[0])
                min_timestamp = timestamp1
         plt.plot(x, y, label=link[1])
      print (min_price, min_timestamp)
      plt.legend(loc='upper left')
      plt.grid(True)
      plt.xlabel(u'Дата')
      plt.ylabel(u'Цена')
      plt.title(title)
#         plt.annotate('min', xy=(min_price, min_timestamp), 
#                      xytext=(0.5,0.5),textcoords='offset points', 
#                      arrowprops=dict(facecolor='black', shrink=0.05))
      #plt.show()
      widget.figure.canvas.draw()

   def filtering(self, model, path, iter, user_data):
       # проверять "корни" дерева - книги
       if model.iter_depth(iter) == 0:
           title = model.get_value(iter, F_NAME).lower()
           if title.find(user_data) == -1:
               model.set_value(iter, F_IS_VISIBLE, False)
           else:
               model.set_value(iter, F_IS_VISIBLE, True)

   def onFind(widget, event):
      try:
         widget.model.foreach(widget.filtering, event.get_text().lower())
      except:
         pass

   def onFindReset(widget, event):
      try:
         widget.model.foreach(widget.filtering, u'')
      except:
         pass

   def onCheckButton(widget, event, data=None):
      url_name = event.get_text()
      (title, author, serial, isbn, desc2, price) = test_url(url_name)
      if widget.test_dlg == None:
         widget.builder.add_from_file("glade/test_link_dialog.glade")
         widget.test_dlg = widget.builder.get_object("test_link_dialog")
      widget.builder.get_object("tfTitle").set_text(title)
      widget.builder.get_object("tfAuthor").set_text(author)
      widget.builder.get_object("tfSerial").set_text(serial)
      widget.builder.get_object("tfISBN").set_text(isbn)
      widget.builder.get_object("tfDesc2").set_text(desc2)
      widget.builder.get_object("tfPrice").set_text(price)
      widget.test_dlg.show()
      widget.test_dlg.run()
      widget.test_dlg.hide()

   def getBooks(self, cursor0):
      # перебор книг в базе
      cursor0.execute('select pr.*, ifnull(prices.price, 0) price, \
                        case pr.ptime when 0 then "" else strftime("%Y-%m-%d", pr.ptime) end shorttime, \
                        case pr.ptime when 0 then 0 else strftime("%s", pr.ptime) end seconds, \
                        strftime("%s", datetime("now")) now, \
                        ifnull(links.state, 0) state \
                     from links \
                     left join (select books.id, \
                            books.isbn, \
                            books.author || ", " || books.title name, \
                            links.urlname, \
                            min(ifnull(prices.price, 0)) pmin, \
                            max(ifnull(prices.price, 0)) pmax, \
                            max(ifnull(prices.timestamp, 0)) ptime, \
                            links.id link \
                          from links \
                            left join prices on prices.link=links.id \
                            join books on links.book=books.id \
                          group by books.id, books.isbn, books.author, books.title, links.urlname, links.id \
                          ) pr on links.id=pr.link \
                     left join prices on links.id=prices.link \
                     where (prices.timestamp=pr.ptime or pr.ptime = 0) \
                     order by pr.name, prices.price')
#      cursor.execute('select pr.*, prices.price, \
#                        strftime("%Y-%m-%d", pr.ptime) shorttime, \
#                        strftime("%s", pr.ptime) seconds, \
#                        strftime("%s", datetime("now")) now \
#                     from prices, \
#                     (select books.id, \
#                        books.isbn, \
#                        books.author || ", " || books.title name, \
#                        links.urlname, \
#                        min(prices.price) pmin, \
#                        max(prices.price) pmax, \
#                        ifnull(max(prices.timestamp),0) ptime, \
#                        links.id link \
#                     from links \
#                        join prices on prices.link=links.id \
#                        join books on links.book=books.id \
#                     group by books.id, books.isbn, books.author, books.title, links.urlname, links.id ) pr \
#                     where prices.link=pr.link and prices.timestamp=pr.ptime \
#                     order by pr.name, prices.price')
      return cursor0.fetchall()

   def loadModel(self):
      rows = self.getBooks(self.connect.cursor())
      books_id = -1
      iter = None
      fg_gray = Gdk.color_parse('gray')
      fg_red = Gdk.color_parse('red')
      pix_ozon = GdkPixbuf.Pixbuf.new_from_file('pics/ozon-16.png')
      pix_readru = GdkPixbuf.Pixbuf.new_from_file('pics/readru-16.png')
      pix_myshop = GdkPixbuf.Pixbuf.new_from_file('pics/myshop-16.png')
      pix_ukazka = GdkPixbuf.Pixbuf.new_from_file('pics/ukazka-16.png')
      pix_bolero = GdkPixbuf.Pixbuf.new_from_file('pics/bolero-16.png')
      pix_labiru = GdkPixbuf.Pixbuf.new_from_file('pics/labiru-16.png')
      pix_bgshop = GdkPixbuf.Pixbuf.new_from_file('pics/bgshop-16.png')
      pix_setbook = GdkPixbuf.Pixbuf.new_from_file('pics/setbook-16.png')
      pix_knigaru = GdkPixbuf.Pixbuf.new_from_file('pics/knigaru-16.png')
      pix_booksru = GdkPixbuf.Pixbuf.new_from_file('pics/booksru-16.png')
      hasGraph = 0
      for row in rows:
         url_name = row[3]
#         print ('=====')
#         for cell in row: print (cell)
         if url_name.find(u'ozon.ru') > -1:
            pix = pix_ozon
         elif url_name.find(u'read.ru') > -1:
            pix = pix_readru
         elif url_name.find(u'my-shop.ru') > -1:
            pix = pix_myshop
         elif url_name.find(u'ukazka.ru') > -1:
            pix = pix_ukazka
         elif url_name.find(u'bolero.ru') > -1:
            pix = pix_bolero
         elif url_name.find(u'labirint.ru') > -1:
            pix = pix_labiru
         elif url_name.find(u'bgshop.ru') > -1:
            pix = pix_bgshop
         elif url_name.find(u'setbook.ru') > -1:
            pix = pix_setbook
         elif url_name.find(u'kniga.ru') > -1:
            pix = pix_knigaru
         elif url_name.find(u'books.ru') > -1:
            pix = pix_booksru
         else:
            pix = None
         bottom_price = ''
         fg_pricecurrent = None
         # давно не обновлявшиеся книги выделить серым цветом
         # 11 - текущее время
         if (int(row[11]) - int(row[10]))/60/60/24/14 > 0:
            fg_timestamp = fg_gray
         else:
            fg_timestamp = None
            # если текущая цена совпадает с минимальной, 
            # то выделить красным цветом и иконкой со стрелкой
            if row[8]==row[4]:
               bottom_price = 'gtk-go-down'
               fg_pricecurrent = fg_red
         # "покинули" текущую книгу
         if books_id != row[0] :
            is_visible = True

#            print (type(row[2]), type(row[4]), type(row[5]), type(row[8]), type(row[0]), type(bottom_price), type(pix), type(row[9]), type(row[10]), type(fg_timestamp), type(fg_pricecurrent), type(row[1]), type(row[7]))
            
            
            iter = self.model.append(None, [row[2], row[4], row[5], row[8], row[0], bottom_price, pix, row[9], int(row[10]), fg_timestamp, fg_pricecurrent, row[1], row[7], is_visible])
#            iter = self.model.append(None, [row[2], row[4], row[5], row[8], row[0], bottom_price, pix, row[9], int(row[10]), fg_timestamp, fg_pricecurrent, row[1], row[7], is_visible, row[12]])
            books_id = row[0]
         # на первом проходе вывести график
         if hasGraph == 0:
            self.update_graphs(books_id, row[2])
            hasGraph = 1
         else:
            imin, imax, iprice, iseconds = self.model.get(iter, 
                                                          F_PRICE_MIN, 
                                                          F_PRICE_MAX, 
                                                          F_PRICE_CUR, F_UNIXSEC)

# можно ставить картинкой магазин с минимальной ценой за все время            
#            if row[4] < imin:
#               self.model.set(iter, F_FAVICON, pix)

            # если где-либо есть не нулевая цена, то поставить картинку соответствующего магазина
            # (т.к. цены сортированы в порядке убывания!)
            if row[4] != 0 and imin == 0:
               self.model.set(iter, F_FAVICON, pix)
            if row[4] > 0:
                if imin == 0:
                    imin = row[4]
                else:
                    imin = min(imin, row[4])
            if row[5] > 0:
                if imax == 0:
                    imax = row[5]
                else:
                    imax = max(imax, row[5])
            if row[8] > 0:
                if iprice == 0:
                    iprice = row[8]
                else:
                    iprice = min(iprice, row[8])
            self.model.set(iter, 
                           F_PRICE_MIN, imin, 
                           F_PRICE_MAX, imax, 
                           F_PRICE_CUR, iprice)
            # row[11] - текущее время в секундах
            if iseconds > 0:
                if iprice == imin and (int(row[11]) - int(iseconds))/60/60/24/5 <= 0:
                   self.model.set(iter, F_SITEICON, 'gtk-go-down')
                else:
                   self.model.set(iter, F_SITEICON, '')
            else:
                self.model.set(iter, 
                               F_UNIXSEC, int(row[10]), 
                               F_TIMESTAMP, row[9], 
                               F_FG_TIMESTAMP, None)
#         self.model.append(iter, [url_name, row[4], row[5], row[8], row[0], bottom_price, pix, row[9], int(row[10]), fg_timestamp, fg_pricecurrent, row[1], row[7], True, row[12]])
         self.model.append(iter, [url_name, row[4], row[5], row[8], row[0], bottom_price, pix, row[9], int(row[10]), fg_timestamp, fg_pricecurrent, row[1], row[7], True])
         if fg_pricecurrent != None: self.model.set(iter, F_FG_PRICE_CUR, fg_pricecurrent)
       
   def __init__(self):
      self.builder = Gtk.Builder()
      # Загружаем интерфейс
      self.builder.add_from_file("glade/gpryced.glade")
      # присоединяем сигналы
      self.builder.connect_signals(self)

      self.main_window = self.builder.get_object("main_window")
      self.main_window.connect("destroy", self.close_app)

      self.builder.get_object("toolbuttonPaste").set_sensitive(0)
      self.iter_src = None

      self.test_dlg = None
      self.book_dlg = None

      self.treeview = self.builder.get_object("treeview1")
      self.model = self.builder.get_object("treestore1")

#      now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      self.connect = connect_to_base()

      self.graphview = self.builder.get_object("box_graph")
      self.figure = plt.figure()
      self.figure.autofmt_xdate()
      self.canvas = FigureCanvasGTK(self.figure) # a gtk.DrawingArea
      # почему-то в настройке отступ от нижнего края не устанавливается,
      # поэтому здесь выставляю его принудительно
      self.figure.subplots_adjust(bottom=0.1)
#      widget.canvas.set_size_request(800, 600)
      self.canvas.show()
      self.toolbar = NavigationToolbar(self.canvas, self.main_window)
      self.graphview.pack_start(self.canvas, True, True, 0)
      self.graphview.pack_start(self.toolbar, False, False, 0)
      self.book_id = -1
      
      self.loadModel()

      self.toolbar.show()
      self.figure.canvas.draw()

      # мне не удалось создать внятно фильтр в glade (хотя он там есть), 
      # потому что там нельзя указать колонку видимости 
      # или функцию-обработчик.
      # и в тоже время в коде тоже нельзя выставить на glade-объект 
      # колонку видимости или функцию-обработчик,
      # потому что из TreeStore никак не удалось извлечь объект фильтра
#      self.filter = self.builder.get_object("treemodelfilter1")
      self.filter = self.model.filter_new()
      self.filter.set_visible_column(F_IS_VISIBLE)

      # отображает данные, хранящиеся в list_store1
      self.treeview.set_model(model=self.filter)
      self.main_window.show()

   def close_app(self, widget):
      Gtk.main_quit()

if __name__ == "__main__":
    # признак запуска на windows-python
    if sys.platform.find(u'win') > -1:
       sys.stdout = open('gpryced_stdout.log', 'w')
       sys.stderr = open('gpryced_stderr.log', 'w')
    app = App()
    Gtk.main()
