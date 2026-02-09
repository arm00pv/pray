from flask import Blueprint, render_template

game_bp = Blueprint('game', __name__, url_prefix='/games')

@game_bp.route('/memory')
def memory_game():
    return render_template('memory_game.html')
