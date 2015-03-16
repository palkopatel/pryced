# Требования к установке в Linux #

## Требует библиотек python 2 ##
  * python-beautifulsoup (для разбора html-кода)
  * python-pysqlite (для работы с sqlite3)

## Требует сторонних пакетов ##
  * matplotlib для построения графиков
  * nimpy для преобразования при работе с графиками
  * ~~gocr для распознавания ISBN на read.ru, где он "спрятан" в картинке~~
  * ~~netpbm для преобразования png в pnm, которые принимает на вход gocr~~

# Ссылки для загрузки в MS Windows #
  * сам python 2 http://www.python.org/download/releases/2.7.1/
Скачать, установить. Можно поменять каталог установки на что-нибудь иное, а не `C:\Python\`
  * python-beautifulsoup http://www.crummy.com/software/BeautifulSoup/#Download
Скачать, распаковать в любое место, установить. Чтобы установить, во-первых, `python setup.py build`, во-вторых, `python setup.py install`
  * nimpy http://sourceforge.net/projects/numpy/files/NumPy/1.6.1/numpy-1.6.1-win32-superpack-python2.7.exe/download . Скачать, установить.
  * matplotlib http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.0.1/matplotlib-1.0.1.win32-py2.7.exe/download . Скачать, установить.
  * ~~поддержка utf8 в консоли через pywin32 http://sourceforge.net/projects/pywin32/files/pywin32/ Далее выбрать последнюю сборку и инсталятор для python 2.7~~
  * ~~netpbm брать с http://netpbm.sourceforge.net/ Здесь можно сразу выбрать последнюю версию: http://sourceforge.net/projects/gnuwin32/files/netpbm/~~
~~Скачать, установить. Затем прописать путь к конвертеру в переменную среды PATH. Обычно, это `C:\Program Files\GnuWin32\bin`~~
  * ~~gocr взять отсюда http://jocr.sourceforge.net/download.html~~
~~Скачать, распаковать, проследить, чтобы назывался просто gocr.exe. Можно для удобства положить в путь к утилитам из netpbm~~