Crate Stresstests
=================

This repository contains Crate Stresstests and Benchmarks.

Those tests and benchmarks do not seek exact, reproducable results. They are
mostly used to compare performance between two different crate versions.

py
==

This folder contains benchmarks which use `cr8`_.

See the README in the py folder for more details.

java
====

This folder contains tests which use the Crate Java client.
These tests are considered legacy.

See the README in the java folder for more details.

api
===

This folder contains the API (Flask application) to access benchmark results
stored in the Crate production cluster on Microsoft Azure.

See the README in the api folder for more details.


.. _cr8: https://github.com/mfussenegger/cr8
