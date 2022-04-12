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

1. As long as you write your tasks in Python, you can use pytask to jump into the
   interactive debugger and inspect your tasks and programs to find errors in your code.

1. Even if your tasks are written in, e.g., R or Julia, pytask tries to feel like a seem

pytest provides the ideal architecture for a workflow management system. Its
plugin-based design allows for customization at every level. A workflow management
system is a tool which can be deployed in many different contexts whose requirements are
not foreseeable by core developers. Thus, it is important to enable users and developers
to adjust pytask to their needs. pytest with its 800+ plugins is a huge success story in
this regard. In turn, pytask may attract many people from different backgrounds who
contribute back to the main application and help the broader community.
