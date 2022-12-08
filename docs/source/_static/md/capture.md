<div class="termy">

```console

$ pytask
──────────────────────────── Start pytask session ────────────────────────────
Platform: win32 -- Python <span style="color: var(--termynal-blue)">3.10.0</span>, pytask <span style="color: var(--termynal-blue)">0.2.0</span>, pluggy <span style="color: var(--termynal-blue)">1.0.0</span>
Root: C:\Users\pytask-dev\git\my_project
Collected <span style="color: var(--termynal-blue)">2</span> tasks.

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Task                         ┃ Outcome ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ <span class="termynal-dim">task_capture.py::</span>task_func1  │ <span class="termynal-success">.      </span> │
│ <span class="termynal-dim">task_capture.py::</span>task_func2  │ <span class="termynal-failed">F      </span> │
└──────────────────────────────┴─────────┘

<span style="color: #bf2d2d">────────────────────────────────── Failures ──────────────────────────────────</span>

<span style="color: #bf2d2d">─────────────────── Task </span><span style="color: #6c1e1e; font-weight: bold">task_capture.py::</span><span style="color: #bf2d2d">task_func2</span><span style="color: #bf2d2d"> failed ──────────────────</span>

<span style="color: #f14c4c">╭─────────────────────</span><span style="color: #f14c4c; font-weight: bold;"> Traceback </span><span style="color: #6c1e1e; font-weight: bold">(most recent call last)</span><span style="color: #f14c4c"> ────────────────────╮</span>
<span style="color: #cd3131">│</span>                                                                            <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">...\git\pytask-examples\task_capture.py</span>:<span style="color: #3b8eea">13</span> in <span style="color: #23d18b">task_func2</span>                   <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>                                                                            <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   10                                                                       <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   11 <span style="color: #3b8eea">def</span> <span style="color: #23d18b">task_func2</span>():                                                     <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   12 │   <span style="color: #29b8db">print</span>(<span style="color: #e5e510">&quot;Debug statement&quot;</span>)                                          <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #cd3131">❱ </span>13 <span style="font-size: .2em;">&thinsp;</span>│   <span style="color: #3b8eea">assert</span> <span style="color: #3b8eea">False</span>                                                      <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   14                                                                       <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   15                                                                       <span style="color: #cd3131">│</span>
<span style="color: #cd3131">╰────────────────────────────────────────────────────────────────────────────╯</span>
<span style="color: #f14c4c; font-weight: bold;">AssertionError</span>

──────────────────────── Captured stdout during call ─────────────────────────
Debug Statement

<span class="termynal-dim">──────────────────────────────────────────────────────────────────────────────</span>
<span style="color: #bf2d2d">╭─────────── </span><span style="font-weight: bold;">Summary</span><span style="color: #bf2d2d"> ───────────╮</span>
<span style="color: #bf2d2d">│</span> <span style="font-weight: bold"> 2  Collected tasks          </span> <span style="color: #bf2d2d">│</span>
<span style="color: #bf2d2d">│</span> <span class="termynal-success-textonly"> 1  Succeeded        (50.0%) </span> <span style="color: #bf2d2d">│</span>
<span style="color: #bf2d2d">│</span> <span class="termynal-failed-textonly"> 1  Failed           (50.0%) </span> <span style="color: #bf2d2d">│</span>
<span style="color: #bf2d2d">╰───────────────────────────────╯</span>
<span style="color: #bf2d2d">─────────────────────────── Failed in 0.03 seconds ───────────────────────────</span>
```

</div>
