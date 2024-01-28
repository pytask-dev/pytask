<div class="termy">

```console

$ pytask markers
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Marker                           ┃ Description                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pytask.mark.persist              │ Prevent execution of a task if all      │
│                                  │ products exist and even ifsomething has │
│                                  │ changed (dependencies, source file,     │
│                                  │ products). This decorator might be      │
│                                  │ useful for expensive tasks where only   │
│                                  │ the formatting of the file has changed. │
│                                  │ The state of the files which have       │
│                                  │ changed will also be remembered and     │
│                                  │ another run will skip the task with     │
│                                  │ success.                                │
│                                  │                                         │
│ pytask.mark.skip                 │ Skip a task and all its dependent tasks.│
│                                  │                                         │
│ pytask.mark.skip_ancestor_failed │ Internal decorator applied to tasks if  │
│                                  │ any of its preceding tasks failed.      │
│                                  │                                         │
│ pytask.mark.skip_unchanged       │ Internal decorator applied to tasks     │
│                                  │ which have already been executed and    │
│                                  │ have not been changed.                  │
│                                  │                                         │
│ pytask.mark.skipif               │ Skip a task and all its dependent tasks │
│                                  │ if a condition is met.                  │
│                                  │                                         │
│ pytask.mark.try_first            │ Try to execute a task a early as        │
│                                  │ possible.                               │
│                                  │                                         │
│ pytask.mark.try_last             │ Try to execute a task a late as         │
│                                  │ possible.                               │
└──────────────────────────────────┴─────────────────────────────────────────┘
```

</div>
