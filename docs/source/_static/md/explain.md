<div class="termy">

```console

$ pytask --explain
────────────────────────── Start pytask session ─────────────────────────
Platform: darwin -- Python <span style="color: var(--termynal-blue)">3.12.0</span>, pytask <span style="color: var(--termynal-blue)">0.5.6</span>, pluggy <span style="color: var(--termynal-blue)">1.6.0</span>
Root: /Users/pytask-dev/git/my_project
Collected <span style="color: var(--termynal-blue)">3</span> tasks.

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Task                                              ┃ Outcome ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ <span class="termynal-dim">task_data.py::</span>task_create_data                    │ <span class="termynal-success">w</span>       │
│ <span class="termynal-dim">task_analysis.py::</span>task_analyze                    │ <span class="termynal-success">w</span>       │
│ <span class="termynal-dim">task_plot.py::</span>task_plot                           │ <span class="termynal-dim">s</span>       │
└───────────────────────────────────────────────────┴─────────┘

<span class="termynal-dim">─────────────────────────────────────────────────────────────────────────</span>
<span style="color: var(--termynal-blue); font-weight: bold;">────────────────────────────── Explanation ──────────────────────────────</span>

<span class="termynal-success">─── Tasks that would be executed ────────────────────────────────────────</span>

<span style="font-weight: bold;">task_data.py::task_create_data</span>
  • task_data.py::task_create_data: Changed

<span style="font-weight: bold;">task_analysis.py::task_analyze</span>
  • Preceding task_data.py::task_create_data would be executed

<span class="termynal-skipped">─── Skipped tasks ───────────────────────────────────────────────────────</span>

<span style="font-weight: bold;">task_plot.py::task_plot</span>
  • Skipped by marker

1 persisted task(s) (use -vv to show details)

<span class="termynal-dim">─────────────────────────────────────────────────────────────────────────</span>
<span class="termynal-success">╭───────────</span> <span style="font-weight: bold;">Summary</span> <span class="termynal-success">──────────────╮</span>
<span class="termynal-success">│</span> <span style="font-weight: bold;"> 3  Collected tasks </span>             <span class="termynal-success">│</span>
<span class="termynal-success">│</span> <span class="termynal-success-textonly"> 2  Would be executed  (66.7%)  </span> <span class="termynal-success">│</span>
<span class="termynal-success">│</span> <span class="termynal-dim-textonly"> 1  Skipped           (33.3%)   </span> <span class="termynal-success">│</span>
<span class="termynal-success">╰──────────────────────────────────╯</span>
<span class="termynal-success">─────────────────────── Succeeded in 0.02 seconds ───────────────────────</span>
```

</div>
