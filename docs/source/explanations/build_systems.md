# Build Systems

## Why another build system?

There are a lot of build systems out there with existing communities who accumulated a
lot of experience over time. So why bother creating another build system?

pytask is created having a particular audience in mind. Many researchers are not
computer scientists first. Instead, they acquired some programming skills throughout
their careers. Thus, a build system must be extremely user-friendly and provide a
[steep learning curve](https://english.stackexchange.com/a/6226). Since pytask resembles
pytest in many ways, users have an easy time switching to pytask and feel more
comfortable and empowered.

pytask inherits many of pytest's best ideas. The most useful one is probably the debug
mode which enables users to jump right into the code where the error happened. It
shortens feedback loops, increases productivity, and facilitates error detection.

pytest provides the ideal architecture for a build system. Its plugin-based design
allows for customization at every level. A build system is a tool which can be deployed
in many different contexts whose requirements are not foreseeable by core developers.
Thus, it is important to enable users and developers to adjust pytask to their needs.
pytest with its 800+ plugins is a huge success story in this regard. In turn, pytask may
attract many people from different backgrounds who contribute back to the main
application and help the broader community.

## Alternatives

There are some alternatives to pytask which are listed below. The short descriptions
don't do them justice and you should check them out to see which build system is best
for you.

Feel free to contribute to this list and add points which made you chose some build
system over pytask. The list also serves as an inspiration for pytask to adopt features
present in other build systems.

### [snakemake](https://github.com/snakemake/snakemake)

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

### [ploomber](https://github.com/ploomber/ploomber)

General

- Strong focus on machine learning pipelines, training, and deployment.
- Integration with tools such as MLflow, Docker, AWS Batch.
- Tasks can be defined in yaml, python files, Jupyter notebooks or SQL.

Pros

- Conversion from Jupyter notebooks to tasks via
  [soorgeon](https://github.com/ploomber/soorgeon).
-

Cons

- Programming in Jupyter notebooks increases the risk of coding errors (e.g.
  side-effects).
- Supports parametrizations in form of cartesian products in `yaml` files, but not more
  powerful parametrizations.

### [Waf](https://waf.io)

Pros

- Mature library.
- Can be extended.

Cons

- Focus on compiling binaries, not research projects.
- Bus factor of 1.

### [nextflow](https://github.com/nextflow-io/nextflow)

-

### [Kedro](https://github.com/quantumblacklabs/kedro)

Pros

- Mature library, used by some institutions and companies. Created inside McKinsey.
- Provides the full package: templates, pipelines, deployment

### [pydoit](https://github.com/pydoit/doit)

General

- A general task runner which focuses on command line tools.
- You can think of it as an replacement for make.
- Powers Nikola, a static site generator.

### [Luigi](https://github.com/spotify/luigi)

General

- A build system written by Spotify.
- Designed for any kind of long-running batch processes.
- Integrates with many other tools like databases, Hadoop, Spark, etc..

Cons

- Very complex interface and a lot of stuff you probably don't need.
- [Development](https://github.com/spotify/luigi/graphs/contributors) seems to stall.

### [sciluigi](https://github.com/pharmbio/sciluigi)

sciluigi aims to be a lightweight wrapper around luigi.

Cons

- [Development](https://github.com/pharmbio/sciluigi/graphs/contributors) has basically
  stalled since 2018.
- Not very popular compared to its lifetime.

### [scipipe](https://github.com/scipipe/scipipe)

Cons

- [Development](https://github.com/scipipe/scipipe/graphs/contributors) slowed down.
- Written in Go.

### [Scons](https://github.com/SCons/scons)

Pros

- Mature library.

Cons

- Seems to have no plugin system.

### [pypyr](https://github.com/pypyr/pypyr)

General

- A general task-runner with task defined in yaml files.
