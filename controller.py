from flask import Blueprint, request
from model import ModelForTest
from repository import test_repository

controller = Blueprint("controller", __name__)


@controller.route("/health", methods=["GET"])
def health():
    return "", 200


@controller.route("/upsert_naive", methods=["POST"])
def upsert_testing_model_naive():
    test_repository.update_or_create_naive(
        request.json,
        [ModelForTest.key.name],
    )
    return "", 200


@controller.route("/upsert", methods=["POST"])
def upsert_testing_model():
    test_repository.update_or_create(
        request.json,
        [ModelForTest.key.name],
    )
    return "", 200
