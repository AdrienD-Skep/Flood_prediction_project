# 🌊 Prévision des Risques d'Inondation
**Autheur** : [Adrien DOUCET]  
**Application** : [🔗 Lien Hugging Face](https://huggingface.co/spaces/AdrienD-Skep/Flood-prediction) 

## 🌍 Contexte
Ce projet vise à anticiper les risques d'inondation à l'échelle européenne en combinant données géospatiales et modèles prédictifs. Face à l'augmentation des événements climatiques extrêmes, cette solution intègre des données hydrologiques, topographiques et météorologiques pour une analyse multi-échelles.

## 🎯 Objectifs  
- Estimer le risque d'inondation pour les 7 jours à veniren Europe
- Classifier le type d'inondation (fluviale/côtière/éclair)  
- Cartographier dynamiquement les zones à risque

📁 **Notebooks/**  
*Jupyter Notebooks d'exploration*  
- `1 Geo coding` : Géocodage des régions et identification des côtes les plus proches  
  *(Localisation des régions via leurs noms + calcul de la distance côtière avec S3_regions_codes_and_names_v2021)*  
- `2 flood train data gathering` : Collecte des données d'entraînement  
  *(Utilisation de l'API Open-Meteo et des données GESLA pour construire le dataset d'entraînement)*  
- `3 flood data analysis` : Analyse exploratoire et visualisation  
  *(EDA - Analyse des tendances historiques et corrélations spatiales)*  
- `4 flood predict ml` : Modélisation prédictive  
  *(Entraînement de modèles ML pour prédire type/probabilité d'inondation)*  
- `5 region geometry` : Préparation des données géospatiales  
  *(Génération des polygones régionaux + calculs de proximité côtière avec GeoPandas/Shapely)*  
- `6 app test` : Validation de l'application  
  *(Tests d'intégration des prédictions dans l'interface Streamlit + debug)*
  
📁 **Streamlit app/**  
*Streamlit Application (Proof of Concept) | Application Streamlit (POC)*  
- `app.py` : Interface utilisateur interactive principale  
  *(Cartographie dynamique + affichage des prédictions en temps réel)*  
- `update_geo_data.py` : Mise à jour automatisée des données géospatiales  
  *(Récupération live via API Open-Meteo)*  

📄 **README.md**  
*Documentation du projet*  


## 📊 Analyse Comparative des Performances des Modèles (Prédiction du type d'inondations)

### 📋 Tableau Synthétique
| Modèle                | Accuracy | Macro F1 | Micro F1 | Temps d'entrainement | Adapté au Déploiement |
|-----------------------|----------|----------|----------|----------------------|-----------------------|
| XGBoost               | 98.14%   | 0.909    | 0.981    | 14.3 sec             | ✅ Optimal             |
| Random Forest         | 96.75%   | 0.837    | 0.968    | 50.2 sec             | ⚠️ Acceptable         |
| Régression Logistique | 93.93%   | 0.595    | 0.939    | 0.6 sec              | ❌ Non recommandé     |
| SVC                   | 94.51%   | 0.583    | 0.945    | 20.3 sec             | ❌ Non recommandé     |
| Réseau Dense          | 66.94%   | 0.320    | 0.669    | 24.3 sec             | ❌ Échec              |

### 🏆 Meilleur Modèle : XGBoost
**Performances Clés** :
Train score (f1_macro): 1.0
Accuracy: 0.9841389728096677
Macro F1 Score: 0.9318149621216436
Micro F1 Score: 0.9841389728096677
### Matrice de Confusion :
```python
 [[  28    0    6    0]  # Côtière
  [   0  150   60    0]  # Éclair
  [   0    2 3682    0]  # Fluviale
  [   1    0    5   38]] # Mixte
```
## 📈 Conclusion
Le modèle XGBoost démontre les meilleures performances globales avec 98.14% d'accuracy et un F1-macro de 0.909. Une attention particulière doit être portée sur la détection des inondations éclair (classe 1) où le recall reste perfectible.


## 📊 Analyse Comparative des Performances des Modèles (prédiction des risques d'inondation)

### 📋 Tableau Synthétique
| Modèle                | Accuracy | Macro F1 | Micro F1 | Temps d'entrainement | Adapté au Déploiement |
|-----------------------|----------|----------|----------|----------------------|-----------------------|
| XGBoost               | 98.76%   | 0.977    | 0.988    | 18.2 sec             | ✅ Optimal            |
| Random Forest         | 98.27%   | 0.967    | 0.983    | 341.2 sec            | ✅ Bon                |
| Régression Logistique | 89.36%   | 0.776    | 0.894    | 1 sec                | ⚠️ Acceptable         |
| SVC                   | 94.37%   | 0.889    | 0.944    | 1126.7 sec           | ⚠️ Acceptable         |
| Réseau Dense          | 83.42%   | 0.455    | 0.834    | 392.3 sec            | ❌ Échec              |

### 🏆 Meilleur Modèle : XGBoost
**Performances Clés** :
Train score: 0.992356721669623
Accuracy: 0.9876455611669936
Macro F1 Score: 0.9771949450269299
Micro F1 Score: 0.9876455611669936
### Matrice de Confusion :
```python
[[19941    46]  # pas d'inondation
 [  250  3722]] # inondation
```

## 📚 Sources de Données & Références

- **Données historiques européennes** :  
  [🌍 HANZE_events.csv](https://zenodo.org/records/11259233) - Historique des inondations en Europe
- **Données géospatiales** :  
  [🗺️ GADM](https://gadm.org/download_world.html) - Limites administratives mondiales
- **Données météorologiques** :  
  [⛅ Open-Meteo](https://open-meteo.com/) - API de prévisions météo historiques et temps réel
- **Niveaux marins extrêmes** :  
  [🌊 GESLA](https://gesla787883612.wordpress.com/downloads/) - Archive mondiale des niveaux marins exceptionnels

