import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Home({ setPlayerInfo }) {
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = useState('');

  const createRoom = async () => {
    try {
      const res = await axios.post('http://localhost:5000/create-room', {}, { withCredentials: true });
      setPlayerInfo(res.data);
      navigate('/room');
    } catch (err) {
      console.error('Error creating room:', err);
    }
  };

  const joinRoom = async () => {
    try {
      const res = await axios.post('http://localhost:5000/join-room', { room_code: roomCode }, { withCredentials: true });
      setPlayerInfo(res.data);
      navigate('/room');
    } catch (err) {
      console.error('Error joining room:', err);
    }
  };

  return (
    <div className="home">
      <h1>Blackjack Lobby</h1>
      <button onClick={createRoom}>Create Room</button>
      <input
        value={roomCode}
        onChange={(e) => setRoomCode(e.target.value)}
        placeholder="Enter Room Code"
      />
      <button onClick={joinRoom}>Join Room</button>
    </div>
  );
}

export default Home;
