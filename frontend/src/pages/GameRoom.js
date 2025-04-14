import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function GameRoom({ playerInfo }) {
  const [localPlayerInfo, setLocalPlayerInfo] = useState(playerInfo);
  const [dealerCard, setDealerCard] = useState(null);
  const [hand, setHand] = useState([]);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();  // Hook for redirecting

  // Fallback to localStorage if playerInfo isn't passed in
  useEffect(() => {
    if (!playerInfo) {
      const storedInfo = localStorage.getItem('playerInfo');
      if (storedInfo) {
        setLocalPlayerInfo(JSON.parse(storedInfo));
      }
    }
  }, [playerInfo]);

  useEffect(() => {
    if (!localPlayerInfo) {
      // Redirect to the home page if no player info is found
      navigate('/');
    }
  }, [localPlayerInfo, navigate]);

  const fetchHand = async () => {
    try {
      const res = await axios.get('http://localhost:5000/hand', { withCredentials: true });
      setHand(res.data.hand);
    } catch (err) {
      console.error('Error fetching hand:', err);
    }
  };

  const startGame = async () => {
    try {
      const res = await axios.post('http://localhost:5000/start-game', {}, { withCredentials: true });
      setDealerCard(res.data.dealer_card);
      fetchHand();
    } catch (err) {
      console.error('Error starting game:', err);
    }
  };

  const hit = async () => {
    try {
      const res = await axios.post('http://localhost:5000/hit', {}, { withCredentials: true });
      setHand(res.data.hand);
      if (res.data.total > 21) {
        setMessage('Bust! You lose');
      }
    } catch (err) {
      console.error('Error on hit:', err);
    }
  };

  const stay = async () => {
    try {
      const res = await axios.post('http://localhost:5000/stay', {}, { withCredentials: true });
      setMessage(res.data.result);
    } catch (err) {
      console.error('Error on stay:', err);
    }
  };

  useEffect(() => {
    if (localPlayerInfo) {
      fetchHand();
    }
  }, [localPlayerInfo]);

  if (!localPlayerInfo) return <p>Loading...</p>;

  return (
    <div>
      <h2>Welcome to the Room</h2>
      <p>Room Code: {localPlayerInfo.room_code}</p>
      <p>Your Hand:</p>
      <ul>
        {hand.map((card, i) => (
          <li key={i}>{card.value} of {card.suit}</li>
        ))}
      </ul>
      {dealerCard && <p>Dealer shows: {dealerCard.value} of {dealerCard.suit}</p>}
      <button onClick={startGame}>Start Game</button>
      <button onClick={hit}>Hit</button>
      <button onClick={stay}>Stay</button>
      <p>{message}</p>
    </div>
  );
}

export default GameRoom;
