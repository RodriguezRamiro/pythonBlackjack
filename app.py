app.py

from flask import Flask, jsonify, request, session
from flask_session import Session
from flask_cors import CORS
import uuid
from api.deck_api import DeckAPI

app = Flask(__name__)
CORS(app)
app.secret_key = 'super-secret-key'  # Use env var in production
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

rooms = {}  # In-memory room state

@app.route('/')
def home():
    return 'Welcome to Blackjack!'

@app.route('/create-room', methods=['POST'])
def create_room():
    room_code = str(uuid.uuid4())[:6].upper()
    player_id = str(uuid.uuid4())

    session['player_id'] = player_id
    session['room_code'] = room_code

    rooms[room_code] = {
        'deck': DeckAPI(),
        'players': {
            player_id: {'hand': [], 'ready': False}
        },
        'dealer_hand': [],
        'game_over': False,
        'message': ''
    }

    return jsonify({'room_code': room_code, 'player_id': player_id})

@app.route('/join-room', methods=['POST'])
def join_room():
    data = request.json
    room_code = data.get('room_code')

    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404

    player_id = str(uuid.uuid4())
    session['player_id'] = player_id
    session['room_code'] = room_code
    rooms[room_code]['players'][player_id] = {'hand': [], 'ready': False}

    return jsonify({'message': f'Joined room {room_code}', 'player_id': player_id})

@app.route('/start-game', methods=['POST'])
def start_game():
    room_code = session.get('room_code')
    player_id = session.get('player_id')

    if not room_code or not player_id or room_code not in rooms:
        return jsonify({'error': 'Invalid session'}), 400

    room = rooms[room_code]
    deck = room['deck']
    deck.new_deck()

    room['dealer_hand'] = deck.draw_cards(2)

    for pid in room['players']:
        room['players'][pid]['hand'] = deck.draw_cards(2)

    return jsonify({
        'message': 'Game started',
        'dealer_card': room['dealer_hand'][0]
    })

@app.route('/hit', methods=['POST'])
def hit():
    room_code = session.get('room_code')
    player_id = session.get('player_id')

    room = rooms.get(room_code)
    if not room or player_id not in room['players']:
        return jsonify({'error': 'Invalid session or room'}), 400

    card = room['deck'].draw_cards(1)[0]
    room['players'][player_id]['hand'].append(card)
    total = calculate_hand_value(room['players'][player_id]['hand'])

    if total > 21:
        room['game_over'] = True
        room['message'] = 'Bust! You lose'

    return jsonify({
        'card': card,
        'hand': room['players'][player_id]['hand'],
        'total': total
    })

@app.route('/stay', methods=['POST'])
def stay():
    room_code = session.get('room_code')
    player_id = session.get('player_id')

    room = rooms.get(room_code)
    if not room or player_id not in room['players']:
        return jsonify({'error': 'Invalid session or room'}), 400

    # Dealer's turn
    dealer_total = calculate_hand_value(room['dealer_hand'])
    while dealer_total < 17:
        room['dealer_hand'].append(room['deck'].draw_cards(1)[0])
        dealer_total = calculate_hand_value(room['dealer_hand'])

    player_total = calculate_hand_value(room['players'][player_id]['hand'])

    if dealer_total > 21 or player_total > dealer_total:
        result = 'You win!'
    elif dealer_total > player_total:
        result = 'Dealer wins.'
    else:
        result = "It's a tie."

    room['game_over'] = True
    room['message'] = result

    return jsonify({
        'dealer_hand': room['dealer_hand'],
        'dealer_total': dealer_total,
        'player_total': player_total,
        'result': result
    })

@app.route('/hand', methods=['GET'])
def show_hand():
    room_code = session.get('room_code')
    player_id = session.get('player_id')
    room = rooms.get(room_code)

    if not room or player_id not in room['players']:
        return jsonify({'error': 'Invalid session or room'}), 400

    hand = room['players'][player_id]['hand']
    return jsonify({
        'hand': hand,
        'total': calculate_hand_value(hand)
    })

def calculate_hand_value(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card['value']
        if rank in ['JACK', 'QUEEN', 'KING']:
            value += 10
        elif rank == 'ACE':
            value += 11
            aces += 1
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

if __name__ == '__main__':
    app.run(debug=True)
