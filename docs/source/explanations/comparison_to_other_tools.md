# Comparison to other tools

There exist some alternatives to pytask which are listed below. The short descriptions
don't do them justice and you should check them out to see which
{term}`workflow management system` (WFM) fits you and your use case best.

Feel free to contribute to this list and add points which you found particularly
favorable. The list also serves as an inspiration for pytask to adopt features present
in other WMFs.

## [snakemake](https://github.com/snakemake/snakemake)

Pros

- Very mature library and probably the most adapted library in the realm of scientific
  workflow software.
- Can scale to clusters and use Docker images.
- Supports Python and R.
- Automatic test case generation.

Cons

- Need to learn snakemake's syntax which is a mixture of Make and Python.
- No debug mode.
- Seems to have no plugin system.

## [ploomber](https://github.com/ploomber/ploomber)

General

- Strong focus on machine learning pipelines, training, and deployment.
- Integration with tools such as MLflow, Docker, AWS Batch.
- Tasks can be defined in yaml, python files, Jupyter notebooks or SQL.

Pros

- Conversion from Jupyter notebooks to tasks via
  [soorgeon](https://github.com/ploomber/soorgeon).

Cons

- Programming in Jupyter notebooks increases the risk of coding errors (e.g.
  side-effects).
- Supports parametrizations in form of cartesian products in `yaml` files, but not more
  powerful parametrizations.

## [Waf](https://waf.io)

Pros

- Mature library.
- Can be extended.

Cons

- Focus on compiling binaries, not research projects.
- Bus factor of 1.

## [nextflow](https://github.com/nextflow-io/nextflow)

- Tasks are scripted using Groovy which is a superset of Java.
- Supports AWS, Google, Azure.
- Supports Docker, Shifter, Podman, etc.

## [Kedro](https://github.com/kedro-org/kedro)

Pros

- Mature library, used by some institutions and companies. Created inside McKinsey.
- Provides the full package: templates, pipelines, deployment

## [pydoit](https://github.com/pydoit/doit)

General

- A general task runner which focuses on command line tools.
- You can think of it as an replacement for make.
- Powers Nikola, a static site generator.

## [Luigi](https://github.com/spotify/luigi)

General

- A build system written by Spotify.
- Designed for any kind of long-running batch processes.
- Integrates with many other tools like databases, Hadoop, Spark, etc..

Cons

- Very complex interface and a lot of stuff you probably don't need.
- [Development](https://github.com/spotify/luigi/graphs/contributors) seems to stall.

## [sciluigi](https://github.com/pharmbio/sciluigi)

sciluigi aims to be a lightweight wrapper around luigi.

Cons

- [Development](https://github.com/pharmbio/sciluigi/graphs/contributors) has basically
  stalled since 2018.
- Not very popular compared to its lifetime.

## [scipipe](https://github.com/scipipe/scipipe)

Cons

- [Development](https://github.com/scipipe/scipipe/graphs/contributors) slowed down.
- Written in Go.

## [Scons](https://github.com/SCons/scons)

Pros

- Mature library.

Cons

- Seems to have no plugin system.

## [pypyr](https://github.com/pypyr/pypyr)

General

- A general task-runner with task defined in yaml files.
