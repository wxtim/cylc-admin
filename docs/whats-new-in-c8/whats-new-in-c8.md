# What's New in Cylc 8

**A quick guide for Cylc 7 users.**

If you need help using Cylc 8 please post questions to the
[Cylc Forum](https://cylc.discourse.group/)


#### Cylc-8.0b0 beta preview release, 1 April 2021

Cylc 8 differs from Cylc 7 in many ways: architecture, scheduling
algorithm, security, UIs, and working practices, and more.

## Table of Contents

- [Backward Compatibility](#backward-compatibility)
- [Terminology and Config File Name](#terminology-and-config-file-name)
- [Architecture](#architecture)
- [Scheduling Algorithm](#scheduling-algorithm)
- [Task/Job Separation and Task States](#task-job-separation-and-task-states)
- [Window on the Workflow](#window-on-the-workflow)
- [Platform Awareness](#platform-awareness)
- [Graph Syntax](#graph-syntax)
- [Workflow Installation](#workflow-installation)
- [Safe Run Semantics](#safe-run-semantics)
- [Security](#security)
- [Packaging](#packaging)

Appendices:
- [What's Still Missing From Cylc 8](#whats-still-missing-from-cylc-8)
- [Cylc 7 Scheduling Deficiencies Fixed by Cylc 8
](#cylc-7-scheduling-deficiencies-fixed-by-cylc-8)

## Backward Compatibility
[TOP](#whats-new-in-cylc-8)

To make the transition easier, Cylc 8 can run Cylc 7 workflows out of the box.

*Please take action on any deprecation warnings though.*

## Terminology and Config File Name
[TOP](#whats-new-in-cylc-8)

- *Suite* is now **workflow**
  - (a more widely used and understood term)
- *suite daemon* (or *suite server program*) is now **scheduler**
  - (ditto)
- *batch system* is now **job runner**
  - (our job runners are not all "batch systems")
- the `suite.rc` config file is now called `flow.cylc`

## Architecture
[TOP](#whats-new-in-cylc-8)

Cylc has been re-architected to support a remote web UI:
- a new Hub component, where you authenticate
  - (can run as a regular user or privileged user)
- a new UI Server component that runs as the user
- new network layers to feed data from schedulers and
  filesystem, through the UI Server, to the UI
  - efficient incremental push updates (c.f. polled global updates in Cylc 7)
- a new in-browser UI
  - a front dashboard page with documentation links (etc.)
  - integrated gscan side-panel
  - responsive web design (from desktop to table to mobile)
  - a tabbed interface to display multiple workflow views
  - command integration, for interacting with task, jobs, and schedulers
- a new terminal UI (TUI) as part of the CLI

![title Cylc Hub](./img/hub.png)
<figcaption>Cylc8 WebUI login screen.</figcaption>

![title Cylc UI dash](./img/cylc-ui-dash.png)
<figcaption>Cylc 8 Web UI home screen.</figcaption>

![title Cylc UI tree](./img/cylc-ui-tree.png)
<figcaption>Cylc 8 Web UI tree view.</figcaption>

![title Cylc TUI](./img/cylc-tui.png)
<figcaption>Cylc 8 TUI (Text User Interface).</figcaption>

## Scheduling Algorithm
[TOP](#whats-new-in-cylc-8)

![Cylc Scheduling](./img/cycling.png)

Cylc 8 has a new *"spawn-on-demand"* scheduler to more efficiently manage
infinite workflows of repeating tasks.
- it only needs to be aware of current active tasks, and what comes next (very
  efficient)
- it handles alternate path branching without the need for suicide triggers
- it can run tasks out of cycle point order
- it enables a sensible active-task based window on the evolving workflow
- users no longer need to know about the "scheduler task pool" or "insertion"
  of task proxy objects into it
  - the `cylc insert` and `cylc reset` commands no longer exist
- **reflow:** you can trigger multiple "wavefronts" of activity at once, in the
  workflow graph.

## Task/Job Separation and Task States
[TOP](#whats-new-in-cylc-8)

A "task" represents a node in your abstract workflow graph. A job is a real
process that runs on a computer. Tasks can submit multiple jobs to run, through
automatic retries or manual re-triggering.

Cylc 7 had 13 task/job states. The GUI only showed tasks, with job data
from the latest task job.

Cylc 8 has only 8 task/job states. The Cylc 8 UI shows both task and jobs.
Task icons are monochrome circles; job icons are coloured squares. The running
task icon incorporates a radial progress indicator.

![](./img/task-job.png)

The missing Cylc 7 states are now just plain old *waiting*, but you can see
what the task is waiting on (e.g. queue, xtrigger, or retry). A waiting task
that already has a failed job associated with it must be about to retry, for
instance.

## Window on the Workflow

![](./img/n-window.png)

The Cylc UI can't show "all the tasks" at once - the graph may be infinite
in extent, after all, in cycling systems. The Cylc 8 UI shows:
- current **active tasks** (submitted, running, unhandled-failed)
  - plus waiting tasks that are only waiting on non-task dependencies:
    queues, runahead limit, clock-triggers, or xtriggers
- tasks up `n` (default `1`) graph edges away from active tasks

## Platform Awareness
[TOP](#whats-new-in-cylc-8)

Cylc 7 was aware of individual job hosts.

```ini
[runtime]
   [[model]]
       [[[remote]]]  # Deprecated Cylc 7
           host = hpc1.login.1
```

Cylc 8 is aware of sets of host settings, specified as *platforms*
in global configuration. By definition platform hosts share a file
system and job runner: If one host is unavailable Cylc 8 can use
other hosts on the same platform to interact with task jobs.

```ini
[runtime]
   [[model]]
       platform = hpc1  # Cylc 8
   [[model_cleanup]]
       # Platforms can have the same hosts with different job runners.
       platform = hpc1_background
```

## Graph Syntax
[TOP](#whats-new-in-cylc-8)

Cylc 7 had unnecessarily deep nesting of graph config sections:

```ini
[scheduling]
   initial cycle point = now
   [[dependencies]]  # Deprecated Cylc 7
       [[[R1]]]
           graph = "prep => foo"
       [[[R/^/P1D]]]
           graph = "foo => bar => baz"
```

Cylc 8 cleans this up:

```ini
[scheduling]
   initial cycle point = now
   [[graph]]  # Cylc 8
       R1 = "prep => foo"
       R/^/P1D = "foo => bar => baz"
```

## Workflow Installation
[TOP](#whats-new-in-cylc-8)

The functionality of `rose suite-run` has been migrated into Cylc 8. This
cleanly separates workflow source directory from run directory, and installs
workflow files into the run directory at start-up

- `cylc install` copies all workflow source files into a dedicated
  run-directory
- each new install creates a new numbered run-directory (by default)
- (workflow files are automatically installed onto job platforms too)

```bash
(venv) $ pwd
/home/oliverh/cylc-src/democ8

(venv) $ cylc install
INSTALLED democ8 from /home/oliverh/cylc-src/democ8 -> /home/oliverh/cylc-run/democ8/run1

(venv) $ cylc play democ8/run1
                ._.
                | |
    ._____._. ._| |_____.
    | .___| | | | | .___|       The Cylc Workflow Engine [8.0b0]
    | !___| !_! | | !___.           Copyright (C) 2008-2021 NIWA
    !_____!___. |_!_____!   & British Crown (Met Office) & Contributors.
          .___! |
          !_____!

...

(venv) $ cylc install
INSTALLED democ8 from /home/oliverh/cylc-src/democ8 -> /home/oliverh/cylc-run/democ8/run2

(venv) $ cylc play democ8/run2
# etc.
```

## Safe Run Semantics: `cylc play`
[TOP](#whats-new-in-cylc-8)

Cylc 7 run semantics were dangerous: if you accidentally typed `cylc run`
instead of `cylc restart` a new from-scratch run would overwrite the existing
run directory, including the run database, so that you could not go back and do
the intended restart.

Cylc 8 has `cylc play` to *start*, *restart*, or *unpause* a workflow, so
"restart" is now the safe default behaviour. For a new run from scratch,
do a fresh install and run it safely in the new run directory.

## Security
[TOP](#whats-new-in-cylc-8)

TBD...

## Packaging
[TOP](#whats-new-in-cylc-8)

Cylc 7 had to be installed by manually unpacking a release tarball and ensuring
that all software dependencies were installed on the system.

The Python components of Cylc 8 can be installed from PyPI into a Python 3 virtual
environment, using `pip`:

```bash
$ python3 -m venv venv
$ . venv/bin/activate
(venv) $ pip install cylc-flow
(venv) $ cylc --version
cylc-8.0b0

# ... and similarly for cylc-uiserver
```

The full Cylc 8 system, including the web UI, can be installed from Conda
Forge:

```bash
$ conda create -n cylc8 python=3.8
$ conda activate cylc8
(cylc8) $ conda install cylc
(cylc8) $ cylc --version
cylc-8.0b0
```

# Appendices

## What's Still Missing From Cylc 8
[TOP](#whats-new-in-cylc-8)

- UI dependency graph view, table view, dot view
- Cross-user functionality and fine-grained authorization
- Cylc Review, workflow and job log viewer
  - for the moment you can access job logs directly in the workflow run
    directory, or use Cylc Review from cylc-7.9.3 or 7.8.8 to view Cylc 8 logs.
- Documentation on various aspects of the system, such as how to spawn remote
  UI Servers from the Hub

## Cylc 7 Scheduling Deficiencies Fixed by Cylc 8
[TOP](#whats-new-in-cylc-8)

- every task had an implicit depedence on the job submission event of its
  own previous-instance (i.e. same task, previous cycle point)
- the scheduler had to be aware of at least one active and one waiting instance
  of every task in the workflow, plus all succeeded tasks in the current
  active task window
- the indiscriminate dependency matching process was costly
- to fully understand what tasks appeared in the GUI (why particular
  *waiting* or *succeeded* tasks appeared in some cycles but not in others, for
  instance) you had to understand the scheduling algorithm
- *suicide triggers* were needed to clear unused graph paths and avoid stalling
  the scheduler
- tasks could not run out of cycle point order, and workflows could stall
  due to next-cycle-point successors not being spawned downstream of failed tasks