# -*- coding: utf-8 -*-
from typing import Dict, Any

from crate.client.connection import connect
from crate.client.cursor import Cursor

SEGMENTS_STATS_STMT = '''
SELECT
    count(*) as cnt,
    sum(size) / 1000^2 as size,
    min(size) / 1000^2 as min_size,
    max(size) / 1000^2 as max_size,
    avg(size) / 1000^2 as avg_size
FROM
    sys.segments
WHERE
    table_schema NOT IN ('sys', 'blob', 'pg_catalog', 'information_schema')
  AND
    primary = true
'''

SHARDS_STATS_STMT = '''
SELECT
    sum(flush_stats['count']) as flush_count,
    sum(flush_stats['periodic_count']) as flush_periodic_count,
    sum(flush_stats['total_time_ns']) / 1000^2 as flush_time,
    min(flush_stats['total_time_ns']) / 1000^2 as flush_time_min,
    max(flush_stats['total_time_ns']) / 1000^2 as flush_time_max,
    avg(flush_stats['total_time_ns']) / 1000^2 as flush_time_avg,

    sum(refresh_stats['count']) as refresh_count,
    sum(refresh_stats['pending_count']) as refresh_pending_count,
    sum(refresh_stats['total_time_ns']) / 1000^2 as refresh_time,
    min(refresh_stats['total_time_ns']) / 1000^2 as refresh_time_min,
    max(refresh_stats['total_time_ns']) / 1000^2 as refresh_time_max,
    avg(refresh_stats['total_time_ns']) / 1000^2 as refresh_time_avg,

    sum(merge_stats['count']) as merge_count,
    sum(merge_stats['total_num_docs']) as merge_num_docs,
    sum(merge_stats['total_size_bytes']) / 1000^2 as merge_size,
    sum(merge_stats['total_time_ms']) as merge_time,
    min(merge_stats['total_time_ms']) as merge_time_min,
    max(merge_stats['total_time_ms']) as merge_time_max,
    avg(merge_stats['total_time_ms']) as merge_time_avg,
    sum(merge_stats['total_throttled_time_ms']) as merge_throttled_time,
    min(merge_stats['total_throttled_time_ms']) as merge_throttled_time_min,
    max(merge_stats['total_throttled_time_ms']) as merge_throttled_time_max,
    avg(merge_stats['total_throttled_time_ms']) as merge_throttled_time_avg,
    sum(merge_stats['current_count']) as merge_current_count,
    sum(merge_stats['current_num_docs']) as merge_current_num_docs,
    sum(merge_stats['current_size_bytes']) / 1000^2 as merge_current_size,
    sum(merge_stats['bytes_per_sec_auto_throttle']) / 1000^2 as merge_throttle,
    
    sum(translog_stats['size']) / 1000^2 as translog_size,
    min(translog_stats['size']) / 1000^2 as translog_size_min,
    max(translog_stats['size']) / 1000^2 as translog_size_max,
    avg(translog_stats['size']) / 1000^2 as translog_size_avg,
    sum(translog_stats['uncommitted_size']) / 1000^2 as translog_uncommitted_size,
    min(translog_stats['uncommitted_size']) / 1000^2 as translog_uncommitted_size_min,
    max(translog_stats['uncommitted_size']) / 1000^2 as translog_uncommitted_size_max,
    avg(translog_stats['uncommitted_size']) / 1000^2 as translog_uncommitted_size_avg,
    sum(translog_stats['number_of_operations']) as translog_ops,
    min(translog_stats['number_of_operations']) as translog_ops_min,
    max(translog_stats['number_of_operations']) as translog_ops_max,
    avg(translog_stats['number_of_operations']) as translog_ops_avg,
    sum(translog_stats['uncommitted_operations']) as translog_uncommitted_ops,
    min(translog_stats['uncommitted_operations']) as translog_uncommitted_ops_min,
    max(translog_stats['uncommitted_operations']) as translog_uncommitted_ops_max,
    avg(translog_stats['uncommitted_operations']) as translog_uncommitted_ops_avg

FROM
    sys.shards
WHERE
    primary = true
'''


