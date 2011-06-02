#!/usr/bin/env python2
# -*- coding: utf-8

try:
    import sys, pygtk
    pygtk.require('2.0')
except:
    print u'Не удалось импортировать модуль PyGTK'
    sys.exit(1)

import gtk
import datetime # для datetime.datetime.now()
from pryced import *
# эти библиотеки включены для сборки в exe'шника в windows
import cairo, gio, pango, atk, pangocairo

class App(object):
   
   def onCut(widget, event):
      model, widget.iter_src = event.get_selected()
      widget.builder.get_object("toolbuttonPaste").set_sensitive(1)
      
   def onPaste(widget, event):
         # копировать нечего
         if widget.iter_src == None:
            return
         model, iter_dest = event.get_selected()
         #  только  нужное место
         if len(model.get_path(iter_dest)) != 1:
            return
         # не вставлять в сво же родителя
         if model.iter_parent(widget.iter_src) != iter_dest :
            try:
               book_id = model[iter_dest][4]
               link_id = model[widget.iter_src][12]
               cursor = widget.connect.cursor()
               cursor.execute( 'update links set book=? where id=?', (book_id, link_id) )
               cursor.close()
               widget.connect.commit()
               model.append(iter_dest, model[model.get_path(widget.iter_src)])
               model.remove(widget.iter_src)
               widget.iter_src = None
               widget.builder.get_object("toolbuttonPaste").set_sensitive(0)
            except sqlite3.Error, e:
               print u'Ошибка при выполнении запроса:', e.args[0]
      
   def onRowActivated(widget, cell, point, render_cell):
      if len(point) == 2:
         try:
            cell.set_text(widget.model.get_value(widget.model.get_iter(point), 0))
         except:
            print 'Сбой в таблице!'
   
   def onCheckButton(widget, event, data=None):
      url_name = event.get_text()
      (title, author, serial, isbn, desc2, price) = test_url(url_name)
      if widget.test_dlg == None:
         widget.test_dlg = widget.builder.get_object("test_link_dialog")
      widget.builder.get_object("tfTitle").set_text(title)
      widget.builder.get_object("tfAuthor").set_text(author)
      widget.builder.get_object("tfSerial").set_text(serial)
      widget.builder.get_object("tfISBN").set_text(isbn)
      widget.builder.get_object("tfDesc2").set_text(desc2)
      widget.builder.get_object("tfPrice").set_text(price)
      widget.test_dlg.show()

   def onCloseDlg(widget, event, data=None):
#      widget.test_dlg.hide_all()
      widget.test_dlg.hide()
      if isinstance(event, gtk.Dialog):
         widget.test_dlg = None

   def __init__libglade(self):
      # Загружаем файл интерфейса
      self.gladefile = "glade/gpryced.glade"
      # дерево элементов интерфейса
      self.widgetsTree = gtk.glade.XML(self.gladefile)
      # Словарик, задающий связи событий с функциями-обработчиками
#      dic = {
#        "button1_clicked_cb" : self.text_operation,
#        "button2_clicked_cb": self.text_operation,
#	   }
      # Магическая команда, соединяющая сигналы с обработчиками
#      self.widgetsTree.signal_autoconnect(dic)
      # Соединяем событие закрытия окна с функцией завершения приложения
      self.window = self.widgetsTree.get_widget("main_window")
      if (self.window):
         self.window.connect("destroy", self.close_app)
      # А это уже логика приложения. Задём маршруты обработки текста для каждой кнопки.
      # Первый элемент - имя виджета-источника текста, второй - имя виджета-получателя
#      self.routes = {'button1': ('textview1','textview2'),
#                     'button2': ('textview2','textview1')}

   def __init__(self):
      self.builder = gtk.Builder()
      # Загружаем наш интерфейс
      self.builder.add_from_file("glade/gpryced.glade")
      # присоединяем сигналы
      self.builder.connect_signals(self)

      self.main_window = self.builder.get_object("main_window")
      self.main_window.connect("destroy", self.close_app)
      
      self.builder.get_object("toolbuttonPaste").set_sensitive(0)
      self.iter_src = None

      self.test_dlg = self.builder.get_object("test_link_dialog")
      self.test_dlg.set_deletable(0)
