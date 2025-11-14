<!-- 56797281-c3b5-4427-8660-cabb438b8c4f 4e357187-9616-40e9-9416-7c82e97bf9c1 -->
# Santrac Öğrenme Platformu - Geliştirme Planı

## Mimari Yapı

### Container Yapısı (Docker Compose)

- **backend**: Python FastAPI servisi (satranç motoru, oyun mantığı, API)
- **frontend**: React uygulaması (Chess.com benzeri UI)
- **database**: PostgreSQL (oyun geçmişi, kullanıcı verileri, puzzle'lar)
- **nginx**: Reverse proxy (opsiyonel, production için)

### Teknoloji Stack

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI + python-chess + Stockfish
- **Database**: PostgreSQL
- **Satranç Motoru**: Stockfish (bot oyunları için)

## Temel Özellikler

### 1. Oyun Özellikleri

- Bot ile oyun (farklı zorluk seviyeleri)
- İki oyuncu arasında oyun
- Oyun geçmişi kaydetme ve analiz
- Oyun sırasında hamle önerileri

### 2. Puzzle Sistemi

- Günlük puzzle'lar
- Zorluk seviyelerine göre puzzle'lar
- Puzzle çözme istatistikleri

### 3. Öğrenme Materyalleri

- Açılış teorisi
- Taktik örnekleri
- Oyun analizi araçları

## Backend Yapısı (Python FastAPI)

### Proje Yapısı

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI uygulaması
│   ├── config.py               # Config yönetimi
│   ├── database.py             # DB bağlantı ve modeller
│   ├── models/                 # SQLAlchemy modelleri
│   ├── schemas/                 # Pydantic şemaları
│   ├── api/                     # API endpoint'leri
│   │   ├── games.py
│   │   ├── puzzles.py
│   │   ├── users.py
│   │   └── analysis.py
│   ├── services/                # İş mantığı
│   │   ├── chess_engine.py     # Stockfish entegrasyonu
│   │   ├── game_service.py
│   │   ├── puzzle_service.py
│   │   └── scheduler.py         # Schedule yönetimi
│   ├── utils/
│   │   ├── logger.py            # Log mekanizması
│   │   ├── retry.py             # Retry mekanizması
│   │   ├── lock.py              # Lock mekanizması
│   │   ├── email.py             # Mail gönderimi
│   │   ├── recovery.py          # Error recovery
│   │   └── metrics.py           # Performans metrikleri
│   └── workers/                 # Background işler
├── config.json                  # Ana konfigürasyon
├── requirements.txt
└── Dockerfile
```

### Config.json Yapısı

- Database bağlantı bilgileri
- Log seviyesi (DEBUG, INFO, WARN, ERROR)
- Retry ayarları (sayı, süre)
- Schedule ayarları (cron formatı)
- SMTP ayarları (alarm mailleri için)
- Connection timeout
- Thread/CPU/RAM limitleri
- Log dosyası ayarları (max size, retention)

### Önemli Özellikler

- **Log Mekanizması**: Seviye bazlı logging, dosyaya yazma, zip backup
- **Retry Mekanizması**: Tüm kritik işlemler için configurable retry
- **Lock Mekanizması**: Schedule işleri için lock (çakışma önleme)
- **Error Recovery**: DB, file system, network recovery stratejileri
- **Performans Metrikleri**: Memory monitoring, CPU tracking, leak detection
- **Alarm Sistemi**: Kritik hatalar için email bildirimi

## Frontend Yapısı (React)

### Proje Yapısı

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChessBoard/          # Satranç tahtası
│   │   ├── GameControls/        # Oyun kontrolleri
│   │   ├── PuzzleView/          # Puzzle görünümü
│   │   ├── Learning/            # Öğrenme materyalleri
│   │   └── Navigation/          # Menü/navigasyon
│   ├── pages/
│   │   ├── PlayPage.tsx
│   │   ├── PuzzlePage.tsx
│   │   ├── LearnPage.tsx
│   │   └── AnalysisPage.tsx
│   ├── services/
│   │   └── api.ts               # Backend API çağrıları
│   ├── hooks/
│   ├── utils/
│   └── App.tsx
├── package.json
└── Dockerfile
```

### UI Özellikleri

- Modern, Chess.com benzeri tasarım
- Responsive layout
- Koyu/açık tema desteği
- Hamle animasyonları
- Gerçek zamanlı oyun durumu

## Database Şeması

### Tablolar

- **users**: Kullanıcı bilgileri
- **games**: Oyun kayıtları (PGN formatında)
- **puzzles**: Puzzle'lar ve çözümler
- **user_puzzles**: Kullanıcı puzzle çözüm istatistikleri
- **sessions**: Aktif oyun oturumları

## Docker Yapılandırması

### docker-compose.yml

- Backend, frontend, database servisleri
- Volume mount'lar (config, logs)
- Network yapılandırması
- Environment variables

### Dockerfile'lar

- Multi-stage build (optimizasyon için)
- Güvenlik best practices
- Minimal image boyutu

## Güvenlik

- SQL injection koruması (ORM kullanımı)
- Input validation (Pydantic)
- CORS yapılandırması
- Rate limiting
- Secure connection strings

## Deployment

- docker-compose ile kolay kurulum
- Environment-based configuration
- Health check endpoints
- Log aggregation

### To-dos

- [ ] Proje klasör yapısını oluştur (backend, frontend, docker dosyaları)
- [ ] Backend config.json yapısını ve config.py modülünü oluştur (log, retry, schedule, SMTP, DB ayarları)
- [ ] Detaylı log mekanizması (logger.py) - seviye bazlı, dosyaya yazma, zip backup
- [ ] PostgreSQL bağlantısı, SQLAlchemy modelleri ve database.py oluştur
- [ ] Retry ve lock mekanizmalarını implement et (retry.py, lock.py)
- [ ] Stockfish entegrasyonu ve chess_engine.py servisi oluştur
- [ ] Oyun API endpoint'lerini oluştur (games.py) - başlat, hamle yap, bitir
- [ ] Puzzle API endpoint'lerini oluştur (puzzles.py)
- [ ] Schedule mekanizması (scheduler.py) - ilk başta çalış, sonra schedule takip et
- [ ] Error recovery stratejileri ve performans metrikleri (recovery.py, metrics.py)
- [ ] Email alarm sistemi (email.py) - SMTP ile kritik hata bildirimleri
- [ ] FastAPI main.py - tüm endpoint'leri bağla, middleware'ler, CORS
- [ ] React projesi kurulumu, TypeScript, Tailwind CSS yapılandırması
- [ ] Satranç tahtası komponenti (ChessBoard) - hamle yapma, görselleştirme
- [ ] Backend API entegrasyonu (api.ts) - axios ile HTTP çağrıları
- [ ] Ana sayfalar (Play, Puzzle, Learn, Analysis) ve routing
- [ ] UI iyileştirmeleri - tema, animasyonlar, responsive design
- [ ] Backend Dockerfile oluştur - Python, Stockfish, dependencies
- [ ] Frontend Dockerfile oluştur - React build, nginx serve
- [ ] docker-compose.yml - tüm servisleri bağla, network, volumes
- [ ] README.md - kurulum, kullanım, config açıklamaları