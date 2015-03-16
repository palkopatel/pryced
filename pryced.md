# Использование #

использование:

`./pryced.py {-a <ссылка на книгу> | -g | -s}`

  * _-a <ссылка на книгу>_ добавить книгу в базу

  * _-t <ссылка на книгу>_ проверить ссылку, не добавляя ее в базу (пока что сделано для отладочных целей)

  * _-g_ получить текущие цены и сохранить их в базу

  * _-s_ показать цены из базы

Данные по ценам хранятся в локальной базе sqlite, которая создается в каталоге программы при первом запуске.

![https://lh3.googleusercontent.com/_ipIDvIJ1jSA/TWBZbsGwL0I/AAAAAAAAAIs/pvQxhZYTJDo/s512/pryced.png](https://lh3.googleusercontent.com/_ipIDvIJ1jSA/TWBZbsGwL0I/AAAAAAAAAIs/pvQxhZYTJDo/s512/pryced.png)