pluggy and the Plugin Architecture
==================================

pluggy is at the heart of pytask and enables the plugin architecture.


The mechanism to
achieve extensibility is called hooking. At certain points, pytask, or more generally
the host, implements entry-points which are called hook specifications. At these
entry-points the host sends a message to all plugins which use this entry-point. The
recipient implemented by the plugin is called a hook implementation. The hook
implementation receives the message and can decide whether to send a response or not.
Then, the host receives the responses and can decide whether to process all or just the
first valid return.
