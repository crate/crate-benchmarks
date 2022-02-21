#!/usr/bin/env python3

"""
About
=====

Investigate variability in benchmark runs on virtual machines.


Synopsis
========
::

    # Start CrateDB with 14 GB heap memory.
    sudo --user=crate vmbench.py start

    # Provision database with `uservisits` table.
    sudo --user=crate vmbench.py setup

    # Invoke list of benchmark specifications, saving corresponding result files
    # to /home/crate/cratedb-benchmark-results.
    sudo --user=crate vmbench.py run


References
==========

- https://engineering.mongodb.com/post/reducing-variability-in-performance-tests-on-ec2-setup-and-key-results
- https://engineering.mongodb.com/post/repeatable-performance-tests-cpu-options-are-best-disabled
- https://www.kernel.org/doc/html/v5.0/admin-guide/pm/cpuidle.html
"""
import datetime
import json
import platform
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

from cr8.run_crate import run_crate
from cr8.run_spec import run_spec

from util import human_readable_byte_size


class Scenario:

    CRATEDB_HOST = "localhost:4200"

    specs = [
        {"file": "specs/queries.toml"},
        {"file": "specs/select/hyperloglog.toml"},
        {"file": "specs/insert_single.py", "full": True},
        {"file": "specs/insert_bulk.toml", "full": True},
        {"file": "specs/insert_unnest.py", "full": True},
    ]

    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")

    def start_cratedb(self):
        run_crate(version="4.7", env=["CRATE_HEAP_SIZE=14G"], keep_data=True)

    def setup_specs(self):
        # Use `setup` recipe from `hyperloglog.toml`, it provides a complete set of `uservisits` data.
        run_spec(
            benchmark_hosts=self.CRATEDB_HOST,
            action="setup",
            spec="specs/select/hyperloglog.toml",
        )
        run_spec(
            benchmark_hosts=self.CRATEDB_HOST,
            action="load_data",
            spec="specs/select/hyperloglog.toml",
        )

    def run_specs(self):
        for spec in self.specs:
            self.run_spec(spec=spec)

    def run_spec(self, spec):

        full = spec.get("full")
        specfile = spec["file"]

        # Compute path to result file.
        home = Path.home()
        spec_slug = slugify(Path(specfile).stem)
        variant = get_variant()
        resultfile = (
            home
            / "cratedb-benchmarks-results"
            / variant
            / f"{self.timestamp}-{spec_slug}.json"
        )
        resultfile.parent.mkdir(parents=True, exist_ok=True)

        # Invoke benchmark specification, either in "full" or "queries"-only mode.
        if full:
            action = None
            print(f"Running specfile {specfile}, full mode")
        else:
            action = "queries"
            print(f"Running specfile {specfile}, queries-only mode")
        run_spec(
            benchmark_hosts=self.CRATEDB_HOST,
            action=action,
            spec=specfile,
            logfile_result=resultfile,
            output_fmt="json",
        )
        # amend_result_file(resultfile)


def amend_result_file(self, resultfile):
    # Read result file.
    with open(resultfile, "r") as f:
        data = json.load(f)

    # Prepare extensions.
    environment_info = OrderedDict(
        system=get_sysinfo(),
        kernel=get_kernelinfo(),
    )
    data["environment_info"] = environment_info

    # Write amended file.
    with open(resultfile, "w") as f:
        json.dump(data, f, indent=2)


def get_sysinfo():
    """
    https://pypi.org/project/sysinfo/
    """
    import psutil

    def format_size(value):
        return " ".join(map(str, human_readable_byte_size(value)))

    def shellout(command):
        return subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        ).decode()

    data = OrderedDict()

    data["kernel"] = shellout("uname -a")
    data["java"] = shellout("java -version")

    more = OrderedDict(
        platform=platform.platform(),
        processor=platform.processor(),
        installed_memory=format_size(psutil.virtual_memory()[0]),
        available_memory=format_size(psutil.virtual_memory()[1]),
        machine=platform.machine(),
        hostname=platform.node(),
        python=sys.version,
        # username=os.getlogin(),
    )
    data.update(more)

    return data


def read_proc(path):
    try:
        return open(path, "r").read().decode()
    except:
        pass


def get_kernelinfo():

    data = OrderedDict()
    data["cmdline"] = read_proc("/proc/cmdline")
    data["version_signature"] = read_proc("/proc/version_signature")

    return data


def get_variant():
    cmdline = read_proc("/proc/cmdline")
    variant = "vanilla"
    if cmdline is not None:
        if "idle=poll" in cmdline:
            variant = "idlepoll"
    return variant


def slugify(value):
    # https://github.com/earthobservations/luftdatenpumpe/blob/0.20.2/luftdatenpumpe/util.py#L211-L230
    import unicodedata

    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    import re

    value = re.sub("[^\w\s-]", "-", value).strip().lower()
    value = re.sub("[-\s]+", "-", value)
    value = value.strip("-")
    return value


def main():
    subcommand = sys.argv[1]
    scenario = Scenario()
    if subcommand == "start":
        scenario.start_cratedb()
    elif subcommand == "setup":
        scenario.setup_specs()
    elif subcommand == "run":
        # scenario.setup_specs()
        # scenario.run_spec(specfile="specs/amo.toml")
        scenario.run_specs()
    else:
        raise KeyError(f"Unknown subcommand {subcommand}")


if __name__ == "__main__":
    main()
