=============================
Millepede II Python Interface
=============================

Installation
------------

You need **cmake** for the building of the python interface to MillepedeII. 

You should setup a virtual enviroment of python first and activate it. Also for the below command to work, you should be in the `alignment/modules` subdirectory and do NOT alter the build directory name.

.. code-block:: shell
   
   mkdir build && cd build
   cmake .. && cmake --build .
   cd .. && pip3 install .

This installation procedure can be improved in the future (make the cmake calls within python setup).

Usage
-----

.. code-block:: python

   import pyMille
   MyMille = pyMille.Mille("output.file")
   MyMille.write([0.1, 0.2], [1.0, 2.0], 0.01, 0.001)

Get more info via docstrings!