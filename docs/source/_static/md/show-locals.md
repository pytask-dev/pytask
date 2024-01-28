<div class="termy">

```console

$ pytask --show-locals
──────────────────────────── Start pytask session ────────────────────────────
Platform: win32 -- Python <span style="color: var(--termynal-blue)">3.10.0</span>, pytask <span style="color: var(--termynal-blue)">0.4.0</span>, pluggy <span style="color: var(--termynal-blue)">1.3.0</span>
Root: C:\Users\pytask-dev\git\my_project
Collected <span style="color: var(--termynal-blue)">1</span> task.

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Task                                                ┃ Outcome ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ <span class="termynal-dim">task_create_random_data.py::</span>task_create_random_data │ <span class="termynal-failed">F      </span> │
└─────────────────────────────────────────────────────┴─────────┘

<span style="color: #bf2d2d">────────────────────────────────── Failures ──────────────────────────────────</span>

<span style="color: #bf2d2d">─────── Task </span><span style="color: #6c1e1e; font-weight: bold">task_create_random_data.py::</span><span style="color: #bf2d2d">task_create_random_data</span><span style="color: #bf2d2d"> failed ──────</span>

<span style="color: #f14c4c">╭─────────────────────</span><span style="color: #f14c4c; font-weight: bold;"> Traceback </span><span style="color: #6c1e1e; font-weight: bold">(most recent call last)</span><span style="color: #f14c4c"> ────────────────────╮</span>
<span style="color: #cd3131">│</span>                                                                            <span style="color: #cd3131">│</span>
<span style="color: #f14c4c">│</span> <span style="color: #e5e510">.../task_data_preparation.py</span>:<span style="color: var(--termynal-blue)">23</span> in <span style="color: #23d18b">task_create_random_data</span>                 <span style="color: #f14c4c">│</span>
<span style="color: #cd3131">│</span>                                                                            <span style="color: #cd3131">│</span>
<span style="color: #f14c4c">│</span>   20 │                                                                     <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   21 │   df = pd.DataFrame({<span style="color: #e5e510">&quot;x&quot;</span>: x, <span style="color: #e5e510">&quot;y&quot;</span>: y})                               <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   22 │                                                                     <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span> <span style="color: #f14c4c">❱</span> 23 <span style="font-size: .2em;">&thinsp;</span>│   <span style="color: #3b8eea">raise</span> <span style="color: #23d18b">Exception</span>                                                   <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   24 │                                                                     <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   25 │   df.to_pickle(produces)                                            <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   26                                                                       <span style="color: #f14c4c">│</span>
<span style="color: #cd3131">│</span>                                                                            <span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">╭──────────────────────────────── locals ─────────────────────────────────╮</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>     beta = <span style="color: #3b8eea">2</span>                                                            <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>       df =            x          y                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>            <span style="color: #3b8eea">0</span>   <span style="color: #3b8eea">6.257302</span>  <span style="color: #3b8eea">12.876199</span>                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>            <span style="color: #3b8eea">1</span>   <span style="color: #3b8eea">3.678951</span>   <span style="color: #3b8eea">8.661903</span>                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>            <span style="color: #3b8eea">2</span>  <span style="color: #3b8eea">11.404227</span>  <span style="color: #3b8eea">23.755534</span>                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>            <span style="color: #3b8eea">3</span>   <span style="color: #3b8eea">6.049001</span>  <span style="color: #3b8eea">11.394267</span>                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>            <span style="color: #3b8eea">4</span>  <span style="color: #3b8eea">-0.356694</span>  <span style="color: #3b8eea">-1.978809</span>                                      <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>  epsilon = <span style="color: #bc3fbc">array</span>([ <span style="color: #3b8eea">0.36159</span>,  <span style="color: #3b8eea">1.30400</span>,  <span style="color: #3b8eea">0.94708</span>, <span style="color: #3b8eea">-0.70373</span>, <span style="color: #3b8eea">-1.26542</span>])    <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span> produces = <span style="color: #bc3fbc">WindowsPath</span>(<span style="color: #e5e510">&#x27;C:/Users/pytask-dev/git/my_project/data.pkl&#x27;</span>)   <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>      rng = <span style="color: #bc3fbc">Generator</span>(PCG64) at <span style="color: #3b8eea">0x20987EC6340</span>                            <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>        x = <span style="color: #bc3fbc">array</span>([ <span style="color: #3b8eea">6.25730</span>,  <span style="color: #3b8eea">3.67895</span>, <span style="color: #3b8eea">11.40422</span> ,  <span style="color: #3b8eea">6.04900</span>, <span style="color: #3b8eea">-0.35669</span>])   <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">│</span>        y = <span style="color: #bc3fbc">array</span>([<span style="color: #3b8eea">12.87619</span>,  <span style="color: #3b8eea">8.66190</span>, <span style="color: #3b8eea">23.75553</span>, <span style="color: #3b8eea">11.39426</span>, <span style="color: #3b8eea">-1.97880</span>])    <span style="color: #e5e510">│</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">│</span> <span style="color: #e5e510">╰─────────────────────────────────────────────────────────────────────────╯</span><span style="color: #cd3131">│</span>
<span style="color: #cd3131">╰────────────────────────────────────────────────────────────────────────────╯</span>
<span style="color: #f14c4c; font-weight: bold;">Exception</span>

<span class="termynal-dim">──────────────────────────────────────────────────────────────────────────────</span>
<span style="color: #bf2d2d">╭─────────── </span><span style="font-weight: bold;">Summary</span><span style="color: #bf2d2d"> ────────────╮</span>
<span style="color: #bf2d2d">│</span> <span style="font-weight: bold"> 1  Collected tasks           </span> <span style="color: #bf2d2d">│</span>
<span style="color: #bf2d2d">│</span> <span class="termynal-failed-textonly"> 1  Failed           (100.0%) </span> <span style="color: #bf2d2d">│</span>
<span style="color: #bf2d2d">╰────────────────────────────────╯</span>
<span style="color: #bf2d2d">─────────────────────────── Failed in 0.01 seconds ───────────────────────────</span>
```

</div>
