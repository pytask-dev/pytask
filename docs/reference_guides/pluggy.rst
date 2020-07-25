.. _pluggy:

pluggy and the Plugin Architecture
==================================

pluggy is at the heart of pytask and enables the plugin architecture. The mechanism to
achieve extensibility is called :term:`hooking`. At certain points, pytask, or more
generally the host, implements entry-points which are called hook specifications. At
these entry-points the host sends a message to all plugins which use this entry-point.
The recipient implemented by the plugin is called a hook implementation. The hook
implementation receives the message and can decide whether to send a response or not.
Then, the host receives the responses and can decide whether to process all or just the
first valid return.

It is the host's responsibility to design the entry-points in such a way that

- plugins can target very specific entry-points of the application and achieve their
  goal without much code.
- many plugins can work alongside each other.
- the necessary knowledge about pytask to program a plugin is somewhat proportional to
  the complexity of plugin's provided functionality.

pytask's entry-points are listed in
