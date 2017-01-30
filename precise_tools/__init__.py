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

import datetime
import httplib
import json

from . import utils

ACCOUNTING_FIELDS = [
    'qname', 'hostname', 'group', 'owner', 'job_name', 'job_number',
    'account', 'priority', 'submission_time', 'start_time', 'end_time',
    'failed', 'exit_status', 'ru_wallclock', 'ru_utime', 'ru_stime',
    'ru_maxrss', 'ru_ixrss', 'ru_ismrss', 'ru_idrss', 'ru_isrss', 'ru_minflt',
    'ru_majflt', 'ru_nswap', 'ru_inblock', 'ru_oublock', 'ru_msgsnd',
    'ru_msgrcv', 'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw', 'project',
    'department', 'granted_pe', 'slots', 'task_number', 'cpu', 'mem', 'io',
    'category', 'iow', 'pe_taskid', 'maxvemem', 'arid', 'ar_submission_time',
]


def tools_from_accounting(days):
    delta = datetime.timedelta(days=days)
    cutoff = int(utils.totimestamp(datetime.datetime.now() - delta))
    tools = set()
    for line in utils.lines_in_last_n_bytes('/data/project/.system/accounting',
                                            400 * 45000 * days):
        parts = line.split(':')
        job = dict(zip(ACCOUNTING_FIELDS, parts))
        if int(job['end_time']) < cutoff:
            continue
        if 'release=precise' in job['category'] and job['owner'] not in tools:
            tools.add(normalize_toolname(job['owner']))
    return tools


def is_precise_host(hostname):
    if hostname[-4:].startswith('12'):
        return True


def tools_from_grid():
    tools = []
    conn = httplib.HTTPConnection('tools.wmflabs.org')
    conn.request(
        'GET', '/gridengine-status',
        headers={
            'User-Agent': 'https://tools.wmflabs.org/precise-tools/'
        }
    )
    res = conn.getresponse().read()
    if not res:
        return []
    grid_info = json.loads(res)['data']['attributes']
    for host, info in grid_info.iteritems():
        if is_precise_host(host):
            if info['jobs']:
                tools.extend([normalize_toolname(job['job_owner'])
                              for job in info['jobs'].values()])
    return tools


def normalize_toolname(name):
    if name.startswith('tools.'):
        return name[6:]
    # else None -- we ignore non-tool accounts like 'root'
