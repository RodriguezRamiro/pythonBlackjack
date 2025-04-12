import React, { useState } from 'react';
import axios from 'axios;'

function App(){
const [roomCode, setRoomCode] = useState('');
const [playerId, setPlayerId] = useState('');
const [message, setMessage] = useState('');
const createRoom = async () => {
const res = await axios.post('/create-room');
setRoomCode(res.data.room_code);
setPlayerId(res.data.player_id);
setMessage('Room Created!');

};

return (
<div style={{ padding: 20}}>
<h1>BlackJack</h1>
<button onClick={createRoom}>Create Room</button>
{message && <p> {message}</p>}
{roomCode && <p>Room Code: {roomCode}</p>}
{playerId && <p>Player ID: {playerId}</p>}
</div>
);
}

export default App;