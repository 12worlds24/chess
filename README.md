# Santrac - Satranç Öğrenme Platformu

Chess.com benzeri modern bir satranç öğrenme platformu. Docker container yapısı ile kolay kurulum ve yönetim.

## Özellikler

- **Bot ile Oyun**: Farklı zorluk seviyelerinde Stockfish botu ile oyun oynayın
- **Puzzle Sistemi**: Günlük puzzle'lar ve zorluk seviyelerine göre bulmacalar
- **Öğrenme Materyalleri**: Açılış teorisi, taktik örnekleri ve oyun analizi
- **Modern UI**: React + TypeScript ile responsive ve modern arayüz
- **Güvenli ve Güvenilir**: Detaylı log mekanizması, error recovery, retry mekanizmaları
- **Performans İzleme**: Real-time memory ve CPU monitoring, leak detection

## Teknoloji Stack

- **Backend**: Python FastAPI, PostgreSQL, Stockfish
- **Frontend**: React, TypeScript, Tailwind CSS
- **Container**: Docker, Docker Compose
- **Satranç Motoru**: Stockfish

## Kurulum

### Gereksinimler

- Docker ve Docker Compose
- En az 4GB RAM
- 10GB disk alanı

### Hızlı Başlangıç

1. Projeyi klonlayın:
```bash
git clone https://github.com/YOUR_USERNAME/Santrac.git
cd Santrac
```

2. Backend config dosyasını düzenleyin (opsiyonel):
```bash
# backend/config.json dosyasını düzenleyin
# Özellikle database ve SMTP ayarlarını kontrol edin
```

3. Docker Compose ile başlatın:
```bash
docker-compose up -d
```

4. Servislerin hazır olmasını bekleyin:
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
# Tarayıcıda http://localhost:3000 adresini açın
```

## Yapılandırma

### Config.json

Ana yapılandırma dosyası `backend/config.json` içinde bulunur. Önemli ayarlar:

#### Database
```json
{
  "database": {
    "host": "postgres",
    "port": 5432,
    "database": "santrac",
    "username": "santrac_user",
    "password": "santrac_password",
    "connection_timeout": 30
  }
}
```

#### Logging
```json
{
  "logging": {
    "level": "INFO",  // DEBUG, INFO, WARN, ERROR
    "file_path": "./logs",
    "max_file_size_mb": 10,
    "backup_count": 5
  }
}
```

#### SMTP (Email Alarms)
```json
{
  "smtp": {
    "enabled": true,
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-password",
    "to_emails": ["admin@example.com"]
  }
}
```

#### Scheduler
```json
{
  "scheduler": {
    "enabled": true,
    "run_on_startup": true,
    "cron_expression": "0 */6 * * *"  // Her 6 saatte bir
  }
}
```

#### Chess Engine
```json
{
  "chess_engine": {
    "skill_level": 10,  // 0-20 arası
    "depth": 15,
    "time_limit_ms": 2000
  }
}
```

## Kullanım

### Oyun Oynama

1. Ana sayfada "Oyna" sekmesine gidin
2. "Yeni Oyun" butonuna tıklayın
3. Taşları sürükleyerek hamle yapın
4. Bot otomatik olarak hamle yapacaktır

### Puzzle Çözme

1. "Bulmaca" sekmesine gidin
2. Rastgele bir puzzle yüklenecektir
3. Doğru hamleyi yaparak puzzle'ı çözün
4. "Yeni Bulmaca" ile farklı puzzle'lar deneyin

### API Kullanımı

API dokümantasyonu: http://localhost:8000/docs

#### Oyun Başlatma
```bash
curl -X POST http://localhost:8000/api/games/ \
  -H "Content-Type: application/json" \
  -d '{"is_bot_game": true, "bot_difficulty": 10}'
```

#### Hamle Yapma
```bash
curl -X POST http://localhost:8000/api/games/move \
  -H "Content-Type: application/json" \
  -d '{"game_id": 1, "move": "e2e4"}'
```

## Yönetim

### Logları Görüntüleme

```bash
# Backend logları
docker logs santrac_backend

# Frontend logları
docker logs santrac_frontend

# PostgreSQL logları
docker logs santrac_postgres
```

### Veritabanı Yedekleme

```bash
# PostgreSQL backup
docker exec santrac_postgres pg_dump -U santrac_user santrac > backup.sql

# Restore
docker exec -i santrac_postgres psql -U santrac_user santrac < backup.sql
```

### Servisleri Yeniden Başlatma

```bash
# Tüm servisleri yeniden başlat
docker-compose restart

# Sadece backend
docker-compose restart backend
```

### Servisleri Durdurma

```bash
# Servisleri durdur (veriler korunur)
docker-compose stop

# Servisleri durdur ve container'ları sil
docker-compose down

# Volumes dahil her şeyi sil
docker-compose down -v
```

## Performans İzleme

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "status": "ok",
  "current": {
    "memory": {
      "rss_mb": 256.5,
      "percent": 12.3
    },
    "cpu": {
      "percent": 5.2,
      "cores": 4
    }
  },
  "averages": {
    "memory_mb": 250.0,
    "cpu_percent": 4.8
  }
}
```

## Güvenlik

- SQL injection koruması (ORM kullanımı)
- Input validation (Pydantic)
- CORS yapılandırması
- Secure connection strings
- Non-root container kullanıcıları

## Sorun Giderme

### Database Bağlantı Hatası

```bash
# PostgreSQL'in çalıştığını kontrol edin
docker ps | grep postgres

# Connection string'i kontrol edin
# backend/config.json dosyasındaki database ayarlarını kontrol edin
```

### Stockfish Bulunamadı

```bash
# Container içinde Stockfish'i kontrol edin
docker exec santrac_backend which stockfish

# Stockfish path'i config.json'da kontrol edin
```

### Port Çakışması

Eğer portlar kullanılıyorsa, `docker-compose.yml` dosyasındaki port mapping'leri değiştirin:

```yaml
ports:
  - "8001:8000"  # Backend için farklı port
  - "3001:80"    # Frontend için farklı port
```

## Geliştirme

### Backend Geliştirme

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Geliştirme

```bash
cd frontend
npm install
npm run dev
```

## Lisans

Bu proje özel bir projedir.

## Destek

Sorularınız için issue açabilir veya dokümantasyonu inceleyebilirsiniz.

