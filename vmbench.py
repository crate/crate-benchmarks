#!/usr/bin/env python3

"""
About
=====

Investigate variability in benchmark runs on virtual machines.


Synopsis
========
::

    # Start CrateDB with 14 GB heap memory.
    vmbench.py start

    # Provision database with `uservisits` table.
    vmbench.py setup

    # Invoke list of benchmark specifications, saving corresponding result files
    # to /home/crate/cratedb-benchmark-results.
    vmbench.py run

    # Aggregate numbers on designated variant.
    python vmbench.py analyze vanilla
    python vmbench.py analyze idlepoll
    python vmbench.py analyze idlepoll-nosmt


Production
==========
::

    sudo --user=crate /opt/crate-benchmarks/.venv/bin/python /opt/crate-benchmarks/vmbench.py start
    sudo --user=crate /opt/crate-benchmarks/.venv/bin/python /opt/crate-benchmarks/vmbench.py setup
    sudo --user=crate /opt/crate-benchmarks/.venv/bin/python /opt/crate-benchmarks/vmbench.py run


References
==========

- https://engineering.mongodb.com/post/reducing-variability-in-performance-tests-on-ec2-setup-and-key-results
- https://engineering.mongodb.com/post/repeatable-performance-tests-cpu-options-are-best-disabled
- https://www.kernel.org/doc/html/latest/admin-guide/pm/cpuidle.html
- https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/l1tf.html#smt-control
"""
import datetime
import json
import platform
import subprocess
import sys
import textwrap
from collections import OrderedDict
from pathlib import Path

from cr8.run_crate import run_crate
from cr8.run_spec import run_spec

from compare_results import read_results
from util import human_readable_byte_size


class Scenario:

    CRATEDB_HOST = "localhost:4200"

    specs = [
        {"file": "specs/queries.toml"},
        {"file": "specs/select/hyperloglog.toml"},
        #{"file": "specs/insert_single.py", "full": True},
        {"file": "specs/insert_bulk.toml", "full": True},
        {"file": "specs/insert_unnest.py", "full": True},
    ]

    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")

    def __init__(self):
        home = Path.home()
        self.resultfile_path = (home / "cratedb-benchmarks-results")

    def start_cratedb(self):
        run_crate(version="4.7", env=["CRATE_HEAP_SIZE=14G"], keep_data=True)

    def setup_specs(self):
        # Use `setup` recipe from `hyperloglog.toml`, it provides a complete set of `uservisits` data.
        hyperloglog_spec = self.get_specfile("specs/select/hyperloglog.toml")
        run_spec(
            benchmark_hosts=self.CRATEDB_HOST,
            action="setup",
            spec=hyperloglog_spec,
        )
        run_spec(
            benchmark_hosts=self.CRATEDB_HOST,
            action="load_data",
            spec=hyperloglog_spec,
        )

    def run_specs(self):
        for spec in self.specs:
            self.run_spec(spec=spec)

    def get_specfile(self, specfile):
        return Path(__file__).parent.joinpath(specfile)

    def run_spec(self, spec):

        full = spec.get("full")
        specfile = self.get_specfile(spec["file"])

        # Compute path to result file.
        variant = get_variant()
        spec_slug = slugify(Path(specfile).stem)
        resultfile = self.resultfile_path / variant / f"{spec_slug}-{self.timestamp}.json"
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

    def analyze(self, variant):
        for spec in self.specs:
            specfile = self.get_specfile(spec["file"])
            spec_slug = slugify(Path(specfile).stem)
            result_files = list(Path(self.resultfile_path).joinpath(variant).glob(spec_slug + "-*"))
            #print(f"Result files for {spec_slug}:\n{result_files}")
            print(f"# {spec_slug}")
            for result_file in result_files:
                results = read_results(result_file)
                #print(results)
                for result in results:
                    filename = result["meta"]["name"]
                    started = result["started"]
                    statement = result["statement"]
                    concurrency = result["concurrency"]
                    vmax = result["runtime_stats"]["max"]
                    vmin = result["runtime_stats"]["min"]
                    vmedian = result["runtime_stats"]["median"]
                    range = (vmax - vmin) / vmedian

                    #timestamp = datetime.datetime.fromtimestamp(started / 1000).strftime("%Y%m%dT%H%M%S")
                    #print(f"{timestamp}-{filename}::{statement}-c{concurrency}:", range)
                    statement = textwrap.shorten(statement, 50)
                    print(f"{filename};{concurrency:02};{statement:55};{range}")
            print()


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


def read_file(path):
    try:
        return open(path, "r").read()
    except:
        pass


def get_kernelinfo():

    data = OrderedDict()
    data["cmdline"] = read_file("/proc/cmdline")
    data["version_signature"] = read_file("/proc/version_signature")

    return data


def get_variant():
    cmdline = read_file("/proc/cmdline")
    variant = "vanilla"
    if cmdline is not None:
        options = []
        if "idle=poll" in cmdline:
            options.append("idlepoll")
        if "nosmt" in cmdline:
            options.append("nosmt")
        variant = "-".join(options)
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
    subcommand = None
    try:
        subcommand = sys.argv[1]
    except IndexError:
        pass
    scenario = Scenario()
    if subcommand == "start":
        scenario.start_cratedb()
    elif subcommand == "setup":
        scenario.setup_specs()
    elif subcommand == "run":
        scenario.run_specs()
    elif subcommand == "analyze":
        scenario.analyze(sys.argv[2])
    elif subcommand == "help":
        print(__doc__)
    else:
        raise KeyError(f"Unknown subcommand {subcommand}, try {sys.argv[0]} help")


if __name__ == "__main__":
    main()
