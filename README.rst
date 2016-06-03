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

To run stresstests and external benchmarks against a specific Crate version 
it is necessary to provide the system property ``crate.testing.from_version`` or
``crate.testing.from_url``. Otherwise the tests won't start.

In order to run the stresstests that put really
lots of concurrent load on your local machine::

    ./gradlew stress -Dcrate.testing.from_version=0.54.9

In order to run the external benchmarks that test a running
crate cluster only via the CrateClient which is exposed in the CrateTestCluster and -Server::

    ./gradlew bench -Dcrate.testing.from_version=0.54.9

You were warned that both stresstests and benchmarks
put lots of pressure and load on your machine. Be prepared!

Crate benchmarks use ``CONSOLE``, ``H2``, and ``XML`` consumers to
persist its results. Benchmark results can be also backed up to Crate via 
transport or HTTP layer.
To achieve that, you need to provide following properties::

    ./gradlew bench
        -Djub.consumers=CONSOLE,CRATE
        -Djub.crate.host=localhost
        -Djub.crate.http=4200
        -Djub.crate.transport=4300

Finally
-------

Have fun!