def report_indexing_stats(indexing_metrics_v1: Dict[str, Any],
                          indexing_metrics_v2: Dict[str, Any]):
    print("")
    print("Indexing statistics across all primary shards")
    segments_metrics_v1 = indexing_metrics_v1.get('segments')
    segments_metrics_v2 = indexing_metrics_v2.get('segments')
    if segments_metrics_v1:
        report_segment_stats(segments_metrics_v1, segments_metrics_v2)

    shards_metrics_v1 = indexing_metrics_v1.get('shards')
    shards_metrics_v2 = indexing_metrics_v2.get('shards')
    if shards_metrics_v1:
        report_shard_stats(shards_metrics_v1, shards_metrics_v2)


def report_segment_stats(segments_metrics_v1: Dict[str, Any], segments_metrics_v2: Dict[str, Any]):
    cnt_v1 = segments_metrics_v1["cnt"]
    size_v1 = segments_metrics_v1["size"]
    min_v1 = segments_metrics_v1["min_size"]
    max_v1 = segments_metrics_v1["max_size"]
    avg_v1 = segments_metrics_v1["avg_size"]
    cnt_v2 = segments_metrics_v2["cnt"]
    size_v2 = segments_metrics_v2["size"]
    min_v2 = segments_metrics_v2["min_size"]
    max_v2 = segments_metrics_v2["max_size"]
    avg_v2 = segments_metrics_v2["avg_size"]
    print(f''' Segments
     |        |                Size (MB)        
     |    cnt |      sum      avg      min      max
  V1 | {cnt_v1:6.0f} | {size_v1:8.2f} {avg_v1:8.2f} {min_v1:8.2f} {max_v1:8.2f}
  V2 | {cnt_v2:6.0f} | {size_v2:8.2f} {avg_v2:8.2f} {min_v2:8.2f} {max_v2:8.2f}
    ''')


