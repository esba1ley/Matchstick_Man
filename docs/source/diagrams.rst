Diagrams
========

Player state machine
--------------------

The central mechanic is a three-state lifecycle driven by ceiling material,
water contact, and matchbook pickups. ``DEAD`` is a terminal state with no
transitions out.

.. uml:: ../diagrams/player_state_machine.puml

Class structure
---------------

Current module and class relationships. ``Player`` carries no Pyxel dependency
and is exercised independently by the unit-test suite.

.. uml:: ../diagrams/class_structure.puml
