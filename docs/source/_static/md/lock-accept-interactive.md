<div class="termy">

```console

$ pytask lock accept -k train
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

Accept recorded state for <span class="termynal-dim">task_train.py::</span>task_train_model? Yes

Accept recorded state for <span class="termynal-dim">task_train.py::</span>task_evaluate_model?
  Yes
  No
❯ Accept all remaining tasks
  Quit

<span class="termynal-success">Accepted recorded state for 2 task(s).</span>
```

</div>
