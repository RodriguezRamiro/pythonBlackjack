import requests

BASE_URL = "https://deckofcardsapi.com/api/deck"

class DeckAPI:
    def __init__(self):
        self.deck_id = self._create_new_deck()

    def _create_new_deck(self):
        response = requests.get(f"{BASE_URL}/new/shuffle/?deck_count=1")
        response.raise_for_status()
        data = response.json()
        return data["deck_id"]

    def draw_cards(self, count=1):
        response = requests.get(f"{BASE_URL}/{self.deck_id}draw/?count={count}")
        response.raise_for_status()
        return response.json()["cards"]

    def reshuffle(self):
        response = requests.get(f"{BASE_URL}/{self.deck_id}/shuffle/")
        response.raise_for_status()
        return response.ok