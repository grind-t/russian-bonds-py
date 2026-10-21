---
name: refactoring-queue
description: Finds explicit violations of Computer Science principles in the code, drafts the principles that .claude/rules and .claude/skills do not cover yet, and queues the violations for refactoring in the skill's queue.md. Use when the user asks to audit the code for principle violations.
---

# Refactoring queue

## Steps

1. Read every file in `.claude/rules` and `.claude/skills` but this skill's `queue.md`. Collect the principles, their IDs and the `paths` each rules file applies to.
2. Read the code in scope: the paths the user names, otherwise all tracked source, tests and root scripts.
3. Keep only explicit violations: a concrete place where the code breaks a named, established principle with a real consequence. Drop style preferences and hunches. A violation of an existing principle counts only if it causes a real bug.
4. Verify each finding before reporting it. Check claims about external APIs and libraries against the installed source, recorded fixtures or a read-only call. Drop a finding that rests on an unverified assumption.
5. Rank the findings: a bug on current data, then a latent bug, then a design flaw.
6. Update `queue.md` next to this file, creating it with a `# Refactoring queue` heading and the two sections below if missing:
   - recheck the locations of each queued problem and drop the problem once none of them violates its principle;
   - drop each proposed principle that the rules or skills now contain;
   - add each new problem after the queued ones, most severe first, or add its locations to a queued problem it repeats;
   - add each new principle the new problems break, unless it exists or is already proposed.
7. Reply with one line per added or dropped problem and principle, and a link to the queue.

## Queue

Write in the user's language, except the formulations.

### Principles

Only the proposed ones, as reference for the problems. For each:

#### `<ID>: <phrase>`

The formulation as the heading: the next free ID of the chosen prefix across the rules, the skills and the queue (a new letter for a new file). Keep it like the existing principles: a short imperative English phrase, preferably the established term.

- **Term**: the established term of the principle.
- **Hierarchy**: a code block tree from Computer Science down to the principle. Name the canonical source (author, work, year) at the node it comes from. Add a second branch when the principle has both a theoretical and an engineering side.
- **Principle**: its most common formulation and related terms, such as the antipattern it fights.
- **Placement**:
  - a rules file for a property of the code; the existing one whose topic and `paths` fit, or a new one with its own `paths`;
  - a skill for a principle of how to work, like the planning principles.
- **Problems**: the IDs of the problems that break it.

### Problems

The queue itself, worked from the top. For each:

#### `Q-<N>: <short title>`

N is one more than the highest problem number in the queue.

- **Principle**: the ID of the broken principle, proposed or existing.
- **Problem**: what is wrong and what it leads to.
- **Location**: `[file:line](path:line)` links to every place.

A problem is done when its code is fixed and its principle exists at the proposed place, so the violation does not come back. Edit no file but the queue; offer to work through the problems from the top.
