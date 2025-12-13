import pytest
from django.urls import reverse

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


@pytest.fixture
def notifications_url():
    return reverse("notifications-list")


@pytest.fixture
def check_all_url():
    return reverse("notifications-check-all")


@pytest.mark.django_db
def test_list_notifications_default_is_checked_false(auth_client, user, notifications_url):
    # Arrange
    Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )
    Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=True,
    )

    # Act
    response = auth_client.get(notifications_url)

    # Assert
    assert response.status_code == 200
    data = response.json()
    results = data.get("results", data)

    assert len(results) == 1
    assert results[0]["is_checked"] is False


@pytest.mark.django_db
def test_list_notifications_is_checked_true(auth_client, user, notifications_url):
    # Arrange
    Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )
    checked = Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=True,
    )

    # Act
    response = auth_client.get(notifications_url, {"is_checked": "true"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    results = data.get("results", data)

    assert len(results) == 1
    assert results[0]["id"] == str(checked.id)
    assert results[0]["is_checked"] is True


@pytest.mark.django_db
def test_list_notifications_filter_by_type(auth_client, user, notifications_url):
    # Arrange
    expected = Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )
    Notification.objects.create(
        for_user=user,
        type=Notification.Type.ITEM_CREATE,
        is_checked=False,
    )

    # Act
    response = auth_client.get(notifications_url, {"types": "follow"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    results = data.get("results", data)

    assert len(results) == 1
    assert results[0]["id"] == str(expected.id)
    assert results[0]["type"] == Notification.Type.FOLLOW


@pytest.mark.django_db
def test_check_all_marks_only_current_user(auth_client, user_factory, user, check_all_url):
    # Arrange
    other = user_factory()

    Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )
    Notification.objects.create(
        for_user=user,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )
    Notification.objects.create(
        for_user=other,
        type=Notification.Type.FOLLOW,
        is_checked=False,
    )

    # Act
    response = auth_client.post(check_all_url)

    # Assert
    assert response.status_code == 200
    assert response.json()["updated"] == 2

    assert Notification.objects.filter(for_user=user, is_checked=False).count() == 0
    assert Notification.objects.filter(for_user=other, is_checked=False).count() == 1


@pytest.mark.django_db
def test_service_create_follow_notification(user_factory):
    # Arrange
    follower = user_factory()
    target = user_factory()
    service = NotificationService()

    # Act
    service.create_follow(
        target_user=target,
        follower_user=follower,
    )

    # Assert
    notification = Notification.objects.get(for_user=target)
    assert notification.type == Notification.Type.FOLLOW
    assert notification.info["user_id"] == str(follower.id)
    assert notification.is_checked is False
