#!/usr/bin/env python3

"""
About
=====

Investigate variability in benchmark runs on virtual machines.


Setup
=====

The analyzer routines use pandas and tabulate, so::

    pip install --requirement=requirements.txt pandas tabulate


Synopsis
========
::

    # Start CrateDB with 14 GB heap memory.
    vmbench.py start

    # Provision database with `uservisits` table, once.
    vmbench.py setup

    # Invoke list of benchmark specifications, saving corresponding result files
    # to /home/crate/cratedb-benchmark-results.
    vmbench.py run

    # Run each scenario five times.
    vmbench.py run 5

    # Summarize numbers on designated variant.
    python vmbench.py collect vanilla
    python vmbench.py collect idlepoll
    python vmbench.py collect idlepoll-nosmt

    # Compare numbers between variants side by side.
    python vmbench.py summary


Production
==========

Convenient shortcut to address `vmbench` program within virtualenv::

    vmbench() {
        sudo --user=crate /opt/crate-benchmarks/.venv/bin/python /opt/crate-benchmarks/vmbench.py "$@"
    }

::

    # Bootstrap environment.
    # Note: Run this after each reboot.
    vmbench start
    vmbench setup

    # Run benchmarks.
    # Note: Change Linux kernel parameters and iterate to create "variants".
    vmbench run 5

    # Compare benchmark results between variants.
    vmbench summary


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
    """
    Run a defined set of `run-spec` files and record their outcomes with different variants.
    The variants are runtime environment tunings with Linux kernel parameters.
    """

    CRATEDB_HOST = "localhost:4200"

    specs = [
        {"file": "specs/queries.toml"},
        {"file": "specs/select/hyperloglog.toml"},
        # {"file": "specs/insert_single.py", "full": True},
        {"file": "specs/insert_bulk.toml", "full": True},
        {"file": "specs/insert_unnest.py", "full": True},
    ]

    variants = [
        "vanilla",
        "idlepoll",
        "idlepoll-nosmt",
    ]

    def __init__(self):
        # TODO: Optionally use path from `VMBENCH_RESULTS` environment variable.
        home = Path.home()
        self.resultfile_path = home / "cratedb-benchmarks-results"

    def start_cratedb(self):
        # TODO: Make version and heap size configurable.
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

    def run_specs(self, count=1):
        for _ in range(count):
            for spec in self.specs:
                self.run_spec(spec=spec)

    @staticmethod
    def get_specfile(specfile):
        return Path(__file__).parent.joinpath(specfile)

    def run_spec(self, spec):

        full = spec.get("full")
        specfile = self.get_specfile(spec["file"])

        # Compute path to result file.
        variant = get_variant()
        spec_slug = slugify(Path(specfile).stem)
        timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        resultfile = self.resultfile_path / variant / f"{spec_slug}-{timestamp}.json"
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

        # TODO: Implement proper result file amending.
        # amend_result_file(resultfile)


class Analyzer:
    """
    Analyze `run-spec` JSONL result files.
    """

    def __init__(self, scenario: Scenario):
        self.scenario = scenario

    def summary(self):
        return self.summarize_variants(grouped=True)

    def summarize_variants(self, grouped=False):
        """
        Collect results from multiple variants across multiple runs and summarize
        the results into spreadsheet shape for convenient side-by-side comparison.
        """
        import pandas as pd

        # Slurp all result files.
        range_items = []
        for variant in Scenario.variants:
            range_items += self.collect(variant)
        # print(json.dumps(range_items, indent=2))

        # Display the data in tabular shape.
        df = pd.DataFrame(range_items)

        if not grouped:
            dft = self.reshape_comparison(df)
            yield "all", dft

        else:
            # Display the data in tabular shape, grouped by run identifier.
            df_grouped = df.groupby(by="run")
            for run_id, dfg in df_grouped:
                # print(f"# Run: {run_id}")
                del dfg["run"]
                dfg = self.reshape_comparison(dfg)
                yield run_id, dfg

    def collect(self, variant):
        """
        - Scan result folder for all spec result files matching variant.
        - For each result file, iterate all result items.
        - For each result item, compute `range = (max - min) / median`.
        """
        spec_item_results = []

        # All the defined spec files.
        for spec in self.scenario.specs:
            specfile = self.scenario.get_specfile(spec["file"])
            spec_slug = slugify(Path(specfile).stem)

            # Each spec file produces multiple result files across multiple runs.
            result_files = list(Path(self.scenario.resultfile_path).joinpath(variant).glob(spec_slug + "-*"))
            # print(f"Result files for {spec_slug}:\n{result_files}")
            # print(f"# {spec_slug}")

            result_file: Path
            for run_index, result_file in enumerate(sorted(result_files)):

                # Derive "run identifier" from timestamp in filename.
                # Needed to identify an individual single spec item across multiple runs.
                # run_id = result_file.stem.rsplit("-", maxsplit=1)[-1]
                run_id = run_index

                # Results from a single spec results file.
                results = read_results(result_file)

                # Each result file has multiple items, one per test case / statement,
                # with designated concurrency. We call it "spec item".
                for result in results:
                    specfile = result["meta"]["name"]
                    started = result["started"]
                    statement = result["statement"]
                    concurrency = result["concurrency"]
                    vmax = result["runtime_stats"]["max"]
                    vmin = result["runtime_stats"]["min"]
                    vmedian = result["runtime_stats"]["median"]

                    """
                    > For each test, we analyzed the 25 data points, with a goal of finding a
                    > configuration that minimizes this single metric:
                    >
                    >     range = (max - min) / median

                    -- https://engineering.mongodb.com/post/reducing-variability-in-performance-tests-on-ec2-setup-and-key-results
                    """
                    vrange = (vmax - vmin) / vmedian
                    vrange = round(vrange, 2)

                    statement_short = textwrap.shorten(statement, 50)

                    # To identify an individual single spec item across multiple runs, we use its
                    # start timestamp and call it the "run identifier".
                    # run_id = datetime.datetime.fromtimestamp(started / 1000).strftime("%Y%m%dT%H%M%S")

                    spec_item_result = dict(
                        # Composite key to uniquely identify a single spec item across multiple spec runs.
                        spec=specfile,
                        stmt=statement_short,
                        concurrency=concurrency,
                        run=run_id,
                        # Column axis in spe.
                        variant=variant,
                        # Value.
                        range=vrange,
                    )
                    spec_item_results.append(spec_item_result)

        return spec_item_results

    def reshape_comparison(self, df):
        """
        Create spreadsheet-style pivot table from all spec item results,
        for side-by-side comparison of outcomes for different variants,
        across multiple runs.

        - All index fields will be squashed into a pandas MultiIndex as composite key.
        - All distinct values of the "variant" field will be used as designated columns.
        """

        # Define fields to be used as multi index / composite key.
        index_fields = ["spec", "stmt", "concurrency"]

        # When data is already grouped by run id, it is missing as field already.
        # So, make it part of the composite key only conditionally.
        if "run" in df:
            index_fields.append("run")

        # Pivot into spreadsheet-style data frame.
        df = df.pivot(index=index_fields, columns=["variant"], values="range")

        # Make sure the order of the "variant" columns matches the definition.
        df = df.reindex(columns=self.scenario.variants)

        # Just slap a meaningful name on the composite key column, derived from its original field names.
        df.index.name = ", ".join(index_fields)

        return df

    @staticmethod
    def display_frame_tabular(df):
        from tabulate import tabulate

        print(tabulate(df, headers="keys"))


def amend_result_file(self, resultfile):
    """
    The idea was to annotate the JSON result file with more data about the runtime environment.
    FIXME: This function does not work on JSONL files yet.
    """

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
        return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()

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
        if options:
            variant = "-".join(options)
    return variant


def slugify(value):
    # https://github.com/earthobservations/luftdatenpumpe/blob/0.20.2/luftdatenpumpe/util.py#L211-L230
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "-", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    value = value.strip("-")
    return value


def print_header(title):
    length = len(title)
    print("-" * length)
    print(title)
    print("-" * length)


def main():
    subcommand = None
    try:
        subcommand = sys.argv[1]
    except IndexError:
        pass

    scenario = Scenario()
    analyser = Analyzer(scenario=scenario)

    # Run benchmarks and record results.
    if subcommand == "start":
        scenario.start_cratedb()
    elif subcommand == "setup":
        scenario.setup_specs()
    elif subcommand == "run":
        try:
            count = int(sys.argv[2])
        except:
            count = 1
        scenario.run_specs(count)

    # Analyze benchmark results.
    elif subcommand == "collect":
        try:
            variant = sys.argv[2]
        except IndexError:
            raise KeyError(f"Variant needed, choose one of {scenario.variants}.")
        print(json.dumps(analyser.collect(variant), indent=2))
    elif subcommand == "summary":
        for run_id, df in analyser.summary():
            print_header(f"Run #{run_id}")
            print()
            analyser.display_frame_tabular(df)
            print()
            print()

    elif subcommand == "help":
        print(__doc__)
    else:
        raise KeyError(f"Unknown subcommand {subcommand}, try {sys.argv[0]} help")


if __name__ == "__main__":
    main()
