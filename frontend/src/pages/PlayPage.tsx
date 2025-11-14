import { useState, useEffect } from 'react';
import ChessBoard from '@/components/ChessBoard';
import { gameAPI } from '@/services/api';
import { Chess } from 'chess.js';

export default function PlayPage() {
  const [gameId, setGameId] = useState<number | null>(null);
  const [position, setPosition] = useState('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
  const [gameStatus, setGameStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [lastMoveIndex, setLastMoveIndex] = useState<number>(-1);
  const [botDifficulty, setBotDifficulty] = useState<number>(10); // Default: Orta

  useEffect(() => {
    startNewGame();
  }, []);

  const startNewGame = async () => {
    try {
      setLoading(true);
      setError(null);
      setMoveHistory([]);
      setLastMoveIndex(-1);
      const response = await gameAPI.create({ 
        is_bot_game: true, 
        bot_difficulty: botDifficulty 
      });
      const game = response.data;
      setGameId(game.id);
      
      // Get initial session
      const sessionResponse = await gameAPI.getSession(game.id);
      setPosition(sessionResponse.data.current_fen);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Oyun başlatılamadı');
    } finally {
      setLoading(false);
    }
  };

  const handleMove = async (move: { from: string; to: string }) => {
    if (!gameId || gameStatus) return;

    try {
      setLoading(true);
      setError(null);
      
      const moveUci = `${move.from}${move.to}`;
      const response = await gameAPI.makeMove({
        game_id: gameId,
        move: moveUci,
      });

      const moveData = response.data;
      
      // Update position - new_fen already includes bot's move if bot played
      if (moveData.new_fen) {
        setPosition(moveData.new_fen);
      }

      // Update move history
      if (moveData.move_history) {
        setMoveHistory(moveData.move_history);
        setLastMoveIndex(moveData.move_history.length - 1);
      }

      // Update game status - set to null if in_progress to allow moves
      if (moveData.game_status && moveData.game_status !== 'in_progress') {
        setGameStatus(moveData.game_status);
      } else {
        setGameStatus(null); // Allow moves when game is in progress
      }
      
      // Ensure loading is set to false after bot move completes
      // Bot move is already included in new_fen, so we can enable the board
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Hamle yapılamadı');
    } finally {
      setLoading(false);
    }
  };

  // Format moves for display
  const formatMoves = () => {
    const chess = new Chess();
    const formatted: { white: string; black: string | null; moveNumber: number }[] = [];
    
    moveHistory.forEach((uci, index) => {
      try {
        const move = chess.move({
          from: uci.substring(0, 2),
          to: uci.substring(2, 4),
          promotion: uci.length > 4 ? uci[4] : undefined
        });
        
        if (move) {
          if (index % 2 === 0) {
            // White move
            formatted.push({
              white: move.san,
              black: null,
              moveNumber: Math.floor(index / 2) + 1
            });
          } else {
            // Black move
            const lastEntry = formatted[formatted.length - 1];
            if (lastEntry) {
              lastEntry.black = move.san;
            }
          }
        }
      } catch (e) {
        // Skip invalid moves
      }
    });
    
    return formatted;
  };

  const formattedMoves = formatMoves();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Satranç Oyna</h1>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-4 flex justify-between items-center flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bot Zorluk Seviyesi
                </label>
                <select
                  value={botDifficulty}
                  onChange={(e) => setBotDifficulty(Number(e.target.value))}
                  disabled={loading || gameId !== null}
                  className="border border-gray-300 rounded px-3 py-2 text-sm"
                >
                  <option value={5}>Kolay</option>
                  <option value={10}>Orta</option>
                  <option value={15}>Zor</option>
                  <option value={20}>En Zor</option>
                </select>
              </div>
              {gameStatus && (
                <div className="text-lg font-semibold">
                  Oyun Durumu: {gameStatus === 'white_won' ? 'Beyaz Kazandı' : 
                               gameStatus === 'black_won' ? 'Siyah Kazandı' : 
                               gameStatus === 'draw' ? 'Berabere' : 'Devam Ediyor'}
                </div>
              )}
            </div>
            <button
              onClick={startNewGame}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
              Yeni Oyun
            </button>
          </div>

          <div className="flex gap-6">
            {/* Left side - White moves */}
            <div className="w-32 flex-shrink-0">
              <div className="bg-gray-100 p-3 rounded mb-2">
                <h3 className="font-bold text-sm text-gray-700 mb-2">Beyaz</h3>
                <div className="space-y-1 max-h-96 overflow-y-auto">
                  {formattedMoves.map((entry, idx) => (
                    <div
                      key={idx}
                      className={`text-xs p-1 rounded ${
                        lastMoveIndex === idx * 2
                          ? 'bg-yellow-200 font-bold'
                          : 'hover:bg-gray-200'
                      }`}
                    >
                      {entry.moveNumber}. {entry.white}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Center - Chess board */}
            <div className="flex-1 flex justify-center">
              <ChessBoard
                position={position}
                onMove={handleMove}
                disabled={loading || (gameStatus !== null && gameStatus !== 'in_progress')}
              />
            </div>

            {/* Right side - Black moves */}
            <div className="w-32 flex-shrink-0">
              <div className="bg-gray-800 p-3 rounded mb-2">
                <h3 className="font-bold text-sm text-white mb-2">Siyah</h3>
                <div className="space-y-1 max-h-96 overflow-y-auto">
                  {formattedMoves.map((entry, idx) => (
                    <div
                      key={idx}
                      className={`text-xs p-1 rounded ${
                        entry.black && lastMoveIndex === idx * 2 + 1
                          ? 'bg-yellow-600 font-bold text-white'
                          : entry.black
                          ? 'text-white hover:bg-gray-700'
                          : 'text-gray-500'
                      }`}
                    >
                      {entry.black || '-'}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
