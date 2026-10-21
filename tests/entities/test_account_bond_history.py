import pytest
from factories import account_operation, bond
from pydantic import ValidationError

from russian_bonds._entities.account_bond_history import AccountBondHistory


def test_unclosed_position_raises():
    buy = account_operation(quantity_delta=5)
    with pytest.raises(ValidationError, match="Unclosed position for A"):
        AccountBondHistory(bond=bond(), operations=[buy])
