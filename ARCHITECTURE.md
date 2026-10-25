# Architecture principles

Package grid — rows by role, columns by state, over `_entities`
  - Rows: computations (deterministic, no IO) ← workflows (wire computations and effects through ports) ← effects (IO)
  - Columns: stateless (calls are independent) | stateful (state kept in memory between calls)
  - Packages in one row may import each other; across rows only downward
  - Ports (`Callable` or `Protocol`) live in workflows next to their use; effects import only those ports from workflows
  - `lib/__init__.py` wires effects into workflows and does no IO on import
