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

import ldap3
import requests

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

CACHE = utils.Cache()


def tools_from_accounting(remove_migrated=True, cached=False):
    """Get a list of (tool, job name, count, last) tuples for jobs running on
    trusty exec nodes in the last 7 days."""
    p = {'purge': 1} if not cached else None
    r = requests.get('https://tools.wmflabs.org/grid-jobs/json', params=p)
    jobs = r.json()['tools']

    if remove_migrated:
        r = requests.get('https://tools.wmflabs.org/sge-jobs/json')
        for tool, data in r.json()['tools'].items():
            for name in data['jobs'].keys():
                try:
                    del jobs[tool][name]
                except KeyError:
                    pass

    return jobs


def gridengine_status(url, cached=False):
    """Get a list of (tool, job name, host) tuples for jobs currently running
    on the given grid."""
    p = {'purge': 1} if not cached else None
    r = requests.get(url,  params=p)
    grid_info = r.json()['data']['attributes']

    tools = []
    for host, info in grid_info.items():
        if info['jobs']:
            tools.extend([
                (
                    normalize_toolname(job['job_owner']),
                    job['job_name'],
                    host
                )
                for job in info['jobs'].values()
            ])

    return tools


def normalize_toolname(name):
    if name.startswith('tools.'):
        return name[6:]
    # else None -- we ignore non-tool accounts like 'root'


def tools_members(tools):
    """
    Return a dict that has members of a tool associated with each tool
    Ex:
    {'musikbot': ['musikanimal'],
     'ifttt': ['slaporte', 'mahmoud', 'madhuvishy', 'ori']}
    """
    members = collections.defaultdict(set)
    with utils.ldap_conn() as conn:
        for tool in tools:
            conn.search(
                'ou=servicegroups,dc=wikimedia,dc=org',
                '(cn=tools.{})'.format(tool),
                ldap3.SUBTREE,
                attributes=['member', 'cn'],
                time_limit=5
            )
            for resp in conn.response:
                attributes = resp.get('attributes')
                for member in attributes.get('member', []):
                    uid = utils.uid_from_dn(member)
                    if uid.startswith('tools.'):
                        # Expand nested tools
                        nested = uid[6:]
                        members[tool].update(tools_members([nested])[nested])
                    else:
                        members[tool].add(uid)
    return members


def get_view_data(days=7, cached=True, remove_migrated=True):
    """Get a structured collection of data about tools that are running on
    precise grid nodes.

    Return value will be a structure something like:
        {
            'generated': datetime,
            'tools': {
                'tool A': {
                    'jobs': {
                        'job X': {
                            'count': N,
                            'last': datetime,
                        },
                        'job Y': {
                            'count': N,
                            'last': datetime,
                        },
                        ...
                    },
                    'members': [
                        'user A',
                        'user B',
                        ...
                    ]
                },
                ...
            },
        }
    """

    cache_key = 'maindict:days={}:remove_migrated={}'.format(
        days, remove_migrated)
    ctx = CACHE.load(cache_key) if cached else None
    if ctx is None:
        date_fmt = '%Y-%m-%d %H:%M'
        tools = tools_from_accounting(remove_migrated, cached)

        if remove_migrated:
            grid_stretch = gridengine_status(
                'https://tools.wmflabs.org/sge-status/api/v1/', cached)
            for tool, name, host in grid_stretch:
                if tool in tools and name in tools[tool]['jobs']:
                    del tools[tool]['jobs'][name]
                    if not tools[tool]['jobs']:
                        del tools[tool]

        grid_trusty = gridengine_status(
            'https://tools.wmflabs.org/gridengine-status/', cached)
        for tool, name, host in grid_trusty:
            if not tool:
                print('Discarding user job: {}@{}'.format(name, host))
                continue

            if tool not in tools:
                tools[tool] = {
                    'jobs': {},
                    'members': [],
                }
            if name not in tools[tool]:
                tools[tool][name] = {
                    'count': 0,
                    'last': '',
                }
            tools[tool]['jobs'][name]['count'] += 1
            tools[tool]['jobs'][name]['last'] = 'Currently running'

        for key, val in tools_members(tools.keys()).items():
            tools[key]['members'] = list(val)

        ctx = {
            'generated': datetime.datetime.now().strftime(date_fmt),
            'tools': tools,
        }
        CACHE.save(cache_key, ctx)
    return ctx
