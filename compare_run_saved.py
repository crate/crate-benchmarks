#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wrapper around compare_run.py which tees the output into a file below runs/,
together with the arguments used to produce it.

All arguments are forwarded to compare_run.py as-is.

The layout below runs/ mirrors the location of the spec, so
--spec specs/select/group_by_destinationURL.toml ends up in
runs/select/group_by_destinationURL/run_yyyy_mm_dd_hh_mm.txt
"""

import argparse
import io
import os
import shlex
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
COMPARE_RUN = os.path.join(HERE, 'compare_run.py')
RUNS_DIR = os.path.join(HERE, 'runs')


def spec_subdir(spec: str) -> str:
    """Path of `spec` relative to specs/, without extension.

    specs/select/group_by_destinationURL.toml -> select/group_by_destinationURL
    """
    spec = os.path.splitext(os.path.abspath(spec))[0]
    rel = os.path.relpath(spec, os.path.join(HERE, 'specs'))
    if rel.startswith(os.pardir):
        # spec lives outside of specs/; don't mirror the whole absolute path
        rel = os.path.basename(spec)
    return rel


def output_file(spec: str, runs_dir: str) -> str:
    """Return the (unique) path to write the output of a run for `spec` to."""
    out_dir = os.path.join(runs_dir, spec_subdir(spec))
    os.makedirs(out_dir, exist_ok=True)
    prefix = 'run_' + datetime.now().strftime('%Y_%m_%d_%H_%M')
    path = os.path.join(out_dir, prefix + '.txt')
    i = 1
    while os.path.exists(path):
        i += 1
        path = os.path.join(out_dir, f'{prefix}_{i}.txt')
    return path


def tee(stream, out):
    """Echo `stream` to stdout, write only real lines (not \r updates) to `out`.

    tqdm draws progress bars by rewriting the current line with a leading \r.
    Those updates are useful on a terminal but would end up as one line per
    update in the run file, so they are dropped on the way to `out`.
    """
    buf = ''
    rewritten = False
    for chunk in iter(lambda: stream.read(1), ''):
        sys.stdout.write(chunk)
        if chunk == '\r':
            sys.stdout.flush()
            buf = ''
            rewritten = True
        elif chunk == '\n':
            sys.stdout.flush()
            if not rewritten:
                out.write(buf + '\n')
                out.flush()
            buf = ''
            rewritten = False
        else:
            buf += chunk
    if buf and not rewritten:
        sys.stdout.flush()
        out.write(buf)
        out.flush()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', help='path to spec file', required=True)
    p.add_argument('--runs-dir', default=RUNS_DIR,
                   help=f'Directory the run outputs are stored in. Defaults to {RUNS_DIR}')
    args, forwarded = p.parse_known_args()

    cmd = [sys.executable, COMPARE_RUN, '--spec', args.spec] + forwarded
    out_file = output_file(args.spec, args.runs_dir)
    started = datetime.now()

    try:
        subprocess.run(
            ['sudo', 'sysctl', 'kernel.perf_event_paranoid=1'],
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f'Warning: failed to set kernel.perf_event_paranoid=1: {e}', file=sys.stderr)

    env = dict(os.environ, PYTHONUNBUFFERED='1')
    print(f'Writing output to {out_file}')
    with open(out_file, 'w', encoding='utf-8') as out:
        out.write(f'# started:  {started.isoformat(timespec="seconds")}\n')
        out.write(f'# cwd:      {os.getcwd()}\n')
        out.write('# command:  ' + ' '.join(shlex.quote(a) for a in cmd) + '\n')
        out.write('\n')
        out.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=HERE,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # newline='' so \r from progress bars isn't translated into \n
        stdout = io.TextIOWrapper(proc.stdout, encoding='utf-8', newline='')
        try:
            tee(stdout, out)
            returncode = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            returncode = proc.wait()
            out.write('\n# interrupted\n')
        ended = datetime.now()
        out.write(f'\n# ended:    {ended.isoformat(timespec="seconds")}\n')
        out.write(f'# duration: {ended - started}\n')
        out.write(f'# exit:     {returncode}\n')
    print(f'Output written to {out_file}')
    sys.exit(returncode)


if __name__ == "__main__":
    main()
