import pytest
import testing.postgresql

from app import app
from db import db


@pytest.fixture(autouse=True, scope="function")
def session(test_app):
    """
    Wrap a test function in an app context, create tables before, then rollback and drop tables after the function.
    """
    with test_app.app_context():
        db.session.begin()

        db.create_all()

        yield db.session

        db.session.rollback()
        db.drop_all()


@pytest.fixture(autouse=True, scope="session")
def postgresql():
    """
    Set up a postgres instance for testing
    """
    with testing.postgresql.Postgresql() as postgresql:
        yield postgresql


@pytest.fixture(autouse=True, scope="session")
def test_app(postgresql):
    """
    Create a flask application for testing
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = postgresql.url()

    return app
