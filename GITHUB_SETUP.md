# GitHub'a Yükleme Talimatları

## 1. GitHub'da Repository Oluşturun

1. https://github.com/new adresine gidin
2. Repository adı: `Santrac`
3. Public veya Private seçin
4. "Initialize this repository with a README" seçeneğini işaretlemeyin
5. "Create repository" butonuna tıklayın

## 2. Remote Ekleme ve Push

GitHub'da repository oluşturduktan sonra, GitHub'ın gösterdiği URL'yi kullanarak:

```bash
# Remote ekle (YOUR_USERNAME'i kendi GitHub kullanıcı adınızla değiştirin)
git remote add origin https://github.com/YOUR_USERNAME/Santrac.git

# Branch adını main olarak ayarla
git branch -M main

# GitHub'a push et
git push -u origin main
```

## Alternatif: SSH Kullanıyorsanız

```bash
git remote add origin git@github.com:YOUR_USERNAME/Santrac.git
git branch -M main
git push -u origin main
```

## Sonraki Adımlar

Repository'yi oluşturduktan sonra bana URL'yi verin, ben de remote'u ekleyip push edebilirim.

