#!/usr/bin/env bash
#
# Records disk IO while a benchmark runs via compare_run_saved.py. Start it in
# a second terminal before the benchmark and stop it with Ctrl-C once the
# benchmark has finished and background IO (merges, flushes) has settled. A
# summary is printed on exit.
#
# Usage: ./io_monitor.sh
#
# compare_run_saved.py puts the CrateDB data below
# /var/tmp/crate-benchmarks-run-<timestamp>, so the disks watched here are the
# ones holding /var/tmp. Every CrateDB node started by compare_run.py is picked up
# automatically. Each fork of v1 and v2 is a new node, with a new pid and a new
# path.data.
#
# Files are written to io_monitor_out/ next to this script, replacing the ones
# of the previous run:
#   devices.txt                     mount and disks holding /var/tmp
#   iostat.log                      iostat -x for those disks, every second
#   psi.log                         /proc/pressure/io, every second
#   diskstats.start, diskstats.end  /proc/diskstats snapshots
#   pressure.start, pressure.end    /proc/pressure/io snapshots
#   nodes.log                       pid, start/end time and path.data of each node
#   pidstat-<pid>.log               pidstat -d -r (IO and page faults), every second
#   procio-<pid>.log                /proc/<pid>/io, every second
#   df-<pid>.log                    used bytes of the path.data filesystem, every second
#   summary.txt                     the summary printed on exit
#
# Requires sysstat (iostat, pidstat). Run it with sudo if the CrateDB node runs
# as another user: /proc/<pid>/io is only readable by the owner and root.

set -uo pipefail

TMP_ROOT=/var/tmp
RUN_PREFIX=$TMP_ROOT/crate-benchmarks-run-

die() {
    echo "$*" >&2
    exit 1
}

disks_below() {
    local dev=$1 slave
    local slaves=(/sys/class/block/"$dev"/slaves/*)
    if [[ -e ${slaves[0]} ]]; then
        for slave in "${slaves[@]}"; do
            disks_below "${slave##*/}"
        done
    elif [[ -e /sys/class/block/$dev/partition ]]; then
        disks_below "$(basename "$(dirname "$(readlink -f "/sys/class/block/$dev")")")"
    else
        echo "$dev"
    fi
}

