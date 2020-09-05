cycle optimization tutorial using PyGMO
---------------------------------------

.. contents::
    :depth: 1
    :local:
    :backlinks: top
    

Task
^^^^

Designing a power plant meets multiple different tasks, such as finding the 
optimal fresh steam temperature and pressure to reduce exhaust steam water 
content, or the optimization of extraction pressures to maximize cycle 
efficiency and many more. 

In case of a rather simple power plant topology the task of finding optimized 
values for e.g. extraction pressures is stll managable without any optimization 
tool. As the topology becomes more complexe and boundary conditions come into play 
the usage of additional tools is recommended.

The following tutorial is intended to show the usage of PyGMO in combination 
with TESPy to maximize the cycle efficiency of a power plant with two extractions.  
