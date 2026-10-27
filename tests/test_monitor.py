
from unittest.mock import Mock, patch

import pytest

import app.monitor as monitor
import app.alerts as alerts

@pytest.fixture(autouse=True)
def reset_alert_state():
    """Reset alert tracking before every test."""
    alerts.alerted_containers.clear()
    alerts.high_cpu_alerted.clear()
    alerts.high_memory_alerted.clear()


def create_container(status="running"):
    """Create a fake Docker container for testing."""
    container = Mock()
    container.name = "monitor-test"
    container.id = "test-container-123"
    container.status = status
    container.reload.return_value = None

    return container



def test_cpu_threshold_alert():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            return_value=(85.0, 26 * 1024 * 1024, 10.0),
        ),
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        monitor.check_containers()

        mock_warning.assert_any_call(
            "ALERT: monitor-test CPU usage is high: 85.00%"
        )

    assert container.id in alerts.high_cpu_alerted


def test_memory_threshold_alert():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            return_value=(10.0, 26 * 1024 * 1024, 90.0),
        ),
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        monitor.check_containers()

        mock_warning.assert_any_call(
            "ALERT: monitor-test memory usage is high: 90.00%"
        )

    assert container.id in alerts.high_memory_alerted


def test_cpu_and_memory_alerts_together():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            return_value=(95.0, 100 * 1024 * 1024, 90.0),
        ),
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        monitor.check_containers()

        mock_warning.assert_any_call(
            "ALERT: monitor-test CPU usage is high: 95.00%"
        )
        mock_warning.assert_any_call(
            "ALERT: monitor-test memory usage is high: 90.00%"
        )


def test_duplicate_high_usage_alerts_are_prevented():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            return_value=(90.0, 100 * 1024 * 1024, 90.0),
        ),
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        # First monitoring cycle
        monitor.check_containers()

        # Second cycle: usage is still high
        monitor.check_containers()

        # Only one CPU alert and one memory alert
        assert mock_warning.call_count == 2


def test_cpu_recovery_alert():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            side_effect=[
                (90.0, 100 * 1024 * 1024, 20.0),
                (40.0, 100 * 1024 * 1024, 20.0),
            ],
        ),
        patch("app.monitor.logging.info") as mock_info,
    ):
        mock_client.containers.list.return_value = [container]

        # First cycle: CPU is too high
        monitor.check_containers()

        # Second cycle: CPU has returned to normal
        monitor.check_containers()

        mock_info.assert_any_call(
            "RECOVERED: monitor-test CPU usage is back to normal: 40.00%"
        )

    assert container.id not in alerts.high_cpu_alerted


def test_memory_recovery_alert():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            side_effect=[
                (10.0, 100 * 1024 * 1024, 90.0),
                (10.0, 50 * 1024 * 1024, 50.0),
            ],
        ),
        patch("app.monitor.logging.info") as mock_info,
    ):
        mock_client.containers.list.return_value = [container]

        # First cycle: memory usage is too high
        monitor.check_containers()

        # Second cycle: memory usage has returned to normal
        monitor.check_containers()

        mock_info.assert_any_call(
            "RECOVERED: monitor-test memory usage is back to normal: 50.00%"
        )

    assert container.id not in alerts.high_memory_alerted


def test_usage_at_threshold_does_not_trigger_alert():
    container = create_container()

    with (
        patch("app.monitor.client") as mock_client,
        patch(
            "app.monitor.get_resource_usage",
            return_value=(80.0, 100 * 1024 * 1024, 80.0),
        ),
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        monitor.check_containers()

        mock_warning.assert_not_called()


def test_stopped_container_alert_is_not_repeated():
    container = create_container(status="exited")

    with (
        patch("app.monitor.client") as mock_client,
        patch("app.monitor.logging.warning") as mock_warning,
    ):
        mock_client.containers.list.return_value = [container]

        # First cycle: stopped alert
        monitor.check_containers()

        # Second cycle: same container remains stopped
        monitor.check_containers()

        mock_warning.assert_called_once_with(
            "ALERT: monitor-test has stopped!"
        )
