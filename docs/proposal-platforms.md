# Proposal - initial support for platforms

This will close [cylc-flow #3421](https://github.com/cylc/cylc-flow/issues/3421)
and partially address
[cylc-flow #2199](https://github.com/cylc/cylc-flow/issues/2199).

## Key functionality

* Introduce configuration and logic to recognise compute platforms in place of
  task hosts. This will resolve a number of issues.
  * In particular, this allows a compute cluster which can be accessed via
    multiple login nodes (remote hosts) to be treated as logical unit.
  * We will be able to configure multiple platforms which share the same remote
    hosts (including `localhost`).

* If a platform has a list of remote hosts then the list will be randomised and
  the host used for each operation on that platform (job submission, polling,
  log retrieval, etc) will be rotated. This should help balance the load. If a
  remote host becomes unavailable, try the next one in the list, until exhausted.
  This will handle remote hosts becoming unavailable after a job is submitted
  which is a major limitation of the current logic.

* It will be possible to specify the platform for a task as a list. For example,
  you may have 2 different HPC systems and you are happy for a task to run on
  either. The list will be randomised and the platforms tried in turn until
  successful job submission.
  * Note that the platform will be selected each time a job is run. If you
    specify a list of platforms, tasks must not assume that retries of that task
    will use the same platform.

* It will be possible to specify the platform as a command in the same way as we
  can currently specify remote hosts as a command. The command must return a
  valid plaftorm (or a list of valid platforms). We hope that this functionality
  will seldom be needed in the future (the main use at present is to select from
  a list of login nodes). However, there are still cases where this may be
  needed. For example running a command which:
  * Returns the platform which has the shortest queue time.
  * Chooses the platform according to the day of the week (perhaps you have a
    platform which can only be used at weekends?).

* Note: it will **not** be possible to specify the platform as an environment
  variable in the same way as we can currently specify remote hosts as an
  environment variable (e.g. `platform = $ROSE_ORIG_HOST`).
  * Unclear why we need this given the Jinja2 variables can be used?
  * Using `$ROSE_ORIG_HOST` relies on Rose specifying extra options to set this
    in `[cylc][environment]` which we should avoid if possible.

## Example platform configurations

```ini
[job platforms]
    [localhost]
        alternate names = desktop\d\d
        # remote hosts = platform name (default)
        # Note: "desktop01" and "desktop02" are both valid and distinct platforms
    [[sugar]]
        remote hosts = localhost
        batch system = slurm
    [[hpc]]
        alternate names = hpcl1, hpcl2
        remote hosts = hpcl1, hpcl2
        retrieve job logs = True
        batch system = pbs
        # Note: "hpcl1" and "hpcl2" are both valid platform names which are
        # equivalent to "hpc" (because "remote hosts" is set)
    [[hpc-bg]]
        remote hosts = hpcl1, hpcl2
        retrieve job logs = True
        batch system = background
```

Note:

* The default for `remote hosts` is the platform name and the `alternate names`
  for each platform can include patterns. This allows us to define many
  platforms in a single section and handles the case where you have a large
  number of separate servers which are identical in terms of their platform
  properties other than their host name.
* The names of all new and existing settings are subject to change until we
  release cylc 8.0. Initially names will be chosen which match current usage
  wherever possible. We intend to review all the config settings once we have
  the key functionality in place.
* The default platform is `localhost`. At cylc 7, any settings for `localhost`
  act as defaults for all other hosts but we do **not** propose doing this for
  platforms. The downside is more duplication if you need to override a
  particular setting for every platform but we think this is clearer and safer.

## Example platform usage

These are examples of how the platform may be assigned in the `[runtime]`
section for a job. They refer to the example platforms shown above.

`platform = desktop01`
* The simplest example. The job will be run on the remote host `desktop01`.

`platform = special`
* There is no platform named `special` defined so this will fail validation.

`platform = hpc`
* The host used will be chosen by rotation.

`platform = hpcl1`
* This is treated the same as specifying `platform = hpc`.

`platform = sugar, hpc`
* The platform used will be chosen at random.

`platform = hpc-bg`
* This uses the same remote hosts as `platform = hpc` but is treated separately.
  In this example the only difference is the `batch system` used but there could
  be other differences.

`platform = $(rose host-select linux)`
* No checking can be performed at validation so if the command does not return a
  valid platform this will result in a submit failure.

## Deprecation method

* You can't mix old with new. If `platform` is defined for any task then any
  settings in the `[remote]` or `[job]` sections of any task result in a
  validation failure.

* Any settings in the `[remote]` or `[job]` sections which have equivalent
  settings in the new runtime section are converted using the normal deprecate
  method. e.g. `[job] execution time limit`.

* The remaining `[remote]` & `[job]` settings are converted by searched for a
  matching platform. If there is none the conversion fails resulting in an
  error.

* For fixed remote hosts the conversion happens at load time and the lack of a
  matching platform results in a validation failure.

* For remote hosts defined as a command or an environment variable the
  remaining `[remote]` & `[job]` settings are stored and the conversion happens
  at job submission. In this case the lack of a matching platform results in a
  submission failure.

* The `[remote] host` setting is matched first by checking the platforms
  `remote hosts` setting. If this is not defined then the match is made against
  the valid platform names.
  * We may need special logic so that if `[remote] host` is set to the workflow
    server hostname then this is converted to `localhost` before matching
    occurs.

## Deprecation examples

```ini
[runtime]
    [[alpha]]
        [[[remote]]]
            host = localhost
        [[[job]]]
            batch system = background
        # => platform = localhost (set at load time)

    [[beta]]
        [[[job]]]
            batch system = slurm
        # => platform = sugar (set at load time)

    [[gamma]]
        [[[remote]]]
            host = $(rose host-select hpc)
            # assuming this returns "hpcl1" or "hpcl2"
        [[[job]]]
            batch system = pbs
        # => platform = hpc (set at job submission time)

    [[delta]]
        [[[remote]]]
            host = hpcl1
        [[[job]]]
            batch system = batchground
        # => platform = hpc-bg (set at load time)
```

## Enhancements to support rose suite-run functionality

Several additions to the platform support will be needed to support rose
suite-run functionality:

1. Installation of suites on platforms
   * We already have logic to install service files on remote platforms just
     before the first set of jobs is submitted to each platform or on suite
     reload. This system needs to be extended to other items of the suite.
   * Consider whether we can make this work on a filesystem rather than a
     platform basis?
     * Configure the id of the filesystem used on a particular platform
       (defaults to the platform name).
     * If multiple platforms share the same root filesystem then use a common
       id.
     * Would need to consider the case where the root filesystem is shared but
       log, work or share differ.

2. Support for moving the share, work & log directories to different locations
   with optional symlinks to the root directory. Similarly support for moving
   the root directory with symlink to the `cylc-run` directory.

## Further enhancements

There are a number of ideas for enhancements referenced in
[cylc-flow #2199](https://github.com/cylc/cylc-flow/issues/2199) which we will
not attempt to address in the initial implementation. These include:

* Specify whether the root filesystem on a platform is shared with the workflow
  server. Currently it is assumed to be separate so installation is attempted on
  all remote hosts. There is logic to detect that it is shared but it would be
  more efficient to configure this. Note: already covered if we install on a
  filesystem basis as discussed above.
* Define default directives for all jobs on a platform.
* Support task management commands (kill, poll) by platform.
* Hold all tasks that target a particular platform. Note: the use of multiple
  platforms and platforms specified via commands will complicate this.
* Limit the number of jobs submitted to a platform at any one time.
* Custom logic to invoke for collecting job accounting information when a job completes.
