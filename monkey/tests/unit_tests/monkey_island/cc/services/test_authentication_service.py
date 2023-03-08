from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from monkey_island.cc.event_queue import IIslandEventQueue, IslandEventTopic
from monkey_island.cc.models import IslandMode, User
from monkey_island.cc.server_utils.encryption import ILockableEncryptor
from monkey_island.cc.services import AuthenticationService

USERNAME = "user1"
PASSWORD = "test"
PASSWORD_HASH = "$2b$12$yQzymz55fRvm8rApg7erluIvIAKSFSDrNIOIrOlxC4sXsDSkeu9z2"


# Some tests have these fixtures as arguments even though `autouse=True`, because
# to access the object that a fixture returns, it needs to be specified as an argument.
# See https://stackoverflow.com/a/37046403.


@pytest.fixture
def mock_repository_encryptor(autouse=True) -> ILockableEncryptor:
    return MagicMock(spec=ILockableEncryptor)


@pytest.fixture
def mock_island_event_queue(autouse=True) -> IIslandEventQueue:
    return MagicMock(spec=IIslandEventQueue)


@pytest.fixture
def authentication_service(
    mock_flask_app,
    tmp_path: Path,
    mock_repository_encryptor: ILockableEncryptor,
    mock_island_event_queue: IIslandEventQueue,
) -> AuthenticationService:
    return AuthenticationService(tmp_path, mock_repository_encryptor, mock_island_event_queue)


def test_needs_registration__true(authentication_service: AuthenticationService):
    assert authentication_service.needs_registration()


def test_needs_registration__false(
    monkeypatch,
    authentication_service: AuthenticationService,
):
    User(username=USERNAME, password=PASSWORD).save()
    assert not authentication_service.needs_registration()


def test_handle_successful_registration(
    mock_repository_encryptor: ILockableEncryptor,
    mock_island_event_queue: IIslandEventQueue,
    authentication_service: AuthenticationService,
):
    authentication_service.handle_successful_registration(USERNAME, PASSWORD)

    assert mock_repository_encryptor.unlock.call_args[0][0] != USERNAME
    assert mock_repository_encryptor.unlock.call_args[0][0] != PASSWORD
    mock_repository_encryptor.reset_key.assert_called_once()
    mock_repository_encryptor.unlock.assert_called_once()

    assert mock_island_event_queue.publish.call_count == 3
    mock_island_event_queue.publish.assert_has_calls(
        [
            call(IslandEventTopic.CLEAR_SIMULATION_DATA),
            call(IslandEventTopic.RESET_AGENT_CONFIGURATION),
            call(topic=IslandEventTopic.SET_ISLAND_MODE, mode=IslandMode.UNSET),
        ]
    )


def test_handle_sucessful_logout(
    mock_repository_encryptor: ILockableEncryptor,
    authentication_service: AuthenticationService,
):
    authentication_service.handle_successful_logout()

    assert mock_repository_encryptor.lock.call_count == 1
