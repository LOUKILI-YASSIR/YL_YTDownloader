# Téléchargeur YouTube

Une application de bureau moderne pour télécharger des contenus YouTube avec des fonctionnalités avancées.

## Fonctionnalités

- Interface utilisateur moderne et intuitive
- Support multilingue (français par défaut)
- Mode clair/sombre
- Téléchargement de vidéos et d'audio
- Génération de transcriptions
- Tableau de bord avec statistiques
- Historique des téléchargements
- Gestion des utilisateurs

## Prérequis

- Python 3.8 ou supérieur
- MongoDB (exécuté localement sur le port 27017)
- Connexion Internet

## Installation

1. Clonez le dépôt :
```bash
git clone [url-du-depot]
cd [nom-du-dossier]
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Assurez-vous que MongoDB est en cours d'exécution sur le port par défaut (27017)

4. Lancez l'application :
```bash
python main.py
```

## Utilisation

1. Créez un compte ou connectez-vous
2. Collez l'URL YouTube dans le champ prévu
3. Sélectionnez le type de contenu (Vidéo, Audio, Transcription)
4. Choisissez le format et la qualité souhaités
5. Cliquez sur "Télécharger"

## Fonctionnalités détaillées

### Types de contenu
- **Vidéo** : MP4, WEBM, MKV, AVI
- **Audio** : MP3, WAV, AAC, M4A, OPUS
- **Transcription** : PDF, DOCX

### Tableau de bord
- Statistiques de téléchargement par jour
- Répartition des types de contenu
- Historique complet des téléchargements

### Personnalisation
- Basculement entre mode clair et sombre
- Sélection du dossier de destination
- Interface redimensionnable

## Sécurité

- Authentification utilisateur
- Mots de passe cryptés
- Gestion des sessions

## Support

Pour toute question ou problème, veuillez créer une issue dans le dépôt du projet.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.