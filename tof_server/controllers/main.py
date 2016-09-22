"""Main controller blueprint."""
from flask import Blueprint, jsonify, request
from tof_server.validators import versioning

controller_main = Blueprint('controller_main', __name__, template_folder='templates')


@controller_main.route('/')
def index():
    """Server information."""
    return jsonify({
        'server-version': versioning.SERVER_VERSION,
        'client-versions': versioning.CLIENT_VERSIONS,
        'you': request.user_agent.string
    })