(( $# == 0 )) || die "Usage: $0"

for cmd in iostat pidstat findmnt pgrep; do
    command -v "$cmd" > /dev/null || die "$cmd not found (iostat and pidstat are part of sysstat)"
done

[[ $(findmnt -no FSTYPE -T "$TMP_ROOT") != tmpfs ]] \
    || die "$TMP_ROOT is on tmpfs, benchmark data lives in RAM and never reaches a disk"
tmp_majmin=$(findmnt -no MAJ:MIN -T "$TMP_ROOT" | tr -d ' ')
[[ -e /sys/dev/block/$tmp_majmin ]] || die "$TMP_ROOT is not on a block device"
tmp_dev=$(basename "$(readlink -f "/sys/dev/block/$tmp_majmin")")
mapfile -t disks < <(disks_below "$tmp_dev" | sort -u)

have_psi=false
if [[ -r /proc/pressure/io ]]; then
    have_psi=true
else
    echo "Warning: /proc/pressure/io not available, no IO pressure data" >&2
fi

out=$(dirname "$(readlink -f "$0")")/io_monitor_out
mkdir -p "$out" || exit 1
rm -f -- "$out"/*.log "$out"/{diskstats,pressure}.{start,end} "$out"/{devices,summary}.txt

{
    findmnt -T "$TMP_ROOT" -o TARGET,SOURCE,FSTYPE,MAJ:MIN
    echo
    echo "block device: $tmp_dev"
    echo "disks: ${disks[*]}"
} > "$out/devices.txt"

export S_TIME_FORMAT=ISO

HB='
function hb(b,   units, i) {
    split("B KiB MiB GiB TiB", units, " ")
    for (i = 1; b >= 1024 && i < 5; i++) b /= 1024
    return sprintf("%.1f %s", b, units[i])
}'

crate_nodes() {
    local parents
    parents=$(pgrep -d, -f 'compare_run\.py') || return 0
    pgrep -P "$parents" -f io.crate.bootstrap.CrateDB
}

watch_node() {
    local pid=$1
    local data pidstat_pid io
    data=$(tr '\0' '\n' < "/proc/$pid/cmdline" | sed -n 's/^-Cpath\.data=//p')
    data=${data%%,*}
    echo "$(date +%s) $(date -Iseconds) pid=$pid start path.data=$data" >> "$out/nodes.log"
    if [[ $data != "$RUN_PREFIX"* ]]; then
        echo "Warning: path.data of node $pid ($data) is not below ${RUN_PREFIX}*, the disk stats may not cover it" >&2
    fi
    if [[ ! -r /proc/$pid/io ]]; then
        echo "Warning: cannot read /proc/$pid/io, run this script as root" >&2
    fi

    pidstat -d -r -h 1 -p "$pid" > "$out/pidstat-$pid.log" &
    pidstat_pid=$!
    trap 'kill "$pidstat_pid" 2> /dev/null; exit' TERM

    echo "time rchar wchar syscr syscw read_bytes write_bytes cancelled_write_bytes" > "$out/procio-$pid.log"
    echo "time used_bytes" > "$out/df-$pid.log"
    while [[ -e /proc/$pid ]]; do
        if io=$(awk '{ printf " %s", $2 }' "/proc/$pid/io" 2> /dev/null); then
            echo "$(date +%s)$io" >> "$out/procio-$pid.log"
        fi
        echo "$(date +%s) $(df -B1 --output=used "$data" 2> /dev/null | tail -n +2)" >> "$out/df-$pid.log"
        sleep 1
    done
    kill "$pidstat_pid" 2> /dev/null
    echo "$(date +%s) $(date -Iseconds) pid=$pid end" >> "$out/nodes.log"
}

summary() {
    local wall_ms f pid
    wall_ms=$(awk -v s="$start" -v e="$end" 'BEGIN { printf "%d", (e - s) * 1000 }')
    echo "Duration: $((wall_ms / 1000)) s"

    echo
    echo "Disks holding $TMP_ROOT (/proc/diskstats, start to end):"
    printf '%-12s %12s %14s %12s %14s %7s\n' device reads read writes written %util
    awk -v devs="${disks[*]}" -v wall="$wall_ms" "$HB"'
        BEGIN { n = split(devs, d, " "); for (i = 1; i <= n; i++) want[d[i]] = 1 }
        NR == FNR { r[$3] = $4; rs[$3] = $6; w[$3] = $8; ws[$3] = $10; busy[$3] = $13; next }
        ($3 in want) && ($3 in r) {
            printf "%-12s %12d %14s %12d %14s %6.1f%%\n", $3,
                $4 - r[$3], hb(($6 - rs[$3]) * 512), $8 - w[$3], hb(($10 - ws[$3]) * 512),
                100 * ($13 - busy[$3]) / wall
        }' "$out/diskstats.start" "$out/diskstats.end"

    if $have_psi; then
        echo
        echo "IO pressure (share of the duration with tasks stalled on IO):"
        awk -v wall="$wall_ms" '
            NR == FNR { sub("total=", "", $5); t[$1] = $5; next }
            {
                sub("total=", "", $5)
                printf "  %-4s %5.1f%%  (%s)\n", $1, 100 * ($5 - t[$1]) / (wall * 1000),
                    $1 == "some" ? "at least one task stalled" : "all non-idle tasks stalled"
            }' "$out/pressure.start" "$out/pressure.end"
    fi

    echo
    echo "Nodes (/proc/<pid>/io totals since node start, df growth = peak - first sample):"
    printf '%-8s %8s %14s %14s %14s\n' pid seconds read written df_growth
    for f in "$out"/procio-*.log; do
        [[ -e $f ]] || continue
        pid=${f##*/procio-}
        pid=${pid%.log}
        awk -v pid="$pid" -v procio="$f" -v dff="$out/df-$pid.log" "$HB"'
            FNR == 1 { next }
            FILENAME == procio { if (!n++) t0 = $1; t1 = $1; rb = $6; wb = $7 - $8 }
            FILENAME == dff && $2 != "" { if (!m++) u0 = umax = $2; if ($2 > umax) umax = $2 }
            END {
                if (!n) { printf "%-8s %8s %14s %14s %14s\n", pid, "n/a", "n/a", "n/a", "n/a"; exit }
                printf "%-8s %8d %14s %14s %14s\n", pid, t1 - t0, hb(rb), hb(wb), m ? hb(umax - u0) : "n/a"
            }' "$f" "$out/df-$pid.log"
    done
}

cleanup() {
    trap - INT TERM
    echo
    echo "Stopping samplers"
    kill $(jobs -p) 2> /dev/null
    wait
    cat /proc/diskstats > "$out/diskstats.end"
    if $have_psi; then
        cat /proc/pressure/io > "$out/pressure.end"
    fi
    end=$(date +%s.%N)
    echo
    summary | tee "$out/summary.txt"
    exit 0
}

cat /proc/diskstats > "$out/diskstats.start"
if $have_psi; then
    cat /proc/pressure/io > "$out/pressure.start"
fi
start=$(date +%s.%N)

iostat -x -z -t -y 1 "${disks[@]}" > "$out/iostat.log" &
if $have_psi; then
    while sleep 1; do
        echo "$(date +%s) $(tr '\n' ' ' < /proc/pressure/io)"
    done > "$out/psi.log" &
fi

declare -A seen
trap cleanup INT TERM
echo "Watching disks ${disks[*]} (holding $TMP_ROOT), writing to $out, press Ctrl-C to stop"
while true; do
    for pid in $(crate_nodes); do
        if [[ -z ${seen[$pid]:-} ]]; then
            seen[$pid]=1
            echo "Node $pid started"
            watch_node "$pid" &
        fi
    done
    sleep 1
done
