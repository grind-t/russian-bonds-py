# Debt schema

Each debt item is described by these fields:

- `defect_description`: a short statement of the problem.
- `defect_location`: where the defect lives in the project.
- `defect_type`: a [reference](../../context-principles/references/reference.md)
  to the family of problems this defect belongs to.
- `defect_characteristic`: the ISO/IEC 25010:2023 quality characteristic the
  defect impairs.
- `defect_subcharacteristic`: the ISO/IEC 25010:2023 quality subcharacteristic
  the defect impairs, within `defect_characteristic`.

Example:

```yaml
defect_description: Order totals are computed in three places with different rounding
defect_location: src/orders/totals.py, src/billing/invoice.py, src/reports/sales.py
defect_type: Duplicated Code (Fowler, Refactoring, 2nd ed.)
defect_characteristic: Maintainability
defect_subcharacteristic: Modifiability
```
