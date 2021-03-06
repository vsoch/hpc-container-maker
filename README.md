# HPC Container Maker

## Introduction

HPC Container Maker (HPCCM) generates container specification files,
either Dockerfiles or Singularity recipe files, based on a "recipe."
A recipe specifies the series of steps to be performed when building a
container.  The recipe format is described [elsewhere](RECIPES.md).
Recipes provide more portable, higher level building blocks that
separate the concerns of choosing what to include in a container from
the low level details of container specification.

## Why use container maker?

At first glance, the idea of specifying a container in a new,
non-native format may not seem worthwhile.  For small, simple
containers, this is probably true.  However, for larger, more complex
containers, there are 3 good reasons to use Container Maker recipes.

1. [Container implementation abstraction](#Container implementation
   abstraction)

2. [Availability of a full programming language](#Availability of a
   full programming language)

3. [Higher level abstraction](#Higher level abstraction), i.e.,
   building blocks

Recipes also address the combinatorial explosion problem as the number
of components and versions increase.

And as a bonus, there is absolutely no lock in.  Container Maker
generates human readable Dockerfiles and Singularity recipe files, so
you can always decide to revert to writing in a native container
specification format.

### Container implementation abstraction

The same recipe file generates specification files for Docker or
Singularity.  There is no need for separate development for each
container implementation you want to natively support.

For example, from this [single recipe](recipes/examples/basic.py)
both a Dockerfile and Singularity recipe file can be easily generated.
(Don't worry about the [syntax of a recipe](RECIPES.md) right now,
although as you can see it's straight forward.)

```python
Stage0.baseimage('ubuntu:16.04')
Stage0 += apt_get(ospackages=['gcc', 'g++', 'gfortran'])
```

```
FROM ubuntu:16.04

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        gfortran && \
    rm -rf /var/lib/apt/lists/*
```

```
BootStrap: docker
From: ubuntu:16.04

%post
    apt-get update -y
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        gfortran
    rm -rf /var/lib/apt/lists/*
```

### Availability of a full programming language

A recipe is Python code.  This means that you can use the full power
of Python in a recipe for conditional branching, input validation,
searching the web for the latest version of a component, etc.

For example, the LAMMPS application may be built in single, double, or
mixed precision mode.  The following will select and the validate the
precision based on a user supplied argument (`hpccm.py --userarg
LAMMPS_PRECISION=...`).

```python
# get and validate precision
VALID_PRECISION = ['single', 'double', 'mixed']
precision = USERARG.get('LAMMPS_PRECISION', 'single')
if precision not in VALID_PRECISION:
    raise ValueError('Invalid precision')

...

Stage0 += shell(commands=['make –f Makefile.linux.{}'.format(precision), ...])

...
```

A standalone [example](recipes/examples/userargs.py) is also provided.

### Higher level abstraction

While it is possible to write a recipe that corresponds nearly one for
one with a Dockerfile or Singularity recipe file, the Container Maker
provides higher level abstractions called building blocks to simplify
recipes and encapsulate best practices.

The first reason illustrates a simple case of installing OS packages.
OpenMPI is a more significant example; with a single recipe line, a
series of optimized Docker or Singularity instructions are generated.

```python
Stage0 += openmpi(cuda=True, infiniband=True,
                  prefix='/usr/local/openmpi', version='3.0.0')
```

```
# OpenMPI version 3.0.0
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        file \
        hwloc \
        openssh-client \
        wget && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /tmp && wget -q --no-check-certificate -P /tmp https://www.open-mpi.org/software/ompi/v3.0/downloads/openmpi-3.0.0.tar.bz2 && \
    tar -x -f /tmp/openmpi-3.0.0.tar.bz2 -C /tmp -j && \
    cd /tmp/openmpi-3.0.0 &&   ./configure --prefix=/usr/local/openmpi --disable-getpwuid --enable-orterun-prefix-by-default --with-cuda --with-verbs && \
    make -j4 && \
    make -j4 install && \
    rm -rf /tmp/openmpi-3.0.0.tar.bz2 /tmp/openmpi-3.0.0
ENV PATH=/usr/local/openmpi/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/openmpi/lib:$LD_LIBRARY_PATH
```

```
# OpenMPI version 3.0.0
%post
    apt-get update -y
    apt-get install -y --no-install-recommends \
        file \
        hwloc \
        openssh-client \
        wget
    rm -rf /var/lib/apt/lists/*
%post
    mkdir -p /tmp && wget -q --no-check-certificate -P /tmp https://www.open-mpi.org/software/ompi/v3.0/downloads/openmpi-3.0.0.tar.bz2
    tar -x -f /tmp/openmpi-3.0.0.tar.bz2 -C /tmp -j
    cd /tmp/openmpi-3.0.0 &&   ./configure --prefix=/usr/local/openmpi --disable-getpwuid --enable-orterun-prefix-by-default --with-cuda --with-verbs
    make -j4
    make -j4 install
    rm -rf /tmp/openmpi-3.0.0.tar.bz2 /tmp/openmpi-3.0.0
%environment
    export PATH=/usr/local/openmpi/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/openmpi/lib:$LD_LIBRARY_PATH
```

## How to Use Container Maker

Typically, Container Maker will be used in 1 of 2 scenarios.

### Template for by-hand customization

In this scenario, a base recipe containing the required core
components (e.g., OFED, OpenMPI) will be selected or created and used
to generate a template Dockerfile or Singularity recipe file.  The
base recipe contains everything needed up to, but not including the
application specification.  The application specification is then
added by-hand to the Dockerfile or Singularity recipe file which is
used to generate the container image.

HPC base recipe files, containing commonly-required core HPC
components, are included for the [GNU](recipes/hpcbase-gnu.py) and
[PGI](recipes/hpcbase-pgi.py) compilers.

The workflow for this scenario follows.

1. Generate a preliminary Dockerfile, e.g., `hpccm.py --recipe recipes/hpcbase-gnu.py > Dockerfile`.

2. Add the HPC application specific build steps to the Dockerfile from
   step 1.

3. Build the Docker container, e.g., `docker build -t myapp -f Dockerfile .`.

4. Run the Docker container, e.g., `nvidia-docker run --rm -ti myapp`.

A variant of this scenario is to use the base recipe to generate a
base image containing the required core components.  The resulting
image can then be referenced from a Dockerfile or Singularity recipe
file.

The workflow for this scenario variant follows.

1. Generate a base image Dockerfile, e.g., `hpccm.py --recipe recipes/hpcbase-gnu.py > Dockerfile.base`.

2. Generate a Docker image, e.g., `docker build -t base -f Dockerfile.base .`.

3. Create a Dockerfile that references the base image from step 2 and
   contains the HPC application specific build steps.

4. Build the Docker container, e.g., `docker build -t myapp -f Dockerfile .`.

5. Run the Docker container, e.g., `nvidia-docker run --rm -ti myapp`.

### Full container specification

In this scenario the application itself is included in the Container
Maker recipe.

Some sample recipe files for applications are included with the tool.
Note that some of these recipes may depend on certain files in the
build context and may not build without them.

A sample workflow for this scenario follows.

1. Generate a Dockerfile, e.g., `hpccm.py --recipe recipes/chroma.py > Dockerfile`

2. Generate a Docker image, e.g., `docker build -t chroma -f Dockerfile .`.

3. Run the Docker container, e.g., `nvidia-docker run --rm -ti chroma`.

## Creating Singularity Images

There are two ways to create Singularity images, one using Docker and
the other using Singularity natively.

If container image size is a concern and multi-stage recipes are being
used, the Docker-based workflow must be used.

### Docker-based workflow

1. Generate a Dockerfile from the recipe.  E.g., `hpccm.py --recipe recipes/examples/basic.py > Dockerfile`

2. Build the Docker container. E.g., `docker build -t basic -f Dockerfile .`

3. Convert the container to a Singularity image.  E.g.,
`docker run -t --rm --privileged -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/output singularityware/docker2singularity basic`

### Singularity native workflow

1. Generate a Singularity recipe file.  E.g., `hpccm.py --recipe recipes/examples/basic.py --format singularity > Singularity`

2. Build the Singularity container. E.g., `sudo singularity build basic.simg Singularity`

## Usage

### Command line options

- `--format`: specify the container format to output.  The choices are
  `docker` and `singularity`; `docker` is the default.

- `--help`: print usage information and exit.

- `--single-stage`: process only the first stage of a multi-stage
  recipe.

- `--recipe`: specify the path to the recipe file.  See the
  [recipes](recipes) sub-directory for some example recipes.

- `--userarg`: specify one or more key / value pairs that are passed
  through to the recipe as a dictionary named `USERARG`.

## Current Limitations

- Supports Ubuntu-based containers only

- Singularity does not support multi-stage containers.  This is a
  limitation of Singularity itself, not Container Maker.  Only the
  first stage of a multi-stage recipe will be generated for
  Singularity.

- Native Singularity support is experimental

## TODO

- Additional building blocks and templates

- Support CentOS-based containers

- Code and interface cleanup
