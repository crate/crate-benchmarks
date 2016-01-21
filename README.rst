Crate Stresstests
=================

This repository contains Crate Stresstests and Benchmarks
that are used to measure and compare performance against a local crate cluster.

Those tests and benchmarks do not seek exact, reproducable results.
They are mostly used to compare performance between two different crate versions.

Both benchmarks and stresstests evolved from our internal test suite into
a separate project because we saw a need for some naive performance measurement
and wanted to measure some heavy-load scenarios. And you usually
don't want that to slow down your unit tests.

Usage
-----

In order to run the stresstests that put really
lots of concurrent load on your local machine::

    ./gradlew stress

In order to run the external benchmarks that test a running
crate cluster only via the CrateClient which is exposed in the CrateTestCluster and -Server::

    ./gradlew bench

You were warned that both stresstests and benchmarks
put lots of pressure and load on your machine. Be prepared!


By default the stresstests and benchmark use the Crate version specified by the
``crate.version`` system property. It is also possible to provide a specific
Crate version using a URL. The URL is set using the ``crate.url`` system property,
e.g.::

    ./gradlew bench
        -Dcrate.url=https://cdn.crate.io/downloads/releases/crate-0.54.3.tar.gz


Crate benchmarks use ``CONSOLE``, ``H2``, and ``XML`` consumers to
persist its results. Benchmark results can be also backed up to Crate.
To achieve that, you need to provide following properties::

    ./gradlew bench
        -Djub.consumers=CONSOLE,CRATE
        -Djub.crate.host=localhost
        -Djub.crate.http=4200
        -Djub.crate.transport=4300

Finally
-------

Have fun!
