#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to transform the output from "sjk ttop" into JSON.

This can be used to for example graph the output using jsonplot:

    sjk ttop -p CRATE_PID | tee ttop.txt | ./ttop2json.py | jq  '{ts, gc_time_young, gc_time_old, heap_alloc_rate_mb}' | jq -s '.' | jsonplot --mode lines

(This will block until the Crate process is stopped)

[sjk]: https://github.com/aragozin/jvm-tools
[jsonplot]: https://github.com/mfussenegger/jsonplot (Note that this is very much WIP)


Sample output of sjk ttop:

    2017-06-12T14:31:20.954+0200 Process summary
      process cpu=1.19%
      application cpu=1.07% (user=0.79% sys=0.28%)
      other: cpu=0.11%
      thread count: 106
      GC time=0.00% (young=0.00%, old=0.00%)
      heap allocation rate 929kb/s
      no safe points
    [000107] user= 0.59% sys= 0.29% alloc=  923kb/s - RMI TCP Connection(2)-192.168.43.138
    [000114] user= 0.00% sys= 0.03% alloc=  3770b/s - JMX server connection timeout 114
    [000026] user= 0.00% sys= 0.01% alloc=  2182b/s - elasticsearch[Dent de Crolles][scheduler][T#1]
    [000025] user= 0.00% sys= 0.01% alloc=     0b/s - elasticsearch[Dent de Crolles][[timer]]
    [000078] user= 0.00% sys= 0.00% alloc=     0b/s - elasticsearch[Dent de Crolles][http_server_worker][T#17]
    [000083] user= 0.00% sys= 0.00% alloc=     0b/s - elasticsearch[Dent de Crolles][http_server_worker][T#22]

After transformation:

    {
      "ts": 1497270680.954,
      "proc_cpu": 1.19,
      "app_cpu": "1.07% (user=0.79% sys=0.28%)",
      "other_cpu": 0.11,
      "thread_count": 106,
      "gc_time_young": 0,
      "gc_time_old": 0,
      "heap_alloc_rate_mb": 0.907
    }
"""

import sys
import re
import json
from datetime import datetime


RE_TIME = re.compile('^\d{4}-\d{2}-\d{2}.* Process summary')
RE_GC_YOUNG = re.compile('\(young=(\d+.\d+)%.*')
RE_GC_OLD = re.compile(', old=(\d+.\d+)%.*')
RE_ALLOC_RATE = re.compile('heap allocation rate (\d+)(.*)$')


def break_iterable(iterable, pred):
    sublist = []
    for i in iterable:
        if pred(i):
            yield sublist
            sublist = []
        sublist.append(i)
    yield sublist


def to_mbs_rate(n, unit):
    n = float(n)
    if unit == 'kb/s':
        return round(n / 1024, 3)
    return float(n)


def event2dict(event):
    event = (
        t,
        proc_cpu,
        app_cpu,
        other_cpu,
        thread_count,
        gc_time,
        heap_alloc_rate,
        safe_point_rate,
        safe_point_sync_time) = event
    return {
        'ts': datetime.strptime(t.strip(' Process_summary'), '%Y-%m-%dT%H:%M:%S.%f%z').timestamp(),
        'proc_cpu': float(proc_cpu.split('=', maxsplit=1)[1].rstrip('%')),
        'app_cpu': app_cpu.split('=', maxsplit=1)[1],
        'other_cpu': float(other_cpu.split('=', maxsplit=1)[1].rstrip('%')),
        'thread_count': int(thread_count.split(':', maxsplit=1)[1]),
        'gc_time_young': float(RE_GC_YOUNG.findall(gc_time)[0]),
        'gc_time_old': float(RE_GC_OLD.findall(gc_time)[0]),
        'heap_alloc_rate_mb': to_mbs_rate(*RE_ALLOC_RATE.findall(heap_alloc_rate)[0]),
    }


def main():
    trimmed_lines = (i.rstrip() for i in sys.stdin if i)
    events = break_iterable(trimmed_lines, lambda x: RE_TIME.match(x))
    trimmed_events = (e[0:9] for e in events)
    events_as_dict = (event2dict(e) for e in trimmed_events
                      if len(e) == 9)
    for event in events_as_dict:
        print(json.dumps(event))


if __name__ == "__main__":
    main()
