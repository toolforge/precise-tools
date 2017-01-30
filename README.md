precise-tools
=============

List tools still running on Precise Open Grid Engine exec nodes.

Install
-------
```
$ become precise-tools
$ mkdir -p $HOME/www/python
$ git clone https://phabricator.wikimedia.org/source/tool-precise-tools.git
$HOME/www/python/src
$ virtualenv $HOME/www/python/venv
$ $HOME/www/python/venv/bin/pip install -r
$HOME/www/python/src/requirements.txt
$ webservice uwsgi-python start
```

License
-------
[GNU GPLv3+](//www.gnu.org/copyleft/gpl.html "GNU GPLv3+")
