# YouTube Downloader Pro

Une application moderne et complète pour télécharger des vidéos YouTube et autres plateformes, avec gestion des utilisateurs, sécurité renforcée et interface graphique intuitive.

## Fonctionnalités principales

### Authentification & Sécurité
- Authentification sécurisée des utilisateurs (bcrypt)
- Gestion des comptes utilisateurs (inscription, connexion, mot de passe oublié)
- Option "Se souvenir de moi"
- Interface moderne avec gestion du thème (clair/sombre)

### Téléchargement de vidéos et audio
- Prise en charge de YouTube, Vimeo, Dailymotion
- Choix du format vidéo (mp4, webm, mkv)
- Extraction audio (mp3, wav, m4a, ogg)
- Sélection de la qualité (1080p, 720p, 480p, 360p)
- Téléchargement de playlists
- Gestion de la file d'attente et suivi de la progression
- Historique des téléchargements

### Tableau de bord et statistiques
- Visualisation des statistiques de téléchargement
- Historique avec recherche et filtres
- Exportation des données (PDF, CSV)

### Profil utilisateur
- Gestion du profil et des préférences
- Paramètres de sécurité
- Gestion des chemins de téléchargement

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/yourusername/youtube-downloader-pro.git
cd youtube-downloader-pro
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
venv\Scripts\activate  # Sous Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez la base de données MongoDB (locale par défaut, modifiable dans le code).

5. Vérifiez que FFmpeg est installé et accessible dans le PATH système.
   - Téléchargez FFmpeg : https://ffmpeg.org/download.html
   - Ajoutez le dossier \bin de FFmpeg à la variable d'environnement PATH.

6. (Windows uniquement) Pour Pillow, installez Visual Studio Build Tools si nécessaire :
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

7. Lancez l'application :
```bash
python main.py
```

L'interface graphique s'ouvrira automatiquement.

## Configuration

La configuration s'effectue principalement dans le code source (main.py) et via les variables d'environnement :
- Connexion MongoDB locale par défaut (modifiable dans main.py)
- Dossiers de téléchargement créés automatiquement (./video, ./audio)
- Thème et préférences utilisateur gérés dans l'interface

## Prérequis

- Python 3.8 ou supérieur
- MongoDB 4.4 ou supérieur (local ou distant)
- FFmpeg (pour l'extraction audio)
- Visual Studio Build Tools (Windows uniquement, pour Pillow)
- Connexion Internet

## Dépendances principales

- customtkinter : Interface graphique moderne
- pymongo : Connexion à MongoDB
- bcrypt : Hachage des mots de passe
- yt-dlp : Téléchargement de vidéos
- Pillow : Gestion des images
- requests : Requêtes HTTP
- pandas : Manipulation de données
- reportlab : Génération de PDF
- matplotlib : Visualisation de données
- ffmpeg-python : Intégration FFmpeg

## Sécurité

- Les mots de passe sont hachés avec bcrypt
- Les données utilisateurs sont stockées dans MongoDB
- Les sessions sont sécurisées
- Les chemins de téléchargement sont isolés par utilisateur

## Contribution

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité
3. Commitez vos modifications
4. Poussez la branche
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Support

Pour toute question ou problème, ouvrez une issue sur le dépôt GitHub ou contactez les mainteneurs.

## Remerciements

- Équipe yt-dlp pour la bibliothèque de téléchargement
- Équipe CustomTkinter pour le framework GUI
- Tous les contributeurs et utilisateurs du projet
