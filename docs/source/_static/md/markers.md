<div class="termy">

```console

$ pytask markers
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Marker                           ┃ Description                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pytask.mark.depends_on           │ Add dependencies to a task. See this    │
│                                  │ tutorial for more information:          │
│                                  │ <a href="https://bit.ly/3JlxylS">https://bit.ly/3JlxylS</a>.                 │
│                                  │                                         │
│ pytask.mark.parametrize          │ The marker for pytest&#x27;s way of          │
│                                  │ repeating tasks which is explained in   │
│                                  │ this tutorial: <a href="https://bit.ly/3uqZqkk">https://bit.ly/3uqZqkk</a>.  │
│                                  │                                         │
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
│ pytask.mark.produces             │ Add products to a task. See this        │
│                                  │ tutorial for more information:          │
│                                  │ <a href="https://bit.ly/3JlxylS">https://bit.ly/3JlxylS</a>.                 │
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
│ pytask.mark.task                 │ Mark a function as a task regardless of │
│                                  │ its name. Or mark tasks which are       │
│                                  │ repeated in a loop. See this tutorial   │
│                                  │ for more information:                   │
│                                  │ <a href="https://bit.ly/3DWrXS3">https://bit.ly/3DWrXS3</a>.                 │
│                                  │                                         │
│ pytask.mark.try_first            │ Try to execute a task a early as        │
│                                  │ possible.                               │
│                                  │                                         │
│ pytask.mark.try_last             │ Try to execute a task a late as         │
│                                  │ possible.                               │
└──────────────────────────────────┴─────────────────────────────────────────┘
```

</div>
