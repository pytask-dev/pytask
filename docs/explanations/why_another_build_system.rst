Why another build system?
=========================

There are a lot of build systems out there with existing communities who accumulated a
lot of experience over time. So why go through the hassle of creating another build
system?

One reason was pure curiosity. `Waf <https://waf.io>`_ has been used for some time as a
build system for research projects. Although, it has several limitations (difficult
interface, no debugging, cryptic error messages, a bus factor of one), it is also a
mature library. At some point annoyance won over comfort and I (`@tobiasraabe
<https://github.com/tobiasraabe>`_) started to write pytask.

Another reason is that pytask is created having a particular audience in mind. Many
researchers are not computer scientists first, but acquired some programming skills
throughout their careers. This means a build system must be extremely user-friendly or
provide a `steep learning curve <https://english.stackexchange.com/a/6226>`_, because it
is only a tool. Since pytask resembles pytest in some ways, users have an easier time
switching to pytask and feel more comfortable.

The third reason is that pytest seems to provide the ideal architecture for a build
system. Its plugin-based design allows for customization at every level. A build system
is a tool which can be deployed in many different environments whose requirements are
not foreseeable by the developer. If it is easy for users / developers to write plugins
which extend the functionality of pytask it is more valuable. If there is any question
whether pytest's architecture is really suited for this, one should look at the success
of pytest, its wide-spread adoption, and its over 800 plugins (even if most of them
might be dead).


Alternatives
------------

Here is a list of other build systems and their advantages and disadvantages compared to
pytask. The list helps to define pytask's niche and to collect new ideas to improve
pytask.


`snakemake <https://github.com/snakemake/snakemake>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pros

- Mature library.
- Is the build system for some research projects.
- Can scale to clusters and use Docker images.
- Supports Python and R.

Cons

- Need to learn snakemake's syntax which is a mixture of Make and Python.
- Seems to have no plugin system.


`Waf <https://waf.io>`_
~~~~~~~~~~~~~~~~~~~~~~~

Pros

- Mature library.
- Can be extended.

Cons

- Focus on compiling binaries.
- Bus factor of 1.


`Luigi <https://github.com/spotify/luigi>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A build system written by Spotify.

Derivatives:

- `sciluigi <https://github.com/pharmbio/sciluigi>`_


`scipipe <https://github.com/scipipe/scipipe>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cons

- written in Go.


`Scons <https://github.com/SCons/scons>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pros

- Mature library.

Cons

- Seems to have no plugin system.


`cook <https://github.com/jachris/cook>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pros

- Still simple, maybe useful for some quick inspirations.

Cons

- Development is paused.
- No plugin system, but extensible interfaces.