#      self.test_dlg.connect("destroy", self.onCloseDlg)
   
      self.treeview = self.builder.get_object("treeview1")
      self.model = self.builder.get_object("treestore1")

      now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      self.connect = connect_to_base()
      cursor = self.connect.cursor()
      # перебор книг в базе
      cursor.execute('select pr.*, prices.price, \
                        strftime("%Y-%m-%d", pr.ptime) shorttime, \
                        strftime("%s", pr.ptime) seconds, \
                        strftime("%s", datetime("now")) now \
                     from prices, \
                     (select books.id, \
                        books.isbn, \
                        books.author || ", " || books.title name, \
                        links.urlname, \
                        min(prices.price) pmin, \
                        max(prices.price) pmax, \
                        max(prices.timestamp) ptime, \
                        links.id link \
                     from prices \
                        join links on prices.link=links.id \
                        join books on links.book=books.id \
                     group by books.id, books.isbn, books.author, books.title, links.urlname, links.id ) pr \
                     where prices.link=pr.link and prices.timestamp=pr.ptime \
                     order by pr.name, prices.price')
      rows = cursor.fetchall()
      books_id = -1
      iter = None
      fg_gray = gtk.gdk.Color('gray')
      fg_red = gtk.gdk.Color('red')
      pix_ozon = gtk.gdk.pixbuf_new_from_file('pics/ozon-16.png')
      pix_readru = gtk.gdk.pixbuf_new_from_file('pics/readru-16.png')
      pix_myshop = gtk.gdk.pixbuf_new_from_file('pics/myshop-16.png')
      pix_ukazka = gtk.gdk.pixbuf_new_from_file('pics/ukazka-16.png')
      cursor_link = self.connect.cursor()
      for row in rows:
         url_name = row[3]
         if url_name.find(u'ozon.ru') > -1:
            pix = pix_ozon
         elif url_name.find(u'read.ru') > -1:
            pix = pix_readru
         elif url_name.find(u'my-shop.ru') > -1:
            pix = pix_myshop
         elif url_name.find(u'ukazka.ru') > -1:
            pix = pix_ukazka
         else:
            pix = None
         if row[8]==row[4]:
            bottom_price = 'gtk-go-down'
            fg_pricecurrent = fg_red
         else:
            bottom_price = ''
            fg_pricecurrent = None
         if (long(row[11]) - long(row[10]))/60/60/24/14 > 0:
            fg_timestamp = fg_gray
         else:
            fg_timestamp = None
         if books_id != row[0] :
            iter = self.model.append(None, [row[2], row[4], row[5], row[8], row[0], bottom_price, pix, row[9], long(row[10]), fg_timestamp, fg_pricecurrent, row[1], row[7]])
            books_id = row[0]
         else:
            imin, imax, iprice, iseconds = self.model.get(iter, 1, 2, 3, 8)
            if row[4] < imin:
               self.model.set(iter, 6, pix)
            imin = min(imin, row[4])
            imax = max(imax, row[5])
            iprice = min(iprice, row[8])
            self.model.set(iter, 1, imin, 2, imax, 3, iprice)
            if iprice == imin:
               self.model.set(iter, 5, 'gtk-go-down')
            else: 
               self.model.set(iter, 5, '')
         self.model.append(iter, [url_name, row[4], row[5], row[8], row[0], bottom_price, pix, row[9], long(row[10]), fg_timestamp, fg_pricecurrent,row[1], row[7]])
         if fg_pricecurrent != None: self.model.set(iter, 10, fg_pricecurrent)

      # отображает данные, хранящиеся в list_store1
      self.treeview.set_model(model=self.model)
      self.main_window.show_all()

   def close_app(self, widget):
      gtk.main_quit()

if __name__ == "__main__":
    # признак запуска на windows-python
    if sys.platform.find(u'win') > -1:
       sys.stdout = open('gpryced_stdout.log', 'w')
       sys.stderr = open('gpryced_stderr.log', 'w')
    app = App()
    gtk.main()
