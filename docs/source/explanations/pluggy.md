# pluggy and the Plugin Architecture

pluggy ([^id4], [^id5], [^id6]) is at the heart of pytask and enables its plugin system.
The mechanism to achieve extensibility is called {term}`hooking`.

At specific points, pytask, or more generally the host, implements entry-points called
hook specifications. At these entry-points, the host sends a message to all plugins
which target this entry-point. The message's recipient is implemented by the plugin and
called a hook implementation. The hook implementation receives the message and can
decide whether to send a response or not. Then, the host gets the responses and can
choose whether to process all or just the first valid return.

In contrast to some other mechanisms to change the behavior of a program (like method
overriding and monkey patching), hooking excels at allowing multiple plugins to work
alongside each other.

It is the host's responsibility to design the entry-points in a way such that

- plugins can target very specific entry-points of the application and achieve their
  goal efficiently.
- many plugins can work alongside each other.
- the necessary knowledge about pytask to implement a plugin is somewhat proportional to
  the complexity of the plugin's provided functionality.

## References

[^id4]: [pluggy's documentation](https://pluggy.readthedocs.io/en/latest/).

[^id5]: [A talk by Floris Bruynooghe about pluggy and pytest](https://youtu.be/zZsNPDfOoHU).

[^id6]: [An introduction to pluggy by Kracekumar Ramaraju](https://kracekumar.com/post/build_plugins_with_pluggy).
