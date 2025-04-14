from flask import Flask, jsonify, request, session
from flask_session import Session
from flask_cors import CORS
import uuid
from api.deck_api import DeckAPI

app = Flask(__name__)

# ✅ Enable CORS for frontend with credentials
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# ✅ Flask config
app.secret_key = 'super-secret-key'  # 🔐 Use an env variable in production
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # True if using HTTPS

Session(app)

# Global in-memory game state
rooms = {}

@app.route('/')
def home():
    return '🎲 Welcome to Blackjack!'

@app.route('/create-room', methods=['POST'])
def create_room():
    print("📥 [POST] /create-room")
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

    print(f"✅ Room {room_code} created | Player: {player_id}")
    return jsonify({'room_code': room_code, 'player_id': player_id})

@app.route('/join-room', methods=['POST'])
def join_room():
    print("📥 [POST] /join-room")
    data = request.json
    room_code = data.get('room_code')

    if room_code not in rooms:
        print("❌ Room not found:", room_code)
        return jsonify({'error': 'Room not found'}), 404

    player_id = str(uuid.uuid4())
    session['player_id'] = player_id
    session['room_code'] = room_code
    rooms[room_code]['players'][player_id] = {'hand': [], 'ready': False}

    print(f"✅ Player {player_id} joined room {room_code}")
    return jsonify({'room_code': room_code, 'player_id': player_id})

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

    print(f"🃏 Game started | Room: {room_code}")
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

    print(f"➕ Player {player_id} hits: {card['value']} of {card['suit']}")
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

    # Dealer logic
    dealer_total = calculate_hand_value(room['dealer_hand'])
    while dealer_total < 17:
        room['dealer_hand'].append(room['deck'].draw_cards(1)[0])
        dealer_total = calculate_hand_value(room['dealer_hand'])

    player_total = calculate_hand_value(room['players'][player_id]['hand'])

    # Game outcome
    if dealer_total > 21 or player_total > dealer_total:
        result = 'You win!'
    elif dealer_total > player_total:
        result = 'Dealer wins.'
    else:
        result = "It's a tie."

    room['game_over'] = True
    room['message'] = result

    print(f"🛑 Player {player_id} stays | Result: {result}")
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
