import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import PlayPage from './pages/PlayPage';
import PuzzlePage from './pages/PuzzlePage';
import LearnPage from './pages/LearnPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <Routes>
          <Route path="/" element={<PlayPage />} />
          <Route path="/play" element={<PlayPage />} />
          <Route path="/puzzles" element={<PuzzlePage />} />
          <Route path="/learn" element={<LearnPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

