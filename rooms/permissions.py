from rest_framework.exceptions import PermissionDenied

GLOBAL_ROOM_ID = '00000000-0000-0000-0000-000000000000'


def user_can_access_room(room, user) -> bool:
    """Global hall is open to all authenticated users; private rooms are creator + partner only."""
    if str(room.id) == GLOBAL_ROOM_ID:
        return True
    if room.created_by_id == user.id:
        return True
    if room.joined_by_id == user.id:
        return True
    return False


def assert_room_access(room, user) -> None:
    if not user_can_access_room(room, user):
        raise PermissionDenied('You do not have access to this room.')
