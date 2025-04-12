# 🌊 Prévision des Risques d'Inondation
**Autheur** : [Adrien DOUCET](https://github.com/AdrienD-Skep)

**Application** : 🔗 [Hugging Face](https://huggingface.co/spaces/AdrienD-Skep/Flood-prediction) 

## 📑 Sommaire
- [🔍 Vision du Projet](#-vision-du-projet)
- [🎯 Objectifs](#-objectifs)
- [🗃 Structure du Projet](#-structure-du-projet)
- [📊 Performances des Modèles](#-analyse-comparative-des-performances-des-modèles)
- [📈 Exemple de Résultat](#-exemple-de-résultat)
- [📚 Sources](#-sources-de-données--références)

## 🔍 Vision du Projet
Ce projet vise à développer une solution intelligente de surveillance et de prévision des inondations à l’échelle européenne.
En croisant des données géospatiales, météorologiques et hydrologiques, il permet d’identifier en temps réel les zones à risque. Grâce à des modèles de machine learning, cette approche permet d’anticiper les inondations sur 7 jours, tout en classifiant leur nature (fluviale, côtière ou éclair) avec une granularité régionale.
Une réponse innovante face à l’intensification des aléas climatiques.

## 🎯 Objectifs  
- Estimer le risque d'inondation pour les 7 jours à venir en Europe
- Classifier le type d'inondation (fluviale/côtière/éclair)  
- Cartographier dynamiquement les zones à risque


## 🗃 Structure du Projet
📁 **Notebooks/**  
*Jupyter Notebooks d'exploration*  
- `1 Geo coding` : Géocodage des régions et identification des côtes les plus proches  
  *(Localisation des régions via leurs noms + calcul de la distance côtière)*  
- `2 flood train data gathering` : Collecte des données d'entraînement  
  *(Utilisation de l'API Open-Meteo et des données GESLA pour construire le dataset d'entraînement)*  
- `3 flood data analysis` : Analyse exploratoire et visualisation  
  *(EDA - Analyse des tendances historiques et corrélations)*  
- `4 flood predict ml` : Modélisation prédictive  
  *(Entraînement de modèles ML pour prédire type/probabilité d'inondation)*  
- `5 region geometry` : Préparation des données géospatiales  
  *(Génération des polygones régionaux + calculs de proximité côtière avec GeoPandas/Shapely)*  
- `6 app test` : Validation de l'application  
  *(Tests d'intégration des prédictions dans l'interface Streamlit + debug)*

📁 **Streamlit app/**  
*Application Streamlit*  
- `app.py` : Interface principale de visualisation  
  *(Affichage interactif des prédictions sur une carte en temps réel)*  
- `Dockerfile` : Conteneurisation de l’application  
  *(Initialisation de l’image Docker pour déployer l’application Streamlit)*  
- `requirement.txt` : Liste des dépendances nécessaires à l’application  

📁 **Update_geo_script/**  
*Workflow de mise à jour automatisée des données géospatiales*  
- 📁 `models`  
  - `model_XGBC_flood_type.pkl` : Modèle de prédiction du type d’inondation  
  - `model_XGBC_predict_flood.pkl` : Modèle de prédiction des probabilités d’inondation  
- `requirement.txt` : Liste des dépendances nécessaires au script  
- `update_geo_data.py` : Script de collecte et mise à jour des données  
  *(Appels aux APIs, prédictions via modèles ML, sauvegarde des données)* 

## 📊 Analyse Comparative des Performances des Modèles
## Prédiction du type d'inondations

### 📋 Tableau Synthétique
| Modèle                | Accuracy | Macro F1 | Micro F1 | Temps d'entrainement | Adapté au Déploiement |
|-----------------------|----------|----------|----------|----------------------|-----------------------|
| XGBoost               | 98.67%   | 0.942    | 0.987    | 6.4 sec              | 🏆 Optimal            |
| Random Forest         | 97.68%   | 0.912    | 0.977    | 46.3 sec             | ✅ Bon                |
| SVC                   | 94.51%   | 0.794    | 0.945    | 16.8 sec             | ⚠️ Acceptable         |
| Régression Logistique | 93.93%   | 0.595    | 0.939    | 6.8 sec              | ❌ Non recommandé     |
| Réseau Dense          | 90.96%   | 0.437    | 0.910    | 53.8 sec             | ❌ Échec              |

### 🏆 Meilleur Modèle : XGBoost

Le meilleur dataset pour XGBC est RandomOverSampler  
Performance après une optimisation par bayes search pour ajuster les hyperparamètres :

**Performances Clés** :
- Train score : 1.0 (parfait)
- Accuracy : 0.986404833836858
- Macro F1 Score : 0.9496588924077598
- Micro F1 Score : 0.986404833836858

### Matrice de Confusion :
```python
[[  30    0    4    0]  # Côtière
 [   0  165   45    0]  # Éclair
 [   0    5 3679    0]  # Fluviale
 [   0    0    0   44]] # Mixte
```
## 📈 Conclusion
Le modèle XGBoost démontre les meilleures performances globales avec 98.64% d'accuracy et un F1-macro de 0.945. Le recall pour la détection des inondations éclair (classe 1) reste perfectible.


## Prédiction des risques d'inondation

### 📋 Tableau Synthétique
| Modèle                | Accuracy | Macro F1 | Micro F1 | Temps d'entrainement | Adapté au Déploiement |
|-----------------------|----------|----------|----------|----------------------|-----------------------|
| XGBoost               | 98.80%   | 0.978    | 0.988    | 5.1 sec              | 🏆 Optimal            |
| Random Forest         | 98.94%   | 0.980    | 0.989    | 123.5 sec            | ✅ Bon                |
| Régression Logistique | 89.45%   | 0.779    | 0.894    | 5.9 sec              | ⚠️ Acceptable         |

### 🏆 Meilleur Modèle : XGBoost

Le meilleur dataset pour XGBC est RandomOverSampler  
Performance après une optimisation par bayes search pour ajuster les hyperparamètres :

**Performances Clés** :
- Train score (neg_brier_score): -6.779782903658843e-07
- Accuracy: 0.9964105346633833
- Macro F1 Score: 0.9934704984747424
- Micro F1 Score: 0.9964105346633833
- brier score 0.002922775998140172
- log loss 0.011802703210718319
- roc auc 0.9996356770873878
- pr auc 0.9988404582809471
### Matrice de Confusion :
```python
 [[19975    12] # pas d'inondation
 [   74  3898]] # inondation
 # threshold = 0.1 :
 [[19922    65] # pas d'inondation
 [   33  3939]] # inondation
```
## 📈 Conclusion
Le modèle Random Forest offrait de meilleures performances sans optimisation des hyperparamètres, mais XGBoost le surpasse après une légère recherche bayésienne. De plus, étant beaucoup plus rapide, XGBoost est mieux adapté pour effectuer une recherche bayésienne complète.

## 🔍 Exemple de Résultat
Voici un aperçu de l'application :
![aperçu de l'app](assets/Streamlit_app.jpeg)


## 📚 Sources de Données & Références

- **Données historiques européennes** :  
  [🌍 HANZE_events.csv](https://zenodo.org/records/11259233) - Historique des inondations en Europe
- **Données géospatiales** :  
  [🗺️ GADM](https://gadm.org/download_world.html) - Limites administratives mondiales
- **Données météorologiques** :  
  [⛅ Open-Meteo](https://open-meteo.com/) - API de prévisions météo historiques et temps réel
- **Niveaux marins extrêmes** :  
  [🌊 GESLA](https://gesla787883612.wordpress.com/downloads/) - Archive mondiale des niveaux marins exceptionnels

