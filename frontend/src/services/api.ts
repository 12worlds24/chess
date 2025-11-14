import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Game API
export const gameAPI = {
  create: (data: { white_player_id?: number; black_player_id?: number; is_bot_game: boolean; bot_difficulty?: number }) =>
    api.post('/api/games/', data),
  
  get: (gameId: number) =>
    api.get(`/api/games/${gameId}`),
  
  getSession: (gameId: number) =>
    api.get(`/api/games/${gameId}/session`),
  
  makeMove: (data: { game_id: number; move: string; player_id?: number }) =>
    api.post('/api/games/move', data),
  
  analyze: (gameId: number, depth?: number) =>
    api.post(`/api/games/${gameId}/analyze`, { depth }),
  
  suggestMove: (gameId: number) =>
    api.post(`/api/games/${gameId}/suggest-move`),
  
  undoMove: (gameId: number, numMoves?: number) =>
    api.post(`/api/games/${gameId}/undo?num_moves=${numMoves || 1}`),
};

// Puzzle API
export const puzzleAPI = {
  getRandom: (difficulty?: string) =>
    api.get('/api/puzzles/random', { params: { difficulty } }),
  
  get: (puzzleId: number) =>
    api.get(`/api/puzzles/${puzzleId}`),
  
  attempt: (data: { puzzle_id: number; move: string; user_id?: number }) =>
    api.post('/api/puzzles/attempt', data),
  
  getStats: (userId: number) =>
    api.get(`/api/puzzles/stats/${userId}`),
};

export default api;