def report_shard_stats(shards_metrics_v1: Dict[str, Any], shards_metrics_v2: Dict[str, Any]):
    flush_stats = []
    for m in (shards_metrics_v1, shards_metrics_v2):
        cnt = m['flush_count']
        cnt_periodic = m['flush_periodic_count']
        time = m['flush_time']
        time_avg = m['flush_time_avg']
        time_min = m['flush_time_min']
        time_max = m['flush_time_max']
        flush_stats.append(
            f'{cnt:5.0f} {cnt_periodic:10.0f} | {time:10.2f} {time_avg:10.2f} {time_min:10.2f} {time_max:10.2f}'
        )

    print(f''' Flush                   
     |      Counts      |                   Times (sec)                
     | total   periodic |        sum        avg        min        max 
  V1 | {flush_stats[0]}
  V2 | {flush_stats[1]} 
    ''')

    refresh_stats = []
    for m in (shards_metrics_v1, shards_metrics_v2):
        cnt = m['refresh_count']
        cnt_pending = m['refresh_pending_count']
        time = m['refresh_time']
        time_avg = m['refresh_time_avg']
        time_min = m['refresh_time_min']
        time_max = m['refresh_time_max']
        refresh_stats.append(
            f'{cnt:5.0f} {cnt_pending:10.0f} | {time:10.2f} {time_avg:10.2f} {time_min:10.2f} {time_max:10.2f}'
        )

    print(f''' Refresh 
     |      Counts      |                   Times (sec)                
     | total    pending |        sum        avg        min        max 
  V1 | {refresh_stats[0]}
  V2 | {refresh_stats[1]} 
    ''')

    merge_stats = []
    for m in (shards_metrics_v1, shards_metrics_v2):
        cnt = m['merge_count']
        curr_cnt = m['merge_current_count']
        time = m['merge_time']
        time_min = m['merge_time_min']
        time_max = m['merge_time_max']
        time_avg = m['merge_time_avg']
        time_throttle = m['merge_throttled_time']
        time_throttle_min = m['merge_throttled_time_min']
        time_throttle_max = m['merge_throttled_time_max']
        time_throttle_avg = m['merge_throttled_time_avg']
        cnt_str = f'{cnt:5.0f} {curr_cnt:8.0f}'
        time_str = f'{time:10.2f} {time_avg:10.2f} {time_min:10.2f} {time_max:10.2f}'
        time_throttle_str = f'{time_throttle:10.2f} {time_throttle_avg:10.2f} {time_throttle_min:10.2f} {time_throttle_max:10.2f}'
        docs_str = f"{m['merge_num_docs']:7.0f} {m['merge_current_num_docs']:9.0f}"
        bytes_str = f"{m['merge_size']:8.2f} {m['merge_current_size']:8.2f}"
        merge_stats.append(
            f"{cnt_str} | {time_str} | {time_throttle_str} | {docs_str} | {bytes_str} | {m['merge_throttle']:8.2f}"
        )

    print(f''' Merge 
     |     Counts     |                   Times (ms)                |             Throttle Times (ms)             |       Docs        |         MB        | Throttle (MB/s)
     | total  current |        sum        avg        min        max |        sum        avg        min        max |   total   current |    total  current | 
  V1 | {merge_stats[0]}
  V2 | {merge_stats[1]} 
    ''')

    translog_stats = []
    for m in (shards_metrics_v1, shards_metrics_v2):
        size = m['translog_size']
        size_min = m['translog_size_min']
        size_max = m['translog_size_max']
        size_avg = m['translog_size_avg']
        size_uncommitted = m['translog_uncommitted_size']
        size_uncommitted_min = m['translog_uncommitted_size_min']
        size_uncommitted_max = m['translog_uncommitted_size_max']
        size_uncommitted_avg = m['translog_uncommitted_size_avg']
        ops = m['translog_ops']
        ops_min = m['translog_ops_min']
        ops_max = m['translog_ops_max']
        ops_avg = m['translog_ops_avg']
        ops_uncommitted = m['translog_uncommitted_ops']
        ops_uncommitted_min = m['translog_uncommitted_ops_min']
        ops_uncommitted_max = m['translog_uncommitted_ops_max']
        ops_uncommitted_avg = m['translog_uncommitted_ops_avg']
        size_str = f"{size:8.2f} {size_avg:8.2f} {size_min:8.2f} {size_max:8.2f}"
        size_uncommitted_str = f"{size_uncommitted:8.2f} {size_uncommitted_avg:8.2f} {size_uncommitted_min:8.2f} {size_uncommitted_max:8.2f}"
        ops_str = f"{ops:8.0f} {ops_avg:8.0f} {ops_min:8.0f} {ops_max:8.0f}"
        ops_uncommitted_str = f"{ops_uncommitted:8.0f} {ops_uncommitted_avg:8.0f} {ops_uncommitted_min:8.0f} {ops_uncommitted_max:8.0f}"
        translog_stats.append(
            f"{size_str} | {ops_str} | {size_uncommitted_str} | {ops_uncommitted_str}"
        )

    print(f''' Translog 
     |                Size (MB)            |                   Ops               |          Size Uncommitted (MB)      |             Ops Uncommitted       
     |    total      avg      min      max |    total      avg      min      max |    total      avg      min      max |    total      avg      min      max 
  V1 | {translog_stats[0]}
  V2 | {translog_stats[1]} 
    ''')


# Executes a SQL statement, fetches the first row and converts the result into a dict of column_name -> value
def fetch_sql_result(stmt: str, cursor: Cursor) -> Dict[str, Any]:
    cursor.execute(stmt)
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    result = {}
    for i in range(len(columns)):
        name = columns[i]
        val = row[i] or 0
        result[name] = val
    return result


def collect_indexing_metrics(benchmark_host: str, indexing_stats: bool) -> Dict[str, Any]:
    indexing_metrics = {}
    if indexing_stats:
        with connect(benchmark_host) as conn:
            cursor = conn.cursor()
            indexing_metrics['segments'] = fetch_sql_result(SEGMENTS_STATS_STMT, cursor)
            indexing_metrics['shards'] = fetch_sql_result(SHARDS_STATS_STMT, cursor)
            cursor.close()
    return indexing_metrics
