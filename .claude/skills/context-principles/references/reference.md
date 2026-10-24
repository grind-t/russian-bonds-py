# Reference

A reference names an external concept in place of stating its content.
It works like a pointer: the text carries only the name, and the model
supplies the content from its own knowledge.

A name counts as a reference only if all four conditions hold:

1. External: the concept exists and is fixed independently of the user and
   the model, in a standard, a book or an established practice.
2. Shared: the model reliably knows the concept, so it belongs to the common
   ground of the user and the model.
3. Unambiguous: the name, qualified by a version or a part when needed, points
   to exactly one concept.
4. Structural: the concept defines a way to view, evaluate or build a result,
   such as a taxonomy, criteria, a procedure or a form, rather than a single
   fact.

When the task needs something slightly different from the concept, keep the
reference and state only the differences.

Examples:

- "Write commit messages per Conventional Commits 1.0.0" is a reference: it
  replaces a whole format specification.
- "Review for injection flaws per OWASP Top 10 (2021), A03" is a reference
  narrowed by version and part.
- "Follow our team style" is not external.
- "Apply the Smith method" is not shared, and it is ambiguous.
- "Python 3.12 was released in 2023" is not structural: it is a fact.
- "Write clean code" is ambiguous: it may mean the book or a vague wish.
  "Apply Clean Code (Martin, 2008), chapter 3" is a reference.
