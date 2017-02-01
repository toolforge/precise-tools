#!/usr/bin/env python2
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

import traceback

import flask

import precise_tools


app = flask.Flask(__name__)


@app.route('/')
def home():
    try:
        cached = 'purge' not in flask.request.args
        ctx = precise_tools.get_view_data(days=7, cached=cached)
        return flask.render_template('home.html', **ctx)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == '__main__':
    app.run()

# vim:sw=4:ts=4:sts=4:et:
