precise-tools
=============

List tools still running on Precise Open Grid Engine exec nodes.

Install
-------

Clone repo and create basic files:
```
bastion$ become precise-tools
tools.precise-tools@bastion:~$ mkdir -p ~/www/python
tools.precise-tools@bastion:~$ git clone https://phabricator.wikimedia.org/source/tool-precise-tools.git ~/www/python/src
tools.precise-tools@bastion:~$ touch ~/redis-prefix.conf
tools.precise-tools@bastion:~$ chmod 600 ~/redis-prefix.conf
```
And edit `~/redis-prefix.conf` with a text editor.

Create virtualenv inside kubernetes:
```
tools.precise-tools@bastion:~$ webservice --backend=kubernetes python2 shell
tools.precise-tools@interactive:~$ virtualenv ~/www/python/venv
tools.precise-tools@interactive:~$ source ~/www/python/venv/bin/activate
(venv)tools.precise-tools@interactive:~$ pip install -U pip
(venv)tools.precise-tools@interactive:~$ pip install -r ~/www/python/src/requirements.txt
```

Back to bastion, start the webservice:
```
tools.precise-tools@bastion:~$ webservice --backend=kubernetes python2 start
```

License
-------
[GNU GPLv3+](//www.gnu.org/copyleft/gpl.html "GNU GPLv3+")
