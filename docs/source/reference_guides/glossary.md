# Glossary

## Workflow management system { #workflow-management-system }

A workflow management system (WMF) provides an infrastructure for the set-up,
performance, and monitoring of a defined sequence of tasks.

## DAG { #dag }

A [directed acyclic graph (DAG)](https://en.wikipedia.org/wiki/Directed_acyclic_graph)
is a graph with a finite amount of nodes and edges which are connected such that no
circles exist.

## Host { #host }

The program which offers extensibility via entry-points.

## Entry-point { #entry-point }

Access points for plugins in the host program. At an entry-point, the host sends a
message which can be processed by plugins. Then, the plugins may respond.

## Plugin { #plugin }

A plugin is software which changes the behavior of the host program by processing the
message sent by the host at an entry-point. A plugin can consist of one or more
`hook implementations`.

## Hooking { #hooking }

See the reference guide on [pluggy](explanations/pluggy.md) or the more general
explanation on [Wikipedia](https://en.wikipedia.org/wiki/Hooking).

## Hook specification { #hook-specification }

Another term for `entry-point` when talking about hooking and pluggy.

## Hook implementation { #hook-implementation }

A part of the plugin which intercepts the message at one specific entry-point.

## Private function { #private-function }

A function whose name starts with an underscore. The function should only be used in the
module where it is defined.

## Public function { #public-function }

A function whose name does not start with an underscore. The function can be imported in
other modules.

## PyTree { #pytree }

A PyTree is a tree-like structure built out of tuples, lists, and dictionaries and other
container types if registered. Any other object that is not a registered container is
treated as a node in the tree.
