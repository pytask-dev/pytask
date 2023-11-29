# Interfaces for dependencies and products

There are different interfaces for dependencies and products and it might be confusing
when to use what. The tables gives you an overview to decide which interface is most
suitable for you.

## Legend

- ✅ = True
- ❌ = False
- ➖ = Does not apply

## Products

|                                                           | `Annotated[..., PNode, Product]` | `produces` | `@task(produces=...)` | `def task() -> Annotated[..., PNode]` | `@pytask.mark.produces(...)` |
| --------------------------------------------------------- | :------------------------------: | :--------: | :-------------------: | :-----------------------------------: | :--------------------------: |
| Not deprecated                                            |                ✅                 |     ✅      |           ✅           |                   ✅                   |              ❌               |
| No type annotations required                              |                ❌                 |     ✅      |           ✅           |                   ❌                   |              ✅               |
| Flexible choice of argument name                          |                ✅                 |     ❌      |           ✅           |                   ➖                   |              ❌               |
| Supports third-party functions as tasks                   |                ❌                 |     ❌      |           ✅           |                   ❌                   |              ❌               |
| Allows to pass custom node while preserving type of value |                ✅                 |     ✅      |           ✅           |                   ✅                   |              ✅               |

## Dependencies

|                                         | `Annotated[..., PNode]` | `@task(kwargs=...)` | `@pytask.mark.depends_on(...)` |
| --------------------------------------- | :---------------------: | :-----------------: | :----------------------------: |
| Not deprecated                          |            ✅            |          ✅          |               ❌                |
| No type annotations required            |            ❌            |          ✅          |               ✅                |
| Flexible choice of argument name        |            ✅            |          ✅          |               ❌                |
| Supports third-party functions as tasks |            ❌            |          ✅          |               ❌                |
