`nspfile`: NSP Audio File Reader in Python
===================================================

|pypi| |status| |pyver| |license| |test_status|

.. |pypi| image:: https://img.shields.io/pypi/v/nspfile
  :alt: PyPI
.. |status| image:: https://img.shields.io/pypi/status/nspfile
  :alt: PyPI - Status
.. |pyver| image:: https://img.shields.io/pypi/pyversions/nspfile
  :alt: PyPI - Python Version
.. |license| image:: https://img.shields.io/github/license/tikuma-lsuhsc/python-nspfile
  :alt: GitHub
.. |test_status| image:: https://img.shields.io/github/workflow/status/tikuma-lsuhsc/python-nspfile/Run%20Tests
  :alt: GitHub Workflow Status

NSP audio file format is primarily used for KayPENTAX Computerized Speech Lab (CSL).

Python `nspfile` package implements `scipy.io.wavfile` compatible functions for .nsp sound file format.

Install
-------

.. code-block:: bash

   pip install nspfile

Use
---

.. code-block:: python

   import nspfile

   fs, x = nspfile.read('myvoice.nsp')

TODOs
-----

- Test multichannel read
- Add a writer function

Reference
---------

http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/CSL/CSL.html
