import pytest

import db.pet_proofs_table as ppt
from db.pet_proofs_table import pet_proofs_table, add_pet_proof, count_pet_proofs_for_team


@pytest.fixture(autouse=True)
def clear_pet_proofs():
    pet_proofs_table.truncate()
    yield
    pet_proofs_table.truncate()


def test_count_pet_proofs_for_team():
    assert count_pet_proofs_for_team("alpha") == 0
    add_pet_proof("alpha", "http://a", 1, "x")
    assert count_pet_proofs_for_team("alpha") == 1
    add_pet_proof("alpha", "http://b", 2, "y")
    assert count_pet_proofs_for_team("alpha") == 2
    add_pet_proof("beta", "http://c", 3, "z")
    assert count_pet_proofs_for_team("alpha") == 2
    assert count_pet_proofs_for_team("beta") == 1
