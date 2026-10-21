import pytest
from factories import account_operation
from pydantic import ValidationError
from t_tech.invest import OperationType


def test_fee_without_parent_raises():
    with pytest.raises(ValidationError, match="No parent operation"):
        account_operation(
            type=OperationType.OPERATION_TYPE_BROKER_FEE, parent_operation_id=""
        )
