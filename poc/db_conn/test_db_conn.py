from db_conn import ping


def test_ping():
    assert ping() is True


