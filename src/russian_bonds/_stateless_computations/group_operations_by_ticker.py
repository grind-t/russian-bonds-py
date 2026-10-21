from collections import defaultdict

from russian_bonds._entities.account_operation import AccountOperation


def group_operations_by_ticker(
    operations: list[AccountOperation],
) -> dict[str, list[AccountOperation]]:
    by_ticker: defaultdict[str, list[AccountOperation]] = defaultdict(list)
    for op in operations:
        by_ticker[op.ticker].append(op)
    return by_ticker
