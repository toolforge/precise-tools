# -*- coding: utf-8 -*-
#
# This file is part of precise-tools
# Copyright (C) 2017 Bryan Davis and contributors
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import hashlib
import json
import os
import pwd

import ldap3
import redis


class Cache(object):
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.conn = redis.Redis(host='tools-redis', decode_responses=True)
        u = pwd.getpwuid(os.getuid())
        self.prefix = hashlib.sha1(
            '{}.{}'.format(u.pw_name, u.pw_dir).encode('utf-8')).hexdigest()

    def key(self, val):
        return '%s%s' % (self.prefix, val)

    def load(self, key):
        if self.enabled:
            try:
                return json.loads(self.conn.get(self.key(key)) or '')
            except ValueError:
                return None
        else:
            return None

    def save(self, key, data, expiry=3600):
        if self.enabled:
            real_key = self.key(key)
            self.conn.setex(real_key, expiry, json.dumps(data))


def ldap_conn():
    """
    Return a ldap connection

    Return value can be used as a context manager
    """
    servers = ldap3.ServerPool([
        ldap3.Server('ldap-labs.eqiad.wikimedia.org'),
        ldap3.Server('ldap-labs.codfw.wikimedia.org'),
    ], ldap3.ROUND_ROBIN, active=True, exhaust=True)
    return ldap3.Connection(servers,
                            read_only=True,
                            auto_bind=True)


def uid_from_dn(dn):
    keys = dn.split(',')
    uid_key = keys[0]
    uid = uid_key.split('=')[1]
    return uid
