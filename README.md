<div align="center">

<img src="web/public/logo.png" width="150" alt="GREEN SHIELD Logo">

# 🟢 GREEN SHIELD

**Plateforme d'audit cyber & GRC assistée par IA — L'outil de consulting augmenté.**

Un environnement d'audit moderne, hors-ligne et modulaire, conçu pour guider les missions de cybersécurité de A à Z avec un haut niveau d'assistance métier.

![React](https://img.shields.io/badge/React-19-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688)
![AI Automation](https://img.shields.io/badge/AI_Agents-MCP-8A2BE2)
![No Code](https://img.shields.io/badge/Build-No_Code-success)

</div>

---

## 📸 Aperçu de la Plateforme (POC)

*(Note: Ajoutez vos captures d'écran dans le dossier docs/screens/ et décommentez les lignes ci-dessous pour les afficher)*

<!--
<p align="center">
  <img src="docs/screens/dashboard.png" width="800" alt="Dashboard et Carte Neurale">
  <br>
  <em>Vue principale avec la Carte Neurale et la progression de mission.</em>
</p>
<p align="center">
  <img src="docs/screens/voice_ai.png" width="400" alt="IA Vocale">
  <img src="docs/screens/copilot.png" width="400" alt="Créateur de Copilote">
  <br>
  <em>IA Vocale (avec masquage RGPD) et Créateur de Copilote sur-mesure.</em>
</p>
-->

---

## 📖 Pourquoi GREEN SHIELD ? (Genèse du projet)

À l'aube d'un stage en consulting cybersécurité pour une association, j'ai ressenti le besoin de structurer mon approche. La sécurité de l'information est un enjeu critique où **rien ne doit être laissé au hasard**. 

Pour pallier le manque d'expérience inhérent à tout début de carrière, j'ai voulu me doter d'un outil extrêmement guidé, capable d'anticiper les oublis et de rattraper d'éventuelles erreurs. Je me suis largement inspiré des leaders du marché comme **Vanta** ou **CISO Assistant**, mais avec un objectif différent : créer un assistant de consulting **plus directif, plus pédagogique**, qui prend l'auditeur par la main de la phase de cadrage jusqu'à la restitution au Comex.

### L'alliance de la GRC et de l'Intelligence Artificielle
Ce projet est l'aboutissement d'un travail d'ingénierie hybride. Il a été **entièrement développé en "no-code"**, en orchestrant des agents IA via le protocole **MCP (Model Context Protocol)**. En combinant mon expertise des référentiels GRC et ma maîtrise du *Prompt Engineering* et de l'automatisation IA, GREEN SHIELD démontre comment l'IA peut être mise au service d'une méthodologie d'audit rigoureuse.

---

## 🛡️ "Security By Design" : La sécurité au cœur de l'architecture

En cybersécurité, les outils que nous utilisons ne doivent pas devenir le maillon faible. La gestion des données sensibles (architectures clients, vulnérabilités) exige des garanties absolues que les outils SaaS classiques peinent parfois à offrir. **GREEN SHIELD a été conçu autour du principe du Zero Trust.**

- **🔒 100% Local & Modèles Hors-Ligne** : L'application fonctionne intégralement en local (127.0.0.1). Vous avez la possibilité de brancher des modèles LLM **totalement hors-ligne** (Ollama, LM Studio). Aucune donnée ne quitte votre machine.
- **🔑 Sécurité absolue des clés API** : La compromission d'une clé API est une faute rédhibitoire. Si vous utilisez une API tierce (OpenAI, Gemini), **votre clé n'est jamais transmise au backend ni sauvegardée en base de données**. Elle est chiffrée et stockée de manière éphémère dans le localStorage de votre navigateur.
- **🤫 Filtre RGPD & Masquage (Data Leak Prevention)** : L'IA vocale (transcription d'entretiens) intègre un moteur de Regex puissant. Il détecte et **masque à la volée** toutes les données sensibles (noms, emails, numéros de sécurité sociale, téléphones) *avant* même qu'elles ne soient analysées par l'IA. Fini le risque de fuite de données personnelles dans les prompts !
- **🔐 Protection des données au repos** : L'architecture impose un environnement maîtrisé. Les missions sont stockées dans des fichiers JSON, nécessitant un chiffrement de disque (BitLocker / LUKS) pour être exploitées de façon professionnelle. De plus, chaque action sensible est tracée dans un udit.log strict.

---

## 🎯 Fonctionnalités Clés de l'Assistant

- **🎙️ IA Vocale Intégrée** : Dictez vos constats d'audit ou enregistrez des entretiens. L'IA retranscrit, analyse et classe l'information automatiquement, tout en caviardant les données personnelles.
- **🧠 Créateur de Copilote IA Sur Mesure** : La plateforme intègre un "Assistant Création". Configurez l'IA pour adopter des "Personas" spécifiques (ex: RSSI de transition, Auditeur ISO 27001 intraitable) afin de vous assister précisément sur vos points faibles.
- **📄 Exports Universels Multi-Formats (PDF / Word / Markdown)** : L'outil génère automatiquement vos livrables (NDA, Déclaration d'Applicabilité, PIA/AIPD, Synthèse Comex) au format Word ou en **PDF d'une qualité d'impression irréprochable**, directement par le navigateur pour garantir une mise en page parfaite.
- **🛤️ Conduite de mission guidée (6 phases)** : Cadrage & Patrimoine, Diagnostic (ISO 27001, NIS2, DORA...), Gestion des Risques Tiers (TPRM), Analyse des Menaces (EBIOS RM), Résilience (E3R/BCP) et Plan de traitement.

---

## 🛠️ Savoir-faire Normatif mis en œuvre

1. **Gouvernance, Risques et Conformité (GRC)** :
   - Implémentation fonctionnelle des normes : **ISO/IEC 27001:2022, DORA, NIS2, RGPD, NIST CSF 2.0**.
   - Méthodologie d'analyse de risques basée sur **EBIOS RM**.
   - Suivi d'impact sur la vie privée via **AIPD (PIA)**.
   - Notation des tiers fournisseurs via ratio **ANSSI**.
2. **IA & Développement Moderne** :
   - Conception dirigée par l'IA (AI Automation, Agents, MCP).
   - Architecture découplée : Frontend moderne (React 19, Tailwind) et moteur d'audit backend (FastAPI, Python).

---

## 🚀 Installation & Démarrage

`ash
# Lancement rapide via Docker
make up          # construit et lance l'app sur http://localhost:8080
`
> Sans make (Windows) : docker compose up --build -d.

### Pour les curieux (Voir le rendu sans installer)
Consultez le dossier **[docs/exemples/](docs/exemples/)**. Vous y trouverez les livrables bruts de deux missions fictives (Conseil et Conformité) générés de bout en bout par l'outil.

---

## ⚖️ Licence & Usage

[PolyForm Noncommercial 1.0.0](LICENSE.md). 
Ce projet est partagé en open source pour contribuer à la communauté cyber et démontrer mon approche du métier. 
- ✅ Lecture, étude, modification, usage associatif ou enseignement.
- ❌ Revente, intégration commerciale ou utilisation en SaaS payant.

*GREEN SHIELD — Un projet conçu avec passion à l'intersection de la Cybersécurité et de l'IA.*
