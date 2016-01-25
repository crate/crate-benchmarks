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

By default Crate Stresstests and Benchmarks fetch Crate by version, by setting
``crate.version`` property to a required version. It is also possible to provide
a URL with the certain specific version. In order to do that the ``crate.url`` property
must be set.
If both properties are set, then the ``crate.url`` is used.

Finally
-------

Have fun!
