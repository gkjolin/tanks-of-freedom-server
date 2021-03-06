"""Module for operations on matches."""
import json
from tof_server.repository import map as map_repository
from tof_server.repository import match as match_repository
from tof_server.utils import randcoder

MAP_CODE_LENGTH = 5


def get_player_matches(player_id):
    """Method for getting list of player matches with details."""
    visible_matches = match_repository.get_player_visible_matches(player_id)

    visible_matches_data = []
    for player_match in visible_matches:
        match_details = match_repository.get_match_info(player_match[0])
        map_code = map_repository.find_code_by_id(match_details[2])
        visible_matches_data.append({
            'join_code': match_details[0],
            'match_status': match_details[1],
            'side': player_match[1],
            'player_status': player_match[2],
            'map_code': map_code
        })

    return visible_matches_data


def create_new_match(host_id, host_side, map_code):
    """Create new match."""
    map_id = map_repository.find_id_by_code(map_code)

    new_match_code = randcoder.get_random_code(MAP_CODE_LENGTH)
    while True:
        match_details = match_repository.get_match_info_by_code(new_match_code)
        if not match_details:
            break

        new_match_code = randcoder.get_random_code(MAP_CODE_LENGTH)

    new_match_id = match_repository.create_new_match(map_id, new_match_code)
    match_repository.join_player_to_match(new_match_id, host_id, host_side)
    match_repository.create_empty_match_state(new_match_id)

    return new_match_code


def get_match_details(match_code):
    """Method for getting details about the match."""
    match_details = match_repository.get_match_info_by_code(match_code)
    if not match_details:
        return None

    map_code = map_repository.find_code_by_id(match_details[2])
    available_side = _get_available_side_for_match(match_details[0])

    return {
        'join_code': match_code,
        'match_status': match_details[1],
        'map_code': map_code,
        'available_side': available_side
    }


def get_player_status_in_match(match_code, player_id):
    """Method for getting status of a player in match."""
    match_details = match_repository.get_match_info_by_code(match_code)
    if not match_details:
        return None

    match_id = match_details[0]
    map_code = map_repository.find_code_by_id(match_details[2])
    player_data = match_repository.get_player_in_match(player_id, match_id)

    return {
        'join_code': match_code,
        'match_status': match_details[1],
        'map_code': map_code,
        'player_side': player_data[0],
        'player_status': player_data[1]
    }


def _get_available_side_for_match(match_id):
    """Method for getting available side in a match."""
    players = match_repository.get_players_for_match(match_id)
    if len(players) != 1:
        return None

    if players[0][1] == match_repository.MATCH_SIDE_BLUE:
        return match_repository.MATCH_SIDE_RED

    return match_repository.MATCH_SIDE_BLUE


def get_match_state(match_code, player_id):
    """Method for getting state of a match."""
    match_details = match_repository.get_match_info_by_code(match_code)
    if not match_details:
        return None

    match_id = match_details[0]
    match_status = match_details[1]
    map_id = match_details[2]

    map_code = map_repository.find_code_by_id(map_id)
    match_state_data = match_repository.get_match_state(match_id)
    match_state_data = json.loads(match_state_data)
    player_data = match_repository.get_player_in_match(player_id, match_id)

    return {
        'join_code': match_code,
        'match_status': match_status,
        'map_code': map_code,
        'data': match_state_data,
        'player_status': player_data[1],
        'player_side': player_data[0]
    }


def add_player_to_match(player_id, match_code):
    """Method for joining new player to a match."""
    match_details = match_repository.get_match_info_by_code(match_code)
    if not match_details:
        return False

    match_id = match_details[0]
    available_side = _get_available_side_for_match(match_id)

    match_repository.join_player_to_match(match_id, player_id, available_side)

    match_repository.update_match_status(match_id, match_repository.MATCH_STATE_IN_PROGRESS)

    return True


def update_match_state(match_code, turn_data, player_id):
    """Method for updating match turn data."""
    match_details = match_repository.get_match_info_by_code(match_code)
    if not match_details:
        return False

    match_id = match_details[0]
    turn_data = json.dumps(turn_data)
    match_repository.update_match_state(match_id, turn_data)

    _update_players_state(
        match_id,
        player_id,
        match_repository.MATCH_PLAYER_STATE_INACTIVE,
        match_repository.MATCH_PLAYER_STATE_ACTIVE)

    if 'win' in turn_data:
        _update_players_state(
            match_id,
            player_id,
            match_repository.MATCH_PLAYER_STATE_WIN,
            match_repository.MATCH_PLAYER_STATE_LOSS)
        match_repository.update_match_status(match_id, match_repository.MATCH_STATE_ENDED)

    return True


def _update_players_state(match_id, player_id, that_player_state, other_player_state):
    """Method for switching active player in match."""
    match_repository.update_other_players_status(match_id, player_id, other_player_state)
    match_repository.update_player_status(match_id, player_id, that_player_state)


def abandon_match(match_code, player_id):
    """Method for abandoning a match."""
    match_details = match_repository.get_match_info_by_code(match_code)

    match_id = match_details[0]
    match_status = match_details[1]

    if match_status == match_repository.MATCH_STATE_IN_PROGRESS:
        match_repository.update_match_status(match_id, match_repository.MATCH_STATE_FORFEIT)
        match_repository.update_other_players_status(match_id, player_id, match_repository.MATCH_PLAYER_STATE_WIN)
    elif match_status == match_repository.MATCH_STATE_NEW:
        match_repository.update_match_status(match_id, match_repository.MATCH_STATE_ENDED)

    match_repository.update_player_status(match_id, player_id, match_repository.MATCH_PLAYER_STATE_DISMISSED)
