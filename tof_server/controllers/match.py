"""Matches controller blueprint."""
from flask import Blueprint, jsonify, request, abort
from tof_server.validators import auth
from tof_server.validators import match as match_validator
from tof_server.models import match as match_model

controller_match = Blueprint('controller_match', __name__, template_folder='templates')


@controller_match.route('/matches/my', methods=['POST'])
def get_player_matches():
    """Method for downloading player active matches."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    return jsonify({
        'matches': match_model.get_player_matches(player_id)
    })


@controller_match.route('/matches', methods=['POST'])
def create_new_match():
    """Method for creating new match."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']
    map_code = request.json['map_code']
    side = request.json['side']

    if not match_validator.are_slots_available(player_id):
        abort(403)
    if not match_validator.is_map_available(map_code):
        abort(400)
    if not match_validator.is_side_valid(side):
        abort(400)

    new_match_code = match_model.create_new_match(player_id, side, map_code)

    return jsonify({
        'match_code': new_match_code
    })


@controller_match.route('/match/<string:match_code>.json', methods=['GET'])
def get_match_details(match_code):
    """Method for downloading match status for joining."""
    match_details = match_model.get_match_details(match_code)

    if match_details is None:
        abort(404)

    return jsonify(match_details)


@controller_match.route('/match/status/<string:match_code>.json', methods=['GET'])
def get_player_match_status(match_code):
    """Method for downloading player status."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    if not match_validator.is_in_match(player_id, match_code):
        abort(403)

    status = match_model.get_player_status_in_match(match_code, player_id)

    return jsonify(status)


@controller_match.route('/match/<string:match_code>.json', methods=['POST'])
def get_match_state(match_code):
    """Method for downloading match state for performing turn."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    if not match_validator.is_in_match(player_id, match_code):
        abort(403)

    match_state = match_model.get_match_state(match_code, player_id)

    return jsonify(match_state)


@controller_match.route('/match/join/<string:match_code>.json', methods=['POST'])
def join_match(match_code):
    """Method for joining a match."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    if not match_validator.are_slots_available(player_id):
        abort(403)
    if match_validator.is_in_match(player_id, match_code):
        abort(400)
    if not match_validator.is_match_joinable(match_code):
        abort(403)

    if not match_model.add_player_to_match(player_id, match_code):
        abort(500)

    return jsonify({
        'status': 'ok'
    })


@controller_match.route('/match/turn/<string:match_code>.json', methods=['POST'])
def update_match_state(match_code):
    """Method for updating a match state."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    if not match_validator.is_in_match(player_id, match_code):
        abort(403)

    match_state = match_model.get_match_state(match_code, player_id)

    turn_data = request.json['turn_data']

    if not match_validator.verify_turn_data(match_state['data'], turn_data):
        abort(400)

    if not match_model.update_match_state(match_code, turn_data, player_id):
        abort(500)

    match_state = match_model.get_match_state(match_code, player_id)

    return jsonify(match_state)


@controller_match.route('/match/abandon/<string:match_code>.json', methods=['POST'])
def abandon_match(match_code):
    """Method for abandoning a match."""
    validation = auth.validate(request)
    if validation['status'] != 'ok':
        abort(validation['code'])

    player_id = request.json['player_id']

    if not match_validator.is_in_match(player_id, match_code):
        abort(403)

    match_model.abandon_match(match_code, player_id)

    return jsonify({
        'status': 'ok'
    })
