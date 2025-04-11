from flask import Flask, jsonify, request, session
from flask_session import Session
import uuid
import random
import string
from api.deck_api import DeckAPI

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Replace with env var in production
app.config['SESSION_TYPE'] = 'filesystem'  # optional switch to redis

Session(app)

# In-memory room state
rooms = {}

deck_api = DeckAPI()

@app.route('/create-room', methods=['POST'])
def create_room():
    room_code= str(uuid.uuid4())[:6].uppder()
    session['player_id'] = str(uuid.uuid4())

    rooms[room_code] = {
        'deck': DeckAPI(),
        'player': {session['player_id']: {'hand': [], 'ready': False}},
        'dealer_hand': [],
        'game_over': False,
        'message:': ''
    }

    session['room_code'] = room_code

    return jsonify({'room_code': room_code, 'player_id': session['player_id']})

@app.route('/join-room', methods=['POST'])
def join_room():
    data = request.json
    room_code = data.get('room_code')
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404

    session['player_id'] = str(uuid.uuid4())
    session['room_code'] = room_code
    rooms [room_code]['player'][session['player_id']] = {'hand': [], 'ready': False}

    return jsonify({'message': f'Joined room {room_code}', 'player_id': session['player_id']})

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

            return jsonify({'message': 'Game Started', 'dealer_card': room['dealer_hand'][0]})

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

    return jsonify({'card': card, 'hand': room['players'][player_id]['hand'], 'total': total})

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
    if dealer_toal > 21 or player_total > dealer_total:
        result = 'You win!'
    elif dealer_total > player_total:
        result = 'Dealer wins.'

    else:
        result = "Its a tie"

    room['game_over'] = True
    room['message'] = result

    return jsonify({
        'dealer_hand': room['dealer_hand'],
        'dealer_total': dealer_total,
        'player_total': dealer_total,
        'result': result
    })





def get_player_state():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
        session['game_state'] = {
            'player_hand': [],
            'dealer_hand': [],
            'deck_id': None,
            'game_over': False,
            'message': ''
        }
    return session['game_state']


def calculate_hand_value(hand):
    """Calculate the total value of a blackjack hand."""
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


@app.route('/')
def home():
    """Welcome message for root route."""
    return 'Welcome to Blackjack!'


@app.route('/start', methods=['GET'])
def start_game():
    """
    Starts a new game by resetting hands and drawing initial cards.
    Returns the player's hand and one visible dealer card.
    """
    game_state = get_player_state()
    deck_api.new_deck()
    session['deck_id'] = deck_api.deck_id

    game_state['player_hand'] = deck_api.draw_cards(2)
    game_state['dealer_hand'] = deck_api.draw_cards(2)
    game_state['game_over'] = False
    game_state['message'] = 'Game started. Your move!'
    session['game_state'] = game_state

    return jsonify({
        'player_hand': game_state['player_hand'],
        'dealer_hand': [game_state['dealer_hand'][0], {'value': 'Hidden', 'suit': 'Hidden'}],
        'message': game_state['message'],
        'player_id': session['player_id']
    })


@app.route('/hit', methods=['GET'])
def hit():
    """
    Player requests a new card.
    If the total exceeds 21, the player busts.
    """
    game_state = get_player_state()
    if game_state['game_over']:
        return jsonify({'message': 'Game is over. Please start a new game.'}), 400

    card = deck_api.draw_cards(1)[0]
    game_state['player_hand'].append(card)
    player_total = calculate_hand_value(game_state['player_hand'])

    if player_total > 21:
        game_state['game_over'] = True
        game_state['message'] = 'Bust! You lose.'

    session['game_state'] = game_state
    return jsonify({
        'player_hand': game_state['player_hand'],
        'player_total': player_total,
        'message': game_state['message']
    })


@app.route('/stay', methods=['GET'])
def stay():
    """
    Player ends their turn. Dealer plays, then results are evaluated.
    """
    game_state = get_player_state()
    if game_state['game_over']:
        return jsonify({'message': 'Game is over. Please start a new game.'}), 400

    dealer_total = calculate_hand_value(game_state['dealer_hand'])
    player_total = calculate_hand_value(game_state['player_hand'])

    while dealer_total < 17:
        game_state['dealer_hand'].append(deck_api.draw_cards(1)[0])
        dealer_total = calculate_hand_value(game_state['dealer_hand'])

    if dealer_total > 21 or player_total > dealer_total:
        result = 'You win!'
    elif dealer_total > player_total:
        result = 'Dealer wins.'
    else:
        result = "It's a tie."

    game_state['game_over'] = True
    game_state['message'] = result
    session['game_state'] = game_state

    return jsonify({
        'player_hand': game_state['player_hand'],
        'dealer_hand': game_state['dealer_hand'],
        'player_total': player_total,
        'dealer_total': dealer_total,
        'message': result
    })


@app.route('/draw', methods=['GET'])
def draw_cards():
    """
    Draw arbitrary number of cards from the deck.

    Query Parameters:
    count (int): Number of cards to draw. Default is 1.

    Returns:
        JSON object with drawn cards.
    """
    count = request.args.get('count', default=1, type=int)
    cards = deck_api.draw_cards(count)
    return jsonify({'cards': cards})


@app.route('/hand', methods=['GET'])
def show_hand():
    """
    Shows the current player's hand and its total value.
    """
    game_state = get_player_state()
    value = calculate_hand_value(game_state['player_hand'])
    return jsonify({
        'hand': game_state['player_hand'],
        'hand_value': value
    })


def main():
    """
    CLI test for drawing two cards using the DeckAPI class directly.
    Not used in the web app context.
    """
    deck = DeckAPI()
    print("Drawing 2 cards...")
    cards = deck.draw_cards(2)
    for card in cards:
        print(f"{card['value']} of {card['suit']}")


if __name__ == "__main__":
    app.run(debug=True)
