import { useState, useEffect } from 'react';
import ChessBoard from '@/components/ChessBoard';
import { puzzleAPI } from '@/services/api';

export default function PuzzlePage() {
  const [puzzle, setPuzzle] = useState<any>(null);
  const [position, setPosition] = useState('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [solved, setSolved] = useState(false);

  useEffect(() => {
    loadRandomPuzzle();
  }, []);

  const loadRandomPuzzle = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setSolved(false);
      const response = await puzzleAPI.getRandom();
      const puzzleData = response.data;
      setPuzzle(puzzleData);
      setPosition(puzzleData.fen);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Bulmaca yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleMove = async (move: { from: string; to: string }) => {
    if (!puzzle || solved) return;

    try {
      setLoading(true);
      setMessage(null);
      
      const moveUci = `${move.from}${move.to}`;
      const response = await puzzleAPI.attempt({
        puzzle_id: puzzle.id,
        move: moveUci,
      });

      const attemptData = response.data;
      setMessage(attemptData.message);

      if (attemptData.correct) {
        if (attemptData.is_complete) {
          setSolved(true);
          setMessage('Tebrikler! Bulmacayı çözdünüz!');
        } else if (attemptData.next_move) {
          // Auto-play next move
          setTimeout(() => {
            // Update position after correct move
            // In a real implementation, you'd update the board state
          }, 500);
        }
      }
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Hamle işlenemedi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Satranç Bulmacaları</h1>

        {message && (
          <div className={`mb-4 px-4 py-3 rounded ${
            message.includes('Tebrikler') || message.includes('Correct')
              ? 'bg-green-100 border border-green-400 text-green-700'
              : 'bg-red-100 border border-red-400 text-red-700'
          }`}>
            {message}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-6">
          {puzzle && (
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">
                Zorluk: {puzzle.difficulty} | Tema: {puzzle.theme || 'Genel'}
              </div>
              {puzzle.description && (
                <p className="text-gray-700">{puzzle.description}</p>
              )}
            </div>
          )}

          <div className="mb-4 flex justify-end">
            <button
              onClick={loadRandomPuzzle}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
              Yeni Bulmaca
            </button>
          </div>

          <ChessBoard
            position={position}
            onMove={handleMove}
            disabled={loading || solved}
          />
        </div>
      </div>
    </div>
  );
}

