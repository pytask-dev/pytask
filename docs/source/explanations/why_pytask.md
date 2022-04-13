# Why pytask?

There are a lot of workflow management systems out there with existing communities who
accumulated a lot of experience over time. So why bother creating another workflow
management system?

pytask is created having a particular audience in mind. Many researchers are not
computer scientists first. Instead, they acquired some programming skills throughout
their careers. Thus, a workflow management system must be extremely user-friendly and
provide a [steep learning curve](https://english.stackexchange.com/a/6226).

pytask tries to address this point in many ways.

1. pytask is written in Python which is one of the most popular and fastest growing
   languages in the realm of scientific computing.

1. For those who know pytest, the main testing framework in Python, pytask will look
   extremely familiar and you will feel productive quickly. If you do not know pytest,
   you will learn two tools at the same time.

1. pytask tries to improve your productivity by offering a couple of features like
   {doc}`repeating tasks <../tutorials/repeating_tasks_with_different_inputs>`,
   {doc}`debugging of tasks <../tutorials/debugging>` and
   {doc}`selecting subsets of tasks <../tutorials/selecting_tasks>`.

1. pytask integrates with other tools which are used in the scientific community such as
   R and Julia and offers solutions to bridge the gap between a
   {term}`workflow management system` written in Python and scripts in another language,
   for example, by making paths to dependencies and products usable in the scripts.

1. The plugin system let's power users tailor pytask to their needs by adding additional
   functionality. It makes pytask extremely versatile and offers people from different
   backgrounds to collaborate on the same software.
