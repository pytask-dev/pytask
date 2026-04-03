<div class="termy">

```console

$ pytask lock clean
────────────────────────── Start pytask session ─────────────────────────
Platform: win32 -- Python 3.12.0, pytask 0.5.3, pluggy 1.3.0
Root: C:\Users\pytask-dev\git\my_project

The following stale lockfile entries would be removed:

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Lockfile entry                                                        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ <span class="termynal-dim">task_old_pipeline.py::</span>task_train_model                  │
│ <span class="termynal-dim">task_old_pipeline.py::</span>task_evaluate_model               │
└───────────────────────────────────────────────────────────────────────┘

Remove stale entry <span class="termynal-dim">task_old_pipeline.py::</span>task_train_model? Yes

Remove stale entry <span class="termynal-dim">task_old_pipeline.py::</span>task_evaluate_model?
  Yes
  No
❯ Remove all remaining entries
  Quit

<span class="termynal-success">Removed 2 stale lockfile entries.</span>
```

</div>
