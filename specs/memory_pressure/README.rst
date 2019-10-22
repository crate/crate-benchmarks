
This directory contains spec files with queries which require a lot of live
memory.


The data sets for the spec files are not checked in but need to be generated.
Generation requires `mkjson`_ and `jq`_::

    $ mkjson --num 500000 custom_user_id="ulid()" | jq -r '.custom_user_id' >! custom_user_ids.txt
    $ mkjson --num 5000000 custom_user_id="oneOf(fromFile('custom_user_ids.txt'))" id="ulid()" > data.json


Then use `cr8`_ to run them (see README of repo root directory).


.. _mkjson: https://github.com/mfussenegger/mkjson/
.. _jq: https://stedolan.github.io/jq/
.. _cr8: https://github.com/mfussenegger/cr8/
