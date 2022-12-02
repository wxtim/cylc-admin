# PROPOSAL: A New Command for Manual Task Forcing


## Background

Users need to be able to intervene and affect the progression of workflows.

Currently we only have `cylc set-ouputs` which doesn't cover all requirements.
(And note it does not actually set task outputs: it just spawns downstream
children with corresponding prerequisites set).


### Task Status Reset is Not Needed

I am proposing that we do NOT support Cylc 7 style task status reset, e.g.
resetting a task from `failed` to `succeeded`.

Task status is more diagnostic than prognostic in the spawn-on-demand
scheduler. (In Cylc 7 the task status determined which tasks engaged in
dependency matching). 

Run history will be clearer if a task's status reflects what happened when
its job ran (or did not run). Users can then tell the scheduler to carry on *as
if* something else had happened, which should be recorded in the database too.


## Requirements

Force set specified **prerequisites** of a target task
  - (We might not want all children of the parent task outputs)
  - This is not the same as setting the parent output, unless the task is an
    only child
  - This is not the same as triggering, unless the task has only one
    unsatisfied prerequisite

Force set specified **outputs** (and **implied outputs**) of a target task
  - Sets the corresponding prerequisites of child tasks
  - And sets target task outputs (with any implied outputs) - contributes to
    **completion** of incomplete tasks
  - If the `succeeded` output gets set, disable automatic retries

Force expire tasks
  - Allows the scheduler to forget incomplete tasks without completing them 
  - Makes `cylc remove` obsolete
  - This *results* in a state change to expired, but we shouldn't consider it a
    manual reset to that state [see Expired Tasks below]


## The New Command

```
$ cylc set [OPTIONS] [TASK(S)]

Command for intervening in task prerequisite, output, and completion status.

Setting a prerequisite contributes to the task's readiness to run.

Setting an output contributes to the task's completion, and sets the
corresponding prerequisites of child tasks.

Setting a future waiting task to expire allows the scheduler to forget it
without running it.

Setting a finished but incomplete task to expire allows the scheduler to forget
it without rerunning it to complete its required outputs.

Setting an output also results in any implied outputs being set:
 - started implies submitted
 - succeeded, failed, and custom outputs, imply started
 - succeeded implies all required custom outputs
 - failed does not imply custom outputs

[OPTIONS]

   --flow=INT`: flow(s) to attribute spawned tasks. Default: all active flows.
      If a task already spawned, merge flows.

   --pre=PRE: set a prerequisite to satisfied (multiple use allowed).

   --pre=all: set all prerequisites to satisfied. Equivalent to trigger.

   --out=OUT: set an output (and implied outputs) to completed (multiple use allowed).

   --out=all or [no-options]: set all required outputs.

   `--expire`: allow the scheduler to forget a task without running it, or
      without rerunning it if incomplete.

```



## QUESTIONS

### Should `expired` be a task attribute, not a state?

`Expired` should really be a task attribute. That would make it easier
to distinbuish between waiting tasks that expire without running (whether
naturally or forced), and incomplete tasks that were force-expired without
being re-run to achieve completion.

I don't think users are deeply invested in the expired state.


### Un-setting prerequisites?

If a task has already run, it's prerequisites have already been "used". There's
no point in unsatisfying them.

Is there a case for unsatisfying prerequisites of tasks with multiple
prerequisites that have not run yet?


### Un-completing outputs?

Normally there's no point in unsetting a completed output. Any downstream
action will have already been triggered (on demand), except in a flow-wait
scenario.


## Example Use Cases


### 1. Forget an incomplete failed task

Expire it.


### 2. Carry on as if a failed task had succeeded

E.g. `foo` failed and is incomplete, but I fixed some files externally
so the workflow can carry on as if it had succeeded.

Set the task's `succeeded` output, to:
- spawn children of that output, with the corresponding prerequisite set
- complete the task, so scheduler can forget it

The database will record:
- `foo` state `failed`, and with the `failed` output
- then `foo:succeeded` set by manual forcing


### 3. Trigger a new flow downstream of target task 

`foo => post<m>`

If we don't want to run `foo` again, setting `foo:succeed` (for a new flow) is
more convenient than triggering all the downstream children individually.

This will spawn all `post<m>` at once, with prerequisite `foo:succeed` satisfied.


### 4. Set off-flow prerequisites, to prep for a new flow

If a flow is not entirely self-contained, you can prime the appropriate tasks
before triggering the flow, by either (whichever is more convenient):
- setting their off-flow prerequisites, or
- setting the parent outputs of the off-flow prerequisites

(Note this is more than a convenient alternative to `cylc trigger` because the
flow needs to progress according to the graph edges, and we don't want to
trigger the off-low parent tasks just to provide the off-flow prerequisites).


### 5. Skip to next cycle after externally-caused failures

Many tasks failed due to (say) external disk error. I want to start over at the
next cycle point rather than re-run the failed tasks.

- Trigger a new flow from next cycle (using `cylc trigger` or `cylc set`)
- Expire all the incomplete failed tasks so the scheduler can forget them


### 6.?? Set jobs to failed when a job platform is known to be down

I don't think this case is valid.

If jobs were submitted already they will have already failed naturally.
Otherwise, you can prevent job submission by holding the tasks, or expiring
them if necessary.


### 7.?? Set switch tasks at an optional branch point, to direct the future flow

I'm not sure this is valid either. Why would we need to do this?

```
foo:x? => bar  # take this branch regardless of x or y at run time?
foo:y? => baz

# or:

foo:fail? => bar  # take this branch regardless of succeed or fail at run time?
foo? => baz
```

Should `foo` still run when the flow reaches it, but only trigger the right
branch regardless of what outputs it completes? That amounts to "the graph is
wrong"!

Or do we want to pretend that `foo` has run already and generated the chosen
output, but don't flow on from there until the flow catches up?

In that case: `cylc broadcast` to change the `script` to simply send the chosen
output and exit.