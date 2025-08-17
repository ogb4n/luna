# Système de Vocalisation Aléatoire de Luna

## 📋 Vue d'ensemble

Luna peut maintenant parler de manière aléatoire en utilisant des fichiers audio préenregistrés. Cette fonctionnalité permet à Luna de sembler plus vivante et interactive dans les canaux vocaux.

## 🎵 Configuration

### 1. Préparation des fichiers audio

1. Créez vos fichiers audio (conversations, phrases, sons, etc.)
2. Placez-les dans le dossier `voicefiles/` 
3. Formats supportés : `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`

Exemple de structure :
```
voicefiles/
├── salut.mp3
├── comment_ca_va.wav
├── rire.ogg
├── conversation1.mp3
└── phrase_random.wav
```

### 2. Configuration des intervalles

Par défaut, Luna parlera aléatoirement toutes les 1 à 10 minutes. Vous pouvez changer cela avec :

```
!vocalise_interval <min_minutes> <max_minutes>
```

Exemples :
- `!vocalise_interval 2 5` - Entre 2 et 5 minutes
- `!vocalise_interval 1 15` - Entre 1 et 15 minutes
- `!vocalise_interval 5 5` - Exactement toutes les 5 minutes

## 🎯 Commandes

### Contrôle principal
- `!vocalise` ou `!vocalize` - Active/désactive la vocalisation aléatoire
- `!vocalise_interval <min> <max>` - Configure l'intervalle de temps

### Statut
- `!status` - Affiche l'état de tous les systèmes, y compris la vocalisation

## 🔧 Fonctionnement

1. **Démarrage automatique** : La vocalisation se lance automatiquement au démarrage de Luna
2. **Condition de fonctionnement** : Ne fonctionne que quand Luna est connectée à un canal vocal
3. **Sélection aléatoire** : Un fichier audio est choisi au hasard dans le dossier `voicefiles/`
4. **Timing aléatoire** : Le délai entre chaque vocalisation est aléatoire dans l'intervalle configuré
5. **Interruption intelligente** : Si Luna est déjà en train de jouer un audio, elle arrête le précédent avant de jouer le nouveau

## ⚠️ Notes importantes

- La vocalisation ne fonctionne que quand Luna est connectée en vocal
- Les fichiers corrompus ou non-audio seront ignorés
- Le dossier `voicefiles/` doit exister (créé automatiquement)
- La vocalisation continue même en mode autonome
- Vous pouvez activer/désactiver à tout moment sans redémarrer Luna

## 🎭 Conseils d'utilisation

### Types de contenu recommandés :
- **Phrases courtes** : "Salut !", "Comment ça va ?", "Ça va bien ?"
- **Réactions** : Rires, soupirs, exclamations
- **Conversations naturelles** : Extraits de vraies conversations
- **Variété** : Mélangez différents types pour plus de réalisme

### Évitez :
- Fichiers trop longs (plus de 30 secondes)
- Contenu répétitif
- Mauvaise qualité audio
- Contenu inapproprié

## 📊 Monitoring

Utilisez `!status` pour voir :
- Si la vocalisation est active
- Combien de fichiers audio sont disponibles
- L'intervalle configuré
- Si Luna est connectée en vocal

## 🛠️ Dépannage

**Luna ne vocalise pas ?**
1. Vérifiez qu'elle est connectée en vocal (`!status`)
2. Vérifiez que des fichiers existent dans `voicefiles/`
3. Vérifiez que la vocalisation est active (`!vocalise`)

**Erreurs de lecture ?**
- Vérifiez le format des fichiers audio
- Assurez-vous que FFmpeg est installé
- Vérifiez les permissions du dossier `voicefiles/`

Cette fonctionnalité rend Luna beaucoup plus vivante et réaliste dans les interactions vocales ! 🎉
