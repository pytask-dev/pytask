<div class="termy">

```console

$ pytask lock accept -k train --dry-run
────────────────────────── Start pytask session ─────────────────────────
Platform: win32 -- Python 3.12.0, pytask 0.5.3, pluggy 1.3.0
Root: C:\Users\pytask-dev\git\my_project
Collected 2 tasks.

The following recorded states would be updated:

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Task                                           ┃ Reason               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ <span class="termynal-dim">task_train.py::</span>task_train_model                │ task_change          │
│ <span class="termynal-dim">task_train.py::</span>task_evaluate_model             │ dependency_change    │
└────────────────────────────────────────────────┴──────────────────────┘

<span class="termynal-warning">No changes were written because --dry-run was used.</span>
```

</div>
