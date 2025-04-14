import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import GameRoom from './pages/GameRoom';

function App() {
    const [playerInfo, setPlayerInfo] = useState(null);

    return (
    <Router>
    <Routes>
    <Route path="/" element={<Home setPlayerInfo={setPlayerInfo} />} />
    <Route path="/room" element={<GameRoom playerInfo={playerInfo} />} />
    </Routes>
    </Router>

    );
}

export default App;
