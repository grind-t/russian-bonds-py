---
name: refactoring-queue
description: Queues violations of unstated Computer Science principles for refactoring.
disable-model-invocation: true
---

# Refactoring queue

Find explicit violations of Computer Science principles that the project does not state yet, and keep `queue.json` next to this file current and sorted by severity. Edit no file but the queue.

## Format

```json
[
  {
    "principle": "<id>: <formulation>",
    "severity": "critical | major | minor | trivial",
    "category": "...",
    "description": "...",
    "hierarchy": [["Computer Science", "...", "..."]],
    "violations": [
      {
        "description": "...",
        "locations": ["path:line"]
      }
    ]
  }
]
```

Principle fields:

- `principle`: the list entry as it will appear under the category heading. The ID is the next free one of the category's prefix across the rules, the skills and the queue (a new letter for a new category). The formulation is like the existing ones: a short imperative English phrase, preferably the established term.
- `severity`: how much harm the violations do to the project.
- `category`: the heading of the existing rules file or skill whose topic fits, such as `Naming principles` or `Design principles`, or a new one: a rules file for a property of the code, a skill for a principle of how to work.
- `description`: a free description of the principle: its established term, its most common formulation and related terms, such as the antipattern it fights.
- `hierarchy`: paths from Computer Science down to the principle, each an array of nodes. Name the canonical source (author, work, year) at the node it comes from. Add a second path when the principle has both a theoretical and an engineering side.

Violation fields:

- `description`: what is wrong and what it leads to.
- `locations`: every place, as `path:line` relative to the repository root.
