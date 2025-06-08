<div class="termy">

```console

$ pytask --pdb
────────────────────────── Start pytask session ─────────────────────────
Platform: win32 -- Python <span style="color: var(--termynal-blue)">3.12.0</span>, pytask <span style="color: var(--termynal-blue)">0.5.3</span>, pluggy <span style="color: var(--termynal-blue)">1.3.0</span>
Root: C:\Users\pytask-dev\git\my_project
Collected <span style="color: var(--termynal-blue)">1</span> task.

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Traceback >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
<span style="color: #f14c4c">╭───────────────────</span><span style="color: #f14c4c; font-weight: bold;"> Traceback </span><span style="color: #6c1e1e; font-weight: bold">(most recent call last)</span><span style="color: #f14c4c"> ─────────────────╮</span>
<span style="color: #f14c4c">│</span>                                                                       <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span> <span style="color: #e5e510">.../task_data_preparation.py</span>:<span style="color: var(--termynal-blue)">23</span> in <span style="color: #23d18b">task_create_random_data</span>            <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>                                                                       <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   20 │                                                                <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   21 │   df = pd.DataFrame({<span style="color: #e5e510">&quot;x&quot;</span>: x, <span style="color: #e5e510">&quot;y&quot;</span>: y})                          <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   22 │                                                                <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span> <span style="color: #f14c4c">❱</span> 23 │   <span style="color: #3b8eea">raise</span> <span style="color: #23d18b">Exception</span>                                              <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   24 │                                                                <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   25 │   df.to_pickle(produces)                                       <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">│</span>   26                                                                  <span style="color: #f14c4c">│</span>
<span style="color: #f14c4c">╰───────────────────────────────────────────────────────────────────────╯</span>
<span style="color: #f14c4c; font-weight: bold;">Exception</span>

>>>>>>>>>>>>>>>> PDB post_mortem (IO-capturing turned off) >>>>>>>>>>>>>>
> ...\git\my_project\task_data_preparation.py(23)task_create_random_data()
-> raise Exception
<span data-ty="input" data-ty-prompt="(Pdb)" data-ty-cursor="▋"></span>

```

</div>
