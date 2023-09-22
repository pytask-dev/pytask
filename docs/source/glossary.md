# Glossary

```{glossary}
workflow management system
    A workflow management system (WMF) provides an infrastructure for the set-up,
    performance and monitoring of a defined sequence of tasks.

DAG
    A [directed acyclic graph (DAG)](https://en.wikipedia.org/wiki/Directed_acyclic_graph)  is a graph with a finite amount of nodes and edges
    which are connected such that no circles exist.

host
    The program which offers extensibility via entry-points.

entry-point
    Access points for plugins in the host program. At an entry-point, the host sends
    a message which can be processed by plugins. Then, the plugins may respond.

plugin
    A plugin is a software which changes the behavior of the host program by
    processing the message send by the host at an entry-point. A plugin can consist
    of one or more {term}`hook implementations <hook implementation>`.

hooking
    See the reference guide on [pluggy](explanations/pluggy.md) or the more
    general explanation on [Wikipedia](https://en.wikipedia.org/wiki/Hooking).

hook specification
    Another term for {term}`entry-point` when talking about hooking and pluggy.

hook implementation
    A part of the plugin which intercepts the message at one specific entry-point.

private function
    A function whose name starts with an underscore. The function should
    only be used in the module where it is defined.

public function
    A function whose does not start with an underscore. The function can be imported
    in other modules.

PyTree
    A PyTree is a tree-like structure built out of tuples, lists, and dictionaries and
    other container types if registered. Any other object that is not a registered
    container is treated as a node in the tree.
```
