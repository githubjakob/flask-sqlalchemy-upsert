import concurrent
import waitress
from threading import Thread
from queue import Queue
from typing import List
from time import sleep
import pytest
import requests
from app import app
from model import ModelForTest
from repository import db

SERVER_URL = "http://127.0.0.1:5000"


def run_flask_app(q):
    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        q.put("shutdown")
        return "Server shutting down...", 200

    s = waitress.create_server(app, host="localhost", port=5000)
    t = Thread(target=s.run)
    t.start()

    try:
        q.get()  # Wait for shutdown signal
    finally:
        s.close()
        t.join()


@pytest.fixture(autouse=True, scope="session")
def threaded_app():
    q = Queue()
    p = Thread(target=run_flask_app, args=(q,))
    p.start()

    # Give the server time to start
    sleep(1)

    yield app

    # Send shutdown request
    try:
        response = requests.post("http://localhost:5000/shutdown")
        print("Shutdown response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error shutting down the server: {e}")

    # Wait for the Flask server thread to complete
    p.join()


class RequestOperation:
    def __init__(self, endpoint, payload, method):
        self.endpoint = endpoint
        self.payload = payload
        self.method = method


def helper_make_concurrent_requests(request_operations: List[RequestOperation]):
    def make_request(request_operation: RequestOperation):
        url = f"{SERVER_URL}{request_operation.endpoint}"
        json = request_operation.payload
        if request_operation.method == "GET":
            return requests.get(url=url, json=json)
        elif request_operation.method == "POST":
            return requests.post(url=url, json=json)
        elif request_operation.method == "PUT":
            return requests.put(url=url, json=json)
        elif request_operation.method == "PATCH":
            return requests.patch(url=url, json=json)
        elif request_operation.method == "DELETE":
            return requests.delete(url=url, json=json)
        else:
            raise Exception("Invalid method")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for ro in request_operations:
            futures.append(executor.submit(make_request, request_operation=ro))

        responses = []
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            responses += [res]

    return responses


def test_threaded_push_device_update_or_create_returns_200(threaded_app):
    payloads = []

    for i in range(10):
        payload = {
            "key": str(i),
            "data": str(i),
        }
        payloads += [payload, payload, payload]

    request_operations = [
        RequestOperation(endpoint="/upsert", payload=payload, method="POST")
        for payload in payloads
    ]

    responses = helper_make_concurrent_requests(request_operations=request_operations)

    failed_responses = [r for r in responses if r.status_code == 500]
    assert len(failed_responses) == 0

    successful_responses = [r for r in responses if r.status_code == 200]
    assert len(successful_responses) == len(payloads)

    created_models = db.session.query(ModelForTest).all()
    assert len(created_models) == int(len(payloads) / 3)
