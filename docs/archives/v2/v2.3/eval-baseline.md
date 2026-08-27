# nexus-code-search eval report

Aggregate recall: **100.0%** Aggregate precision: **100.0%**

## Per-fixture

| Fixture | Questions | Recall | Precision |
|---------|-----------|--------|-----------|
| c_app | 5 | 100.0% | 100.0% |
| cpp_app | 5 | 100.0% | 100.0% |
| csharp_app | 5 | 100.0% | 100.0% |
| fastapi_app | 4 | 100.0% | 100.0% |
| go_app | 5 | 100.0% | 100.0% |
| java_app | 5 | 100.0% | 100.0% |
| minimal | 5 | 100.0% | 100.0% |
| php_app | 5 | 100.0% | 100.0% |
| python_app | 5 | 100.0% | 100.0% |
| ruby_app | 5 | 100.0% | 100.0% |
| rust_app | 5 | 100.0% | 100.0% |
| ts_express | 4 | 100.0% | 100.0% |

## c_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `add` | add | add | 100.0% | 100.0% |
| code_search | `compute` | compute | compute | 100.0% | 100.0% |
| code_search | `Point` | Point | Point | 100.0% | 100.0% |
| code_search | `Color` | Color | Color | 100.0% | 100.0% |
| code_callees | `compute` | add | add | 100.0% | 100.0% |

## cpp_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Greeter` | Greeter | Greeter, Greeter | 100.0% | 100.0% |
| code_search | `greet` | greet | greet | 100.0% | 100.0% |
| code_search | `hello` | hello | hello | 100.0% | 100.0% |
| code_search | `banner` | banner | banner | 100.0% | 100.0% |
| code_callees | `greet` | hello | hello | 100.0% | 100.0% |

## csharp_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Lion` | Lion | Lion | 100.0% | 100.0% |
| code_search | `Animal` | Animal | Animal | 100.0% | 100.0% |
| code_search | `Create` | Create | Create | 100.0% | 100.0% |
| code_impact | `Lion` | Create, Animal | Animal, Create | 100.0% | 100.0% |
| code_callers | `Animal` | (none) | (none) | 100.0% | 100.0% |

## fastapi_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `create_item` | create_item | create_item | 100.0% | 100.0% |
| code_search | `delete_item` | delete_item | delete_item | 100.0% | 100.0% |
| code_callees | `root` | (none) | (none) | 100.0% | 100.0% |
| code_context | `create_item` | (none) | (none) | 100.0% | 100.0% |

## go_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Greeter` | Greeter | Greeter | 100.0% | 100.0% |
| code_search | `NewGreeter` | NewGreeter | NewGreeter | 100.0% | 100.0% |
| code_search | `Speaker` | Speaker | Speaker | 100.0% | 100.0% |
| code_callees | `main` | NewGreeter, Speak | NewGreeter, Speak | 100.0% | 100.0% |
| code_callers | `NewGreeter` | main | main | 100.0% | 100.0% |

## java_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Lion` | Lion | Lion | 100.0% | 100.0% |
| code_search | `Animal` | Animal | Animal | 100.0% | 100.0% |
| code_search | `create` | create | create | 100.0% | 100.0% |
| code_impact | `Lion` | create, Animal | Animal, create | 100.0% | 100.0% |
| code_callers | `Animal` | (none) | (none) | 100.0% | 100.0% |

## minimal

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `helper` | helper | helper | 100.0% | 100.0% |
| code_callers | `helper` | main | main | 100.0% | 100.0% |
| code_callees | `main` | helper | helper | 100.0% | 100.0% |
| code_impact | `helper` | main | main | 100.0% | 100.0% |
| code_context | `helper` | main | main | 100.0% | 100.0% |

## php_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Greeter` | Greeter | Greeter | 100.0% | 100.0% |
| code_search | `announce` | announce | announce | 100.0% | 100.0% |
| code_search | `greet` | greet | greet | 100.0% | 100.0% |
| code_search | `MAX` | MAX | MAX | 100.0% | 100.0% |
| code_callees | `announce` | greet | greet | 100.0% | 100.0% |

## python_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `AdminUser` | AdminUser | AdminUser | 100.0% | 100.0% |
| code_search | `make_admin` | make_admin | make_admin | 100.0% | 100.0% |
| code_search | `is_admin` | is_admin | is_admin | 100.0% | 100.0% |
| code_search | `make_user` | make_user | make_user | 100.0% | 100.0% |
| code_search | `greet_user` | greet_user | greet_user | 100.0% | 100.0% |

## ruby_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Greeter` | Greeter | Greeter | 100.0% | 100.0% |
| code_search | `greet` | greet | greet | 100.0% | 100.0% |
| code_search | `hello` | hello | hello | 100.0% | 100.0% |
| code_callees | `greet` | hello | hello | 100.0% | 100.0% |
| code_callers | `hello` | greet | greet | 100.0% | 100.0% |

## rust_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Circle` | Circle | Circle | 100.0% | 100.0% |
| code_search | `Shape` | Shape | Shape | 100.0% | 100.0% |
| code_search | `make` | make | make | 100.0% | 100.0% |
| code_callees | `run` | make, area | make, area | 100.0% | 100.0% |
| code_callers | `make` | run | run | 100.0% | 100.0% |

## ts_express

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `listUsers` | listUsers | listUsers | 100.0% | 100.0% |
| code_search | `getUser` | getUser | getUser | 100.0% | 100.0% |
| code_search | `createUser` | createUser | createUser | 100.0% | 100.0% |
| code_context | `listUsers` | (none) | (none) | 100.0% | 100.0% |
