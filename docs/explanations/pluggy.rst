.. _pluggy:

pluggy and the Plugin Architecture
==================================

pluggy ([1]_, [2]_, [3]_) is at the heart of pytask and enables its plugin system. The
mechanism to achieve extensibility is called :term:`hooking`.

At certain points, pytask, or more generally the host, implements entry-points which are
called hook specifications. At these entry-points the host sends a message to all
plugins which use this entry-point. The recipient of the message is implemented by the
plugin and called a hook implementation. The hook implementation receives the message
and can decide whether to send a response or not. Then, the host receives the responses
and can decide whether to process all or just the first valid return.

In contrast to some other mechanisms to change the behavior of a program (like method
overriding, monkey patching), hooking excels at allowing multiple plugins to work
alongside each other.

Thus, it is the host's responsibility to design the entry-points in such a way that

- plugins can target very specific entry-points of the application and achieve their
  goal efficiently.
- many plugins can work alongside each other.
- the necessary knowledge about pytask to implement a plugin is somewhat proportional to
  the complexity of plugin's provided functionality.


References
----------

.. [1] `pluggy's documentation <https://pluggy.readthedocs.io/en/latest/>`_.

.. [2] `A talk by Floris Bruynooghe about pluggy and pytest
       <https://youtu.be/zZsNPDfOoHU>`_.

.. [3] `An introduction to pluggy by Kracekumar Ramaraju
       <https://kracekumar.com/post/build_plugins_with_pluggy>`_.
