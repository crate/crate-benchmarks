==================
Random query tests
==================

This folder contains tests which intend to test the performance of different
``WHERE`` expressions.

``SELECT count(*)`` is used because it has little overhead besides the query
expression evaluation.


Run with::

    cr8 run-track query_tests/track.toml
