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

import collections
import datetime
import traceback

import flask

import precise_tools


app = flask.Flask(__name__)


@app.route('/')
def home():
    try:
        # tools will be a structure something like:
        # {
        #     'tool A': {
        #         'jobs': {
        #             'job X': {
        #                 'count': N,
        #                 'last': datetime,
        #             },
        #             'job Y': {
        #                 'count': N,
        #                 'last': datetime,
        #             },
        #             ...
        #         },
        #         'members': [
        #             'user A',
        #             'user B',
        #             ...
        #         ]
        #     },
        #     ...
        # }
        purge = 'purge' in flask.request.args
        tools = None if purge else precise_tools.CACHE.load('maindict')
        if tools is None:
            tools = collections.defaultdict(lambda: {
                'jobs': collections.defaultdict(lambda: {
                    'count': 0,
                    'last': ''}),
                'members': []})

            for rec in precise_tools.tools_from_accounting(7):
                tools[rec[0]]['jobs'][rec[1]]['count'] += rec[2]
                tools[rec[0]]['jobs'][rec[1]]['last'] = (
                    datetime.datetime.fromtimestamp(
                        rec[3]).strftime('%Y-%m-%d %H:%M'))
            for rec in precise_tools.tools_from_grid():
                tools[rec[0]]['jobs'][rec[1]]['count'] += 1
                tools[rec[0]]['jobs'][rec[1]]['last'] = 'Currently running'

            for key, val in precise_tools.tools_members(tools.keys()).items():
                tools[key]['members'] = list(val)

            precise_tools.CACHE.save('maindict', tools)

        return flask.render_template('home.html', tools=tools)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == '__main__':
    app.run()

# vim:sw=4:ts=4:sts=4:et:
