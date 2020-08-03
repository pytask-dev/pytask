Design
======

The design of pytask has some key objectives.

1. The interface must be simple, easy-to-learn, and may have synergies with pytest. It
   is important that even users without a strong background in computer science are able
   to use pytask.

2. pytask must be easily extensible via plugins. Developers of pytask are naturally
   unaware of all the possible applications of a build system. Thus, they must focus on
   the host application and the design of the entry-points. This will also reduce the
   amount of maintenance.
