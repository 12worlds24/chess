import { useState, useEffect } from 'react';
import ChessBoard from '@/components/ChessBoard';
import { Chess } from 'chess.js';
import { gameAPI } from '@/services/api';

export default function LearnPage() {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [selectedOpening, setSelectedOpening] = useState<number | null>(null);
  const [currentMoveIndex, setCurrentMoveIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const openings = [
    {
      id: 0,
      name: "İspanyol Açılışı (Ruy Lopez)",
      moves: ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
      moveNotation: "1.e4 e5 2.Nf3 Nc6 3.Bb5",
      description: "Klasik ve güçlü bir açılış. Beyaz, siyahın atını tehdit ederek merkez kontrolünü sağlar.",
      difficulty: "Orta",
      explanation: "Bu açılış, beyazın e4 ile merkezi kontrol etmesiyle başlar. Siyah e5 ile cevap verir. Beyaz atını f3'e çıkarır ve siyah da atını c6'ya oynar. Son olarak beyaz, filini b5'e oynayarak siyahın atını tehdit eder. Bu açılış, merkez kontrolü ve taş gelişimi açısından çok güçlüdür.",
      variations: [
        "3...a6 - Morphy Savunması",
        "3...Nf6 - Berlin Savunması",
        "3...Bc5 - Klasik Varyant"
      ]
    },
    {
      id: 1,
      name: "Sicilya Savunması",
      moves: ["e2e4", "c7c5"],
      moveNotation: "1.e4 c5",
      description: "Siyahın en popüler ve agresif cevabı. Asimetrik bir oyun yapısı oluşturur.",
      difficulty: "Zor",
      explanation: "Sicilya Savunması, siyahın e4'e en popüler cevabıdır. Siyah, c5 ile merkezi dolaylı olarak kontrol etmeye çalışır ve asimetrik bir oyun yapısı oluşturur. Bu açılış, dinamik oyunlar ve karşı saldırı fırsatları sunar.",
      variations: [
        "2.Nf3 d6 - Klasik Varyant",
        "2.Nf3 Nc6 - Taimanov Varyantı",
        "2.c3 - Alapin Varyantı"
      ]
    },
    {
      id: 2,
      name: "Fransız Savunması",
      moves: ["e2e4", "e7e6"],
      moveNotation: "1.e4 e6",
      description: "Sağlam bir savunma. Siyah, merkezi kapalı tutarak karşı saldırı fırsatı arar.",
      difficulty: "Kolay",
      explanation: "Fransız Savunması, sağlam ve güvenilir bir açılıştır. Siyah, e6 ile filini geliştirir ve d5 ile merkeze saldırmayı planlar. Bu açılış, kapalı pozisyonlar ve stratejik oyunlar için idealdir.",
      variations: [
        "2.d4 d5 - Klasik Varyant",
        "2.d4 d5 3.Nc3 - Tarrasch Varyantı",
        "2.d4 d5 3.e5 - İlerleme Varyantı"
      ]
    },
    {
      id: 3,
      name: "İtalyan Açılışı",
      moves: ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
      moveNotation: "1.e4 e5 2.Nf3 Nc6 3.Bc4",
      description: "Hızlı gelişim ve merkez kontrolü sağlayan klasik bir açılış.",
      difficulty: "Kolay",
      explanation: "İtalyan Açılışı, hızlı taş gelişimi ve merkez kontrolü sağlar. Beyaz, filini c4'e oynayarak f7 karesini (siyahın en zayıf karesi) tehdit eder. Bu açılış, agresif oyunlar ve hızlı saldırılar için idealdir.",
      variations: [
        "3...Bc5 - Klasik İtalyan",
        "3...Nf6 - İki At Savunması",
        "3...f5 - Calabrese Varyantı"
      ]
    },
    {
      id: 4,
      name: "Caro-Kann Savunması",
      moves: ["e2e4", "c7c6"],
      moveNotation: "1.e4 c6",
      description: "Sağlam ve güvenli bir savunma. Siyah, piyon yapısını koruyarak oyunu dengeler.",
      difficulty: "Kolay",
      explanation: "Caro-Kann Savunması, sağlam ve güvenli bir açılıştır. Siyah, c6 ile d5 hamlesini hazırlar ve piyon yapısını korur. Bu açılış, zayıflık yaratmadan oyunu dengeler ve karşı saldırı fırsatları sunar.",
      variations: [
        "2.d4 d5 - Klasik Varyant",
        "2.d4 d5 3.Nc3 - Klasik Varyant",
        "2.d4 d5 3.e5 - İlerleme Varyantı"
      ]
    }
  ];

  const tactics = [
    {
      name: "Çatal (Fork)",
      description: "Bir taşın aynı anda iki veya daha fazla düşman taşı tehdit etmesi. En yaygın taktik motiflerinden biridir.",
      example: "At ile iki taşı aynı anda tehdit etmek"
    },
    {
      name: "Açmaz (Pin)",
      description: "Bir taşın, arkasındaki daha değerli taşı korumak için hareket edememesi durumu.",
      example: "Fil ile şahı açmaza almak"
    },
    {
      name: "Çifte Tehdit (Double Attack)",
      description: "İki farklı tehdit aynı anda yapılır. Rakip sadece birini savunabilir.",
      example: "Hem vezir hem de at tehdidi"
    },
    {
      name: "Açılış (Discovered Attack)",
      description: "Bir taşın hareket etmesiyle, arkasındaki başka bir taşın tehdit oluşturması.",
      example: "Fil hareket edince, arkasındaki kalenin veziri tehdit etmesi"
    },
    {
      name: "Şah Çekme ve Mat",
      description: "Şahı tehdit altına alıp, kaçış yolu bırakmamak. Oyunu bitiren taktik.",
      example: "Vezir ve kale ile mat kombinasyonu"
    }
  ];

  const analysisTips = [
    {
      title: "Hamle Öncesi Düşün",
      content: "Her hamleden önce rakip hamlelerini düşün. 'Rakip ne yapabilir?' sorusunu sor."
    },
    {
      title: "Taktik Fırsatları Ara",
      content: "Çatal, açmaz, çifte tehdit gibi taktik motifleri sürekli kontrol et."
    },
    {
      title: "Zayıf Kareleri Belirle",
      content: "Rakibin zayıf karelerini ve korunmasız taşlarını tespit et."
    },
    {
      title: "Merkez Kontrolü",
      content: "Merkez kareleri (d4, d5, e4, e5) kontrol etmek genellikle avantaj sağlar."
    },
    {
      title: "Taş Gelişimi",
      content: "Tüm taşlarınızı aktif karelerde konumlandırın. Pasif taşlar zayıflıktır."
    },
    {
      title: "Güvenlik Kontrolü",
      content: "Hamle yapmadan önce, kendi şahınızın güvende olduğundan emin olun."
    }
  ];

  // Get current position for selected opening
  const getCurrentPosition = () => {
    if (selectedOpening === null) return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
    
    const opening = openings[selectedOpening];
    const chess = new Chess();
    
    for (let i = 0; i <= currentMoveIndex && i < opening.moves.length; i++) {
      const move = opening.moves[i];
      try {
        chess.move({
          from: move.substring(0, 2),
          to: move.substring(2, 4),
          promotion: move.length > 4 ? move[4] : undefined
        });
      } catch (e) {
        console.error('Invalid move:', move);
      }
    }
    
    return chess.fen();
  };

  // Auto-play moves
  useEffect(() => {
    if (isPlaying && selectedOpening !== null) {
      const opening = openings[selectedOpening];
      if (currentMoveIndex < opening.moves.length - 1) {
        const timer = setTimeout(() => {
          setCurrentMoveIndex(prev => prev + 1);
        }, 1500);
        return () => clearTimeout(timer);
      } else {
        setIsPlaying(false);
      }
    }
  }, [isPlaying, currentMoveIndex, selectedOpening]);

  const handlePreviousMove = () => {
    if (currentMoveIndex > 0) {
      setCurrentMoveIndex(prev => prev - 1);
      setIsPlaying(false);
    }
  };

  const handleNextMove = () => {
    if (selectedOpening !== null) {
      const opening = openings[selectedOpening];
      if (currentMoveIndex < opening.moves.length - 1) {
        setCurrentMoveIndex(prev => prev + 1);
        setIsPlaying(false);
      }
    }
  };

  const handleReset = () => {
    setCurrentMoveIndex(0);
    setIsPlaying(false);
  };

  const handlePlayPause = () => {
    if (selectedOpening !== null) {
      const opening = openings[selectedOpening];
      if (currentMoveIndex >= opening.moves.length - 1) {
        handleReset();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Satranç Öğren</h1>
        
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Öğrenme Materyalleri</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button
              onClick={() => {
                setActiveSection(activeSection === 'openings' ? null : 'openings');
                setSelectedOpening(null);
                setCurrentMoveIndex(0);
                setIsPlaying(false);
              }}
              className={`p-4 rounded-lg border-2 transition-all ${
                activeSection === 'openings'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-300'
              }`}
            >
              <div className="flex items-center">
                <div className="w-4 h-4 bg-blue-500 rounded-full mr-3"></div>
                <h3 className="text-xl font-semibold">Açılış Teorisi</h3>
              </div>
              <p className="text-gray-600 mt-2 text-sm">
                Satranç açılışlarını öğrenin ve oyununuzu güçlendirin.
              </p>
            </button>
            
            <button
              onClick={() => setActiveSection(activeSection === 'tactics' ? null : 'tactics')}
              className={`p-4 rounded-lg border-2 transition-all ${
                activeSection === 'tactics'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 hover:border-green-300'
              }`}
            >
              <div className="flex items-center">
                <div className="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
                <h3 className="text-xl font-semibold">Taktik Örnekleri</h3>
              </div>
              <p className="text-gray-600 mt-2 text-sm">
                Çeşitli taktik örnekleri ile oyununuzu geliştirin.
              </p>
            </button>
            
            <button
              onClick={() => setActiveSection(activeSection === 'analysis' ? null : 'analysis')}
              className={`p-4 rounded-lg border-2 transition-all ${
                activeSection === 'analysis'
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-300 hover:border-purple-300'
              }`}
            >
              <div className="flex items-center">
                <div className="w-4 h-4 bg-purple-500 rounded-full mr-3"></div>
                <h3 className="text-xl font-semibold">Oyun Analizi</h3>
              </div>
              <p className="text-gray-600 mt-2 text-sm">
                Oyunlarınızı analiz edin ve hatalarınızdan öğrenin.
              </p>
            </button>

            <button
              onClick={() => setActiveSection(activeSection === 'practice' ? null : 'practice')}
              className={`p-4 rounded-lg border-2 transition-all ${
                activeSection === 'practice'
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-gray-300 hover:border-orange-300'
              }`}
            >
              <div className="flex items-center">
                <div className="w-4 h-4 bg-orange-500 rounded-full mr-3"></div>
                <h3 className="text-xl font-semibold">Öğretici Oyun</h3>
              </div>
              <p className="text-gray-600 mt-2 text-sm">
                Bot ile öğretici oyun oynayın ve açılışları öğrenin.
              </p>
            </button>
          </div>
        </div>

        {/* Açılış Teorisi */}
        {activeSection === 'openings' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-blue-600">Açılış Teorisi</h2>
              <p className="text-gray-700 mb-6">
                Satranç açılışları oyunun ilk hamleleridir ve oyunun yönünü belirler. 
                İyi bir açılış bilgisi, oyununuzu güçlendirir ve size avantaj sağlar.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {openings.map((opening) => (
                  <button
                    key={opening.id}
                    onClick={() => {
                      setSelectedOpening(opening.id);
                      setCurrentMoveIndex(0);
                      setIsPlaying(false);
                    }}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      selectedOpening === opening.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold text-gray-800">{opening.name}</h3>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        opening.difficulty === 'Kolay' ? 'bg-green-100 text-green-800' :
                        opening.difficulty === 'Orta' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {opening.difficulty}
                      </span>
                    </div>
                    <p className="text-sm font-mono text-gray-600 mb-2">{opening.moveNotation}</p>
                    <p className="text-sm text-gray-700">{opening.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Selected Opening Detail */}
            {selectedOpening !== null && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Chess Board */}
                  <div>
                    <h3 className="text-xl font-semibold mb-4">
                      {openings[selectedOpening].name}
                    </h3>
                    <div className="mb-4">
                      <ChessBoard
                        position={getCurrentPosition()}
                        disabled={true}
                      />
                    </div>
                    
                    {/* Controls */}
                    <div className="flex items-center justify-center gap-2 mb-4">
                      <button
                        onClick={handleReset}
                        className="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm font-medium"
                      >
                        Başa Dön
                      </button>
                      <button
                        onClick={handlePreviousMove}
                        disabled={currentMoveIndex === 0}
                        className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ← Önceki
                      </button>
                      <button
                        onClick={handlePlayPause}
                        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded text-sm font-medium"
                      >
                        {isPlaying ? '⏸ Duraklat' : '▶ Oynat'}
                      </button>
                      <button
                        onClick={handleNextMove}
                        disabled={selectedOpening !== null && currentMoveIndex >= openings[selectedOpening].moves.length - 1}
                        className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Sonraki →
                      </button>
                    </div>

                    {/* Move Progress */}
                    <div className="mb-4">
                      <div className="flex justify-between text-sm text-gray-600 mb-1">
                        <span>Hamle: {currentMoveIndex + 1} / {openings[selectedOpening].moves.length}</span>
                        <span>{Math.round(((currentMoveIndex + 1) / openings[selectedOpening].moves.length) * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${((currentMoveIndex + 1) / openings[selectedOpening].moves.length) * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Current Move Notation */}
                    <div className="bg-gray-50 p-3 rounded">
                      <p className="text-sm font-mono text-gray-700">
                        {openings[selectedOpening].moveNotation.split(' ').slice(0, currentMoveIndex + 1).join(' ')}
                      </p>
                    </div>
                  </div>

                  {/* Explanation */}
                  <div>
                    <h4 className="text-lg font-semibold mb-3">Açıklama</h4>
                    <p className="text-gray-700 mb-4 leading-relaxed">
                      {openings[selectedOpening].explanation}
                    </p>

                    <h4 className="text-lg font-semibold mb-3">Varyantlar</h4>
                    <ul className="list-disc list-inside space-y-2 mb-4">
                      {openings[selectedOpening].variations.map((variation, idx) => (
                        <li key={idx} className="text-gray-700">{variation}</li>
                      ))}
                    </ul>

                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <h5 className="font-semibold text-blue-800 mb-2">💡 İpucu</h5>
                      <p className="text-sm text-blue-700">
                        Bu açılışı öğrenirken, her hamlenin amacını düşünün. 
                        Taş gelişimi, merkez kontrolü ve şah güvenliği açılışın temel prensipleridir.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Taktik Örnekleri */}
        {activeSection === 'tactics' && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-semibold mb-4 text-green-600">Taktik Örnekleri</h2>
            <p className="text-gray-700 mb-6">
              Taktikler, satrançta avantaj kazanmanın temel yoludur. 
              Bu temel taktik motiflerini öğrenerek oyununuzu önemli ölçüde geliştirebilirsiniz.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tactics.map((tactic, index) => (
                <div key={index} className="border-l-4 border-green-500 pl-4 py-3 bg-gray-50 rounded-r">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{tactic.name}</h3>
                  <p className="text-gray-700 mb-2">{tactic.description}</p>
                  <p className="text-sm text-gray-600 italic">Örnek: {tactic.example}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Oyun Analizi */}
        {activeSection === 'analysis' && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-semibold mb-4 text-purple-600">Oyun Analizi</h2>
            <p className="text-gray-700 mb-6">
              Oyunlarınızı analiz etmek, hatalarınızı görmenizi ve gelecekte aynı hataları 
              yapmamanızı sağlar. İşte etkili oyun analizi için bazı ipuçları:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysisTips.map((tip, index) => (
                <div key={index} className="border-l-4 border-purple-500 pl-4 py-3 bg-gray-50 rounded-r">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{tip.title}</h3>
                  <p className="text-gray-700">{tip.content}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h3 className="text-lg font-semibold text-purple-800 mb-2">Analiz Süreci</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                <li>Oyununuzu hamle hamle gözden geçirin</li>
                <li>Her hamlede alternatif hamleleri düşünün</li>
                <li>Hatalarınızı ve kaçırdığınız fırsatları not edin</li>
                <li>Rakibin güçlü hamlelerini inceleyin</li>
                <li>Benzer pozisyonlarda ne yapacağınızı planlayın</li>
              </ol>
            </div>
          </div>
        )}

        {/* Öğretici Oyun */}
        {activeSection === 'practice' && <PracticeGame />}
      </div>
    </div>
  );
}

// Öğretici Oyun Komponenti
function PracticeGame() {
  const [gameId, setGameId] = useState<number | null>(null);
  const [position, setPosition] = useState('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
  const [gameStatus, setGameStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [positionHistory, setPositionHistory] = useState<string[]>(['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1']);
  const [hint, setHint] = useState<string | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [selectedOpening, setSelectedOpening] = useState<number | null>(null);
  const [openingMoves, setOpeningMoves] = useState<string[]>([]);
  const [currentOpeningMove, setCurrentOpeningMove] = useState<number>(0);

  const practiceOpenings = [
    {
      id: 0,
      name: "İspanyol Açılışı (Ruy Lopez)",
      moves: ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
      description: "Klasik ve güçlü bir açılış"
    },
    {
      id: 1,
      name: "İtalyan Açılışı",
      moves: ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
      description: "Hızlı gelişim ve merkez kontrolü"
    },
    {
      id: 2,
      name: "Fransız Savunması",
      moves: ["e2e4", "e7e6"],
      description: "Sağlam bir savunma"
    }
  ];

  useEffect(() => {
    startNewGame();
  }, []);

  const startNewGame = async () => {
    try {
      setLoading(true);
      setError(null);
      setMoveHistory([]);
      setPositionHistory(['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1']);
      setHint(null);
      setShowHint(false);
      setSelectedOpening(null);
      setOpeningMoves([]);
      setCurrentOpeningMove(0);
      
      const response = await gameAPI.create({ 
        is_bot_game: true, 
        bot_difficulty: 5 // Kolay seviye öğretici oyun için
      });
      const game = response.data;
      setGameId(game.id);
      
      const sessionResponse = await gameAPI.getSession(game.id);
      setPosition(sessionResponse.data.current_fen);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Oyun başlatılamadı');
    } finally {
      setLoading(false);
    }
  };

  const startOpeningPractice = (openingId: number) => {
    const opening = practiceOpenings[openingId];
    setSelectedOpening(openingId);
    setOpeningMoves(opening.moves);
    setCurrentOpeningMove(0);
    setHint(`Şimdi ${opening.name} açılışını öğreneceğiz. İlk hamle: ${opening.moves[0]}`);
    setShowHint(true);
  };

  const handleMove = async (move: { from: string; to: string }) => {
    if (!gameId || gameStatus || loading) return;

    try {
      setLoading(true);
      setError(null);
      setHint(null);
      setShowHint(false);
      
      const moveUci = `${move.from}${move.to}`;
      
      // Check if we're practicing an opening
      if (selectedOpening !== null && currentOpeningMove < openingMoves.length) {
        const expectedMove = openingMoves[currentOpeningMove];
        if (moveUci !== expectedMove) {
          setHint(`Bu açılışta önerilen hamle: ${expectedMove}. Ama devam edebilirsiniz!`);
          setShowHint(true);
        } else {
          setCurrentOpeningMove(prev => prev + 1);
          if (currentOpeningMove + 1 < openingMoves.length) {
            setHint(`Harika! Şimdi: ${openingMoves[currentOpeningMove + 1]}`);
            setShowHint(true);
          } else {
            setHint('Açılış tamamlandı! Artık serbest oynayabilirsiniz.');
            setShowHint(true);
          }
        }
      }
      
      const response = await gameAPI.makeMove({
        game_id: gameId,
        move: moveUci,
      });

      const moveData = response.data;
      
      if (moveData.new_fen) {
        setPosition(moveData.new_fen);
        setPositionHistory(prev => [...prev, moveData.new_fen]);
        if (moveData.move_history) {
          setMoveHistory(moveData.move_history);
        }
      }

      if (moveData.game_status && moveData.game_status !== 'in_progress') {
        setGameStatus(moveData.game_status);
      } else {
        setGameStatus(null);
      }

      // Get move suggestion after user move
      if (gameId && !moveData.bot_move) {
        try {
          const suggestionResponse = await gameAPI.suggestMove(gameId);
          const suggestedMove = suggestionResponse.data.suggested_move;
          if (suggestedMove !== moveUci) {
            setHint(`💡 İpucu: Daha iyi bir hamle olabilir. Önerilen: ${suggestedMove}`);
            setShowHint(true);
          }
        } catch (err) {
          // Ignore suggestion errors
        }
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Hamle yapılamadı');
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = async () => {
    if (!gameId || positionHistory.length <= 1 || loading) return;

    try {
      setLoading(true);
      setError(null);
      setHint(null);
      setShowHint(false);
      
      const response = await gameAPI.undoMove(gameId, 1);
      const undoData = response.data;
      
      if (undoData.new_fen) {
        setPosition(undoData.new_fen);
        setPositionHistory(prev => {
          const newHistory = [...prev];
          if (newHistory.length > 1) {
            newHistory.pop();
          }
          return newHistory;
        });
        
        if (undoData.move_history) {
          setMoveHistory(undoData.move_history);
        }
      }
      
      if (undoData.game_status && undoData.game_status !== 'in_progress') {
        setGameStatus(undoData.game_status);
      } else {
        setGameStatus(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Hamle geri alınamadı');
    } finally {
      setLoading(false);
    }
  };

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
            formatted.push({
              white: move.san,
              black: null,
              moveNumber: Math.floor(index / 2) + 1
            });
          } else {
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
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-semibold mb-4 text-orange-600">Öğretici Oyun</h2>
        <p className="text-gray-700 mb-6">
          Bot ile öğretici bir oyun oynayın. Bot hamlelerinizi analiz eder ve daha iyi hamleler önerir.
          Açılışları öğrenmek için bir açılış seçin ve bot size rehberlik edecek.
        </p>

        {/* Opening Selection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Açılış Seçin (Opsiyonel)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {practiceOpenings.map((opening) => (
              <button
                key={opening.id}
                onClick={() => startOpeningPractice(opening.id)}
                className={`p-3 border-2 rounded-lg text-left transition-all ${
                  selectedOpening === opening.id
                    ? 'border-orange-500 bg-orange-50'
                    : 'border-gray-300 hover:border-orange-300'
                }`}
              >
                <h4 className="font-semibold">{opening.name}</h4>
                <p className="text-sm text-gray-600">{opening.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Hint Display */}
        {showHint && hint && (
          <div className="mb-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
            <p className="text-yellow-800">{hint}</p>
          </div>
        )}

        {/* Controls */}
        <div className="mb-4 flex gap-3 flex-wrap">
          <button
            onClick={startNewGame}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            Yeni Oyun
          </button>
          <button
            onClick={handleUndo}
            disabled={positionHistory.length <= 1 || loading}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            ↶ Hamle Geri Al
          </button>
          <button
            onClick={async () => {
              if (gameId) {
                try {
                  setLoading(true);
                  const suggestionResponse = await gameAPI.suggestMove(gameId);
                  const suggestedMove = suggestionResponse.data.suggested_move;
                  setHint(`💡 Önerilen hamle: ${suggestedMove}`);
                  setShowHint(true);
                } catch (err) {
                  setError('İpucu alınamadı');
                } finally {
                  setLoading(false);
                }
              }
            }}
            disabled={!gameId || loading}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            💡 İpucu Al
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Game Board and Move History */}
        <div className="flex gap-6">
          {/* Left side - White moves */}
          <div className="w-32 flex-shrink-0">
            <div className="bg-gray-100 p-3 rounded mb-2">
              <h3 className="font-bold text-sm text-gray-700 mb-2">Beyaz</h3>
              <div className="space-y-1 max-h-96 overflow-y-auto">
                {formattedMoves.map((entry, idx) => (
                  <div key={idx} className="text-xs p-1 rounded hover:bg-gray-200">
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
                  <div key={idx} className="text-xs p-1 rounded text-white hover:bg-gray-700">
                    {entry.black || '-'}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {gameStatus && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-lg font-semibold text-blue-800">
              Oyun Durumu: {gameStatus === 'white_won' ? 'Beyaz Kazandı' : 
                           gameStatus === 'black_won' ? 'Siyah Kazandı' : 
                           gameStatus === 'draw' ? 'Berabere' : 'Devam Ediyor'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
