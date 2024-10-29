from flask import Blueprint, request
from model import ModelForTest
from repository import update_or_create, update_or_create_naive


controller = Blueprint("controller", __name__)


@controller.route("/health", methods=["GET"])
def health():
    return "", 200


@controller.route("/upsert_naive", methods=["POST"])
def upsert_testing_model_naive():
    update_or_create_naive(
        request.json,
        [ModelForTest.key.name],
        ModelForTest,
    )
    return "", 200


@controller.route("/upsert", methods=["POST"])
def upsert_testing_model():
    update_or_create(
        request.json,
        [ModelForTest.key.name],
        ModelForTest,
    )
    return "", 200
