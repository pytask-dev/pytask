<div class="termy">

```console

$ pytask --log-cli --log-cli-level=INFO --show-capture=log
───────────────────────── Start pytask session ─────────────────────────
Platform: win32 -- Python 3.12.0, pytask 0.5.3, pluggy 1.3.0
Root: C:\Users\pytask-dev\git\my_project
Collected 2 tasks.

10:14:51 INFO     build:preparing report.txt
10:14:51 WARNING  build:publishing report is about to fail
╭───────────────────────────────────────────┬─────────╮
│ Task                                      │ Outcome │
├───────────────────────────────────────────┼─────────┤
│ <span class="termynal-dim">task_logging.py::</span>task_prepare_report      │ <span class="termynal-success">.      </span> │
│ <span class="termynal-dim">task_logging.py::</span>task_publish_report      │ <span class="termynal-failed">F      </span> │
╰───────────────────────────────────────────┴─────────╯

<span style="color: #bf2d2d">─────────────────────────────── Failures ───────────────────────────────</span>

<span style="color: #bf2d2d">─────────── Task </span><span style="color: #6c1e1e; font-weight: bold">task_logging.py::</span><span style="color: #bf2d2d">task_publish_report</span><span style="color: #bf2d2d"> failed ───────────</span>

<span style="color: #f14c4c">╭──────────────────</span><span style="color: #f14c4c; font-weight: bold;"> Traceback </span><span style="color: #6c1e1e; font-weight: bold">(most recent call last)</span><span style="color: #f14c4c"> ──────────────────╮</span>
<span style="color: #cd3131">│</span>                                                                       <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">...\git\my_project\task_logging.py</span>:<span style="color: #3b8eea">18</span> in <span style="color: #23d18b">task_publish_report</span>          <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>                                                                       <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   15 │   logger.warning(<span style="color: #e5e510">"publishing report is about to fail"</span>)         <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   16 │   print(<span style="color: #e5e510">"stdout from publish"</span>)                                 <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   17 │   sys.stderr.write(<span style="color: #e5e510">"stderr from publish\n"</span>)                    <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #cd3131">❱ </span>18 │   <span style="color: #3b8eea">raise</span> <span style="color: #23d18b">RuntimeError</span>(<span style="color: #e5e510">"simulated publish failure"</span>)              <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span>   19                                                                  <span style="color: #cd3131">│</span>
<span style="color: #cd3131">╰───────────────────────────────────────────────────────────────────────╯</span>
<span style="color: #f14c4c; font-weight: bold;">RuntimeError:</span> simulated publish failure

─────────────────────── Captured log during call ────────────────────────
10:14:51 WARNING  build:publishing report is about to fail
```

</div>
