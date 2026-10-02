from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from t_tech.invest import OperationType

from russian_bonds.operations.normalized_operations import NormalizedOperation


def test_fee_without_parent_raises():
    with pytest.raises(ValidationError, match="No parent operation"):
        NormalizedOperation(
            id="fee",
            parent_operation_id="",
            ticker="A",
            name="Комиссия",
            description="Удержание комиссии",
            type=OperationType.OPERATION_TYPE_BROKER_FEE,
            payment=-1.0,
            quantity_done=0,
            date=datetime(2026, 1, 1, tzinfo=UTC),
            virtual=False,
        )
