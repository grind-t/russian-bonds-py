from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.t_invest_operation import TInvestOperation
from russian_bonds._stateless_computations.quantity_delta import quantity_delta
from russian_bonds._stateless_computations.to_rub_money import to_rub_money


def to_account_operation(operation: TInvestOperation) -> AccountOperation:
    return AccountOperation(
        id=operation.id,
        parent_operation_id=operation.parent_operation_id,
        ticker=operation.ticker,
        name=operation.name,
        description=operation.description,
        type=operation.type,
        payment=to_rub_money(operation.payment),
        quantity_delta=quantity_delta(operation.type, operation.quantity_done),
        date=operation.date,
        virtual=False,
    )
