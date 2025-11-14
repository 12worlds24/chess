import { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Square } from 'chess.js';

interface ChessBoardProps {
  position: string;
  onMove?: (move: { from: string; to: string; promotion?: string }) => void;
  boardOrientation?: 'white' | 'black';
  disabled?: boolean;
}

export default function ChessBoardComponent({
  position,
  onMove,
  boardOrientation = 'white',
  disabled = false,
}: ChessBoardProps) {
  const [game, setGame] = useState(new Chess(position));

  useEffect(() => {
    try {
      const newGame = new Chess(position);
      setGame(newGame);
    } catch (error) {
      console.error('Invalid FEN position:', error);
    }
  }, [position]);

  function onDrop(sourceSquare: Square, targetSquare: Square) {
    if (disabled || !onMove) return false;

    try {
      const move = game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q',
      });

      if (move === null) return false;

      onMove({
        from: sourceSquare,
        to: targetSquare,
        promotion: move.promotion,
      });

      return true;
    } catch (error) {
      return false;
    }
  }

  return (
    <div className="w-full max-w-xl mx-auto">
      <Chessboard
        position={game.fen()}
        onPieceDrop={onDrop}
        boardOrientation={boardOrientation}
        arePiecesDraggable={!disabled}
        boardWidth={500}
        customBoardStyle={{
          borderRadius: '4px',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
        }}
        customLightSquareStyle={{ backgroundColor: '#f0d9b5' }}
        customDarkSquareStyle={{ backgroundColor: '#b58863' }}
      />
    </div>
  );
}

