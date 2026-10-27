
from unittest.mock import patch

from docker.errors import DockerException, NotFound
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_list_containers():
    with patch("app.main.client") as mock_client:

        container = type(
            "FakeContainer",
            (),
            {
                "name": "monitor-test",
                "short_id": "abc123",
                "status": "running",
            },
        )()

        mock_client.containers.list.return_value = [container]

        response = client.get("/containers")

    assert response.status_code == 200
    assert response.json() == {
        "containers": [
            {
                "name": "monitor-test",
                "id": "abc123",
                "status": "running",
            }
        ]
    }


def test_list_containers_docker_unavailable():
    with patch("app.main.client") as mock_client:
        mock_client.containers.list.side_effect = DockerException(
            "Docker is unavailable"
        )

        response = client.get("/containers")

    assert response.status_code == 503
    assert "Docker is unavailable" in response.json()["detail"]


def test_container_stats_success():
    with (
        patch("app.main.client") as mock_client,
        patch(
            "app.main.get_resource_usage",
            return_value=(12.345, 10 * 1024 * 1024, 50.555),
        ),
    ):
        container = mock_client.containers.get.return_value
        container.name = "monitor-test"
        container.status = "running"
        container.short_id = "abc123"

        response = client.get("/containers/monitor-test/stats")

    assert response.status_code == 200
    assert response.json() == {
        "name": "monitor-test",
        "status": "running",
        "cpu_percent": 12.35,
        "memory_usage_mib": 10.0,
        "memory_percent": 50.55,
    }
    container.reload.assert_called_once()


def test_container_stats_not_running():
    with patch("app.main.client") as mock_client:
        container = mock_client.containers.get.return_value
        container.status = "exited"

        response = client.get("/containers/monitor-test/stats")

    assert response.status_code == 409
    assert response.json()["detail"] == "Container is not running"


def test_container_not_found():
    with patch("app.main.client") as mock_client:
        mock_client.containers.get.side_effect = NotFound(
            "Container does not exist"
        )

        response = client.get("/containers/nonexistent-container/stats")

    assert response.status_code == 404
    assert response.json()["detail"] == "Container not found"


def test_container_stats_docker_unavailable():
    with patch("app.main.client") as mock_client:
        mock_client.containers.get.side_effect = DockerException(
            "Docker is unavailable"
        )

        response = client.get("/containers/monitor-test/stats")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Could not retrieve container information."
    )
