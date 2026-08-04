<div align="center">

<img src="web/public/logo.png" width="150" alt="GREEN SHIELD Logo">

# 🟢 GREEN SHIELD

**Cockpit de conduite de mission pour consultant cybersécurité — 100 % local.**

Un environnement d'audit moderne, hors-ligne et modulaire, qui guide une mission GRC de la phase de cadrage jusqu'à la restitution au Comex.

![React](https://img.shields.io/badge/React-19-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688)
![Tests](https://img.shields.io/badge/tests-624%20back%20%2F%20150%20front-success)
![Licence](https://img.shields.io/badge/licence-PolyForm%20Noncommercial-lightgrey)

</div>

---

## 📸 Aperçu de la plateforme

<p align="center">
  <img src="docs/assets/demo_sql.webp" width="820" alt="Démonstration de la navigation dans GREEN SHIELD">
  <br>
  <em>Navigation et sauvegarde d'une mission.</em>
</p>

Les captures ci-dessous proviennent de la **mission de démonstration** livrée avec l'outil — entièrement fictive, générée en un clic, et régénérable par [`scripts/captures_readme.py`](scripts/captures_readme.py).

<p align="center">
  <img src="docs/assets/01-registre-missions.png" width="820" alt="Registre des missions avec la frise des remédiations sur trois horizons">
  <br>
  <em><strong>Registre des missions.</strong> Frise des remédiations consolidée sur trois horizons (court / moyen / long terme), toutes missions confondues, avec charges consommées et complétion moyenne.</em>
</p>

<p align="center">
  <img src="docs/assets/04-multi-referentiel.png" width="820" alt="Check-lists d'audit ISO 27001 et DORA sur une même mission">
  <br>
  <em><strong>Multi-référentiel.</strong> Une même mission porte ISO 27001 <em>et</em> DORA : chaque check-list est regroupée par référentiel, et les livrables indiquent l'origine de chaque contrôle.</em>
</p>

<p align="center">
  <img src="docs/assets/05-soa.png" width="820" alt="Bibliothèque de preuves et Déclaration d'Applicabilité">
  <br>
  <em><strong>Preuves et Déclaration d'Applicabilité.</strong> Une preuve peut couvrir des contrôles de plusieurs référentiels à la fois. En dessous, les 93 contrôles de l'Annexe A avec leur justification d'inclusion ou d'exclusion.</em>
</p>

<p align="center">
  <img src="docs/assets/03-phase2-violations.png" width="820" alt="Registre des violations de données personnelles">
  <br>
  <em><strong>Registre des violations (RGPD Art. 33-34).</strong> Toute violation se documente, même jugée non notifiable. Le délai de 72 h est contrôlé avant l'export.</em>
</p>

<p align="center">
  <img src="docs/assets/06-phase6-livrables.png" width="820" alt="Revue avant export et génération des livrables">
  <br>
  <em><strong>Revue avant export et livrables.</strong> L'outil énumère ce qui manque avant qu'un document ne parte chez le client, puis génère les six livrables en Word, PDF et Markdown.</em>
</p>

> **Envie de voir le résultat sans rien installer ?** Le dossier **[docs/exemples/](docs/exemples/)** contient les livrables bruts de deux missions fictives, générés de bout en bout par l'outil (Word, HTML, Markdown).

---

## 📖 Pourquoi GREEN SHIELD ? (Genèse du projet)

À l'aube d'un stage en consulting cybersécurité pour une association, j'ai ressenti le besoin de structurer mon approche. La sécurité de l'information est un enjeu critique où **rien ne doit être laissé au hasard**.

Pour pallier le manque d'expérience inhérent à tout début de carrière, j'ai voulu me doter d'un outil extrêmement guidé, capable d'anticiper les oublis et de rattraper d'éventuelles erreurs. Je me suis largement inspiré des leaders du marché comme **Vanta** ou **CISO Assistant**, mais avec un objectif différent : créer un assistant de consulting **plus directif, plus pédagogique**, qui prend l'auditeur par la main.

### Une règle qui structure tout le produit : zéro invention

Un outil d'audit qui « comble les trous » est un outil dangereux : il fait signer au consultant des constats qu'il n'a pas faits. GREEN SHIELD applique donc une règle stricte, vérifiable dans le code :

- une mission neuve démarre **vide** — aucun actif, aucun tiers, aucun risque pré-rempli ;
- ce qui n'est pas saisi apparaît comme **manquant** dans le livrable, jamais comblé ;
- un LLM ne remplit **jamais** un champ structuré : il produit du texte libre affiché à l'écran, que le consultant recopie s'il le juge bon.

---

## 🛡️ Sécurité et confidentialité — ce qui est réellement garanti

Les outils que nous utilisons ne doivent pas devenir le maillon faible. Voici l'état **exact** de l'architecture, sans embellissement.

| Garantie | Détail |
|---|---|
| **Fonctionnement hors-ligne** | L'application tourne intégralement en local (`127.0.0.1`). Sans clé API, le Copilote répond depuis un moteur local qui construit sa réponse à partir des données réelles de la mission. Aucune donnée ne sort. |
| **Données hors du dépôt** | Les missions vivent dans `%APPDATA%\GreenShield` (Windows) / `$XDG_DATA_HOME` (Linux), jamais dans le dépôt git. Une mise à jour ou un `git clean` ne peut pas les détruire. |
| **Archives chiffrées** | L'export d'une mission produit une archive **AES-256** (standard WinZip, lisible par 7-Zip). L'import est durci contre le Zip Slip et les bombes de décompression. |
| **Journal d'audit** | Chaque action sensible (création, suppression, export, purge, appel au Copilote) est tracée dans `logs/audit.log`. Le contenu des missions n'y figure jamais. |
| **Rétention RGPD** | Les entretiens contiennent des données personnelles : une durée de conservation est définie par mission, avec purge qui efface les personnes interrogées **sans jamais toucher aux constats d'audit**. |
| **Versionnement** | Un instantané est pris à chaque validation de phase et avant toute opération destructive. Aucune action n'est un aller sans retour. |

### Sortie réseau : les deux seuls cas, explicites

L'application est hors-ligne **par défaut**. Deux fonctionnalités, et deux seulement, peuvent émettre du trafic — toujours sur action volontaire :

1. **Copilote en ligne** — si (et seulement si) vous saisissez une clé API Gemini. La clé est conservée en `sessionStorage` (effacée à la fermeture de l'onglet), **jamais persistée côté serveur ni journalisée** ; elle transite par le backend qui la relaie à l'API sans la stocker. Sans clé, le repli local s'applique et rien ne sort.
2. **Dictée vocale** — elle s'appuie sur le service de reconnaissance vocale du navigateur, qui transmet l'audio à son éditeur. L'interface le signale à l'endroit où l'on dicte. Préférez le clavier pour tout élément confidentiel.

> ⚠️ **Prérequis d'exploitation.** Les missions sont stockées en JSON **non chiffré**. Un chiffrement de disque (BitLocker / LUKS) est un **prérequis**, pas une option — c'est ce qui protège les données au repos.

> ℹ️ **Portée du masquage automatique.** Le module d'anonymisation couvre aujourd'hui les **adresses IP, courriels et noms de domaine**. Il ne détecte **pas** les noms de personnes ou d'organisations. Ne comptez pas dessus pour caviarder un nom de client.

---

## 🎯 Ce que fait l'outil

### Conduite de mission guidée — 6 phases

| Phase | Contenu |
|---|---|
| **1. Cadrage & Patrimoine** | Périmètre, NDA, valeurs métier, biens supports, socle de mission (qualification, contractualisation, kick-off, entretiens). |
| **2. Diagnostic & RGPD** | Hygiène, registre des traitements (Art. 30), **AIPD** avec ses 5 obligations organisationnelles, **registre des violations** (Art. 33-34). |
| **3. Risques Tiers (TPRM)** | Volet Conseil : ratio **ANSSI** `(dépendance × pénétration) / (maturité × confiance)`. Volet GRC : exigences DORA/NIS2 vérifiables, **sans score** — ces référentiels ne se réclament pas d'EBIOS. |
| **4. Analyse des menaces** | **EBIOS RM** : événements redoutés, sources de risque, scénarios opérationnels, cas réels. |
| **5. Résilience & Conformité** | RTO/RPO, séquence **E3R** de l'ANSSI, volet stratégique d'arbitrage Direction, check-list d'audit par référentiel, **Déclaration d'Applicabilité**, bibliothèque de preuves. |
| **6. Traitement & Livrables** | Plan de remédiation piloté, risques acceptés, revue avant export, génération des livrables. |

### Fonctionnalités structurantes

- **🗂️ Multi-référentiel par mission** — une même mission peut porter **ISO 27001 + DORA + NIS2** simultanément. La check-list se regroupe par référentiel, et les livrables indiquent l'origine de chaque contrôle. C'est le cas réel d'un établissement financier visant la certification.
- **📋 Déclaration d'Applicabilité (SoA)** — les **93 contrôles de l'Annexe A ISO 27001:2022**, avec justification d'inclusion *et* d'exclusion. C'est le premier document qu'un auditeur de certification réclame. Livrable dédié (Word + Markdown).
- **🔗 Bibliothèque de preuves multi-référentiels** — une preuve écrite une fois (une PSSI signée, un contrat) peut couvrir des contrôles de **plusieurs référentiels** à la fois. Fini la ressaisie.
- **⚖️ Registre des violations RGPD** — toute violation se documente, **même jugée non notifiable** (Art. 33 §5). La règle des **72 h** est vérifiée : une violation non notifiée et non justifiée passé ce délai devient un manque **bloquant** avant export.
- **🔁 Chaîne risque → traitement** — chaque scénario porte un propriétaire, un risque résiduel, une stratégie (Réduire / Accepter / Transférer / Éviter) et un statut. Sans propriétaire ni décision, un scénario n'est qu'une observation.
- **✅ Revue avant export** — l'outil énumère ce qui manque **avant** qu'un livrable ne parte chez le client, en distinguant bloquant et recommandé. Il ne remplit rien : il rend l'incomplétude visible.
- **📄 Exports multi-formats** — NDA, EBIOS RM, PSSI/PRI, AIPD, Déclaration d'Applicabilité et rapport de mission, en **Word (`python-docx`), HTML et Markdown**, à l'identité de votre cabinet (logo, nom, coordonnées).
- **⏱️ Suivi des charges** — temps consommé par phase, comparé au budget vendu, repris dans le rapport.
- **🔬 AuditCraft-GRC** — analyse hors-ligne de fichiers de configuration (`sshd_config`, `nginx.conf`) rattachée aux référentiels **CIS v8 / NIST CSF 2.0**, avec un **taux de couverture technique** affiché honnêtement : ce qui repose sur du déclaratif est annoncé comme tel.

### 🚀 Mission de démonstration

Un clic sur **« Mission de démo »** génère une mission **entièrement fictive** (« Néobanque Fictive SAS »), explicitement marquée, qui traverse chaque fonctionnalité : deux référentiels actifs, une SoA partiellement statuée, des preuves partagées entre référentiels, deux violations RGPD illustrant les deux branches de l'article 33, une AIPD conduite, quatre scénarios EBIOS et un plan de traitement piloté.

Elle permet de démontrer l'outil **sans jamais ouvrir une mission cliente réelle** — et de vérifier après chaque évolution que la chaîne complète fonctionne encore.

---

## 🛠️ Savoir-faire normatif mis en œuvre

- **Référentiels** : ISO/IEC 27001:2022 (dont les 93 contrôles de l'Annexe A), DORA, NIS2, RGPD, NIST CSF 2.0, EU AI Act.
- **Méthodes** : EBIOS RM (ANSSI), AIPD/PIA (CNIL), séquence de remédiation E3R (ANSSI), ratio de criticité tiers ANSSI.
- **Architecture** : React 19 + Vite + Tailwind v4 (TypeScript strict) / FastAPI + Python 3.12, données en fichiers JSON/YAML à plat, empaquetage Docker Compose.
- **Qualité** : **624 tests backend (pytest) et 150 tests frontend (vitest)**, schéma de mission versionné avec chaîne de migration rejouable, écritures atomiques.

> **Respect du droit d'auteur des normes** : les référentiels embarqués ne contiennent que des **identifiants et intitulés courts reformulés**. Aucun texte normatif ISO/AFNOR n'est reproduit.

---

## 🚀 Installation & démarrage

```bash
# Lancement via Docker (recommandé)
make up          # construit et lance l'app sur http://localhost:8080
```

> Sans `make` (Windows) : `docker compose up --build -d`.

### En développement

```bash
# Backend
cd api && py -3 -m uvicorn main:app --reload --port 8000

# Frontend
cd web && npm install && npm run dev
```

### Tests

```bash
py -3 -m pytest api/tests -q      # 624 tests backend
cd web && npx vitest run          # 150 tests frontend
cd web && npx tsc --noEmit        # typage strict
```

### Configuration recommandée

| Variable | Rôle |
|---|---|
| `GREENSHIELD_API_SECRET` | Secret de signature des jetons de session. **À définir en déploiement** : sinon un secret est généré et conservé localement au premier démarrage. |
| `GREENSHIELD_DATA_DIR` | Répertoire des missions. Par défaut `%APPDATA%\GreenShield\projects`. |

---

## ⚖️ Licence & usage

[PolyForm Noncommercial 1.0.0](LICENSE.md).
Ce projet est partagé en open source pour contribuer à la communauté cyber et démontrer mon approche du métier.

- ✅ Lecture, étude, modification, usage associatif ou enseignement.
- ❌ Revente, intégration commerciale ou utilisation en SaaS payant.

---

*GREEN SHIELD — Un projet conçu à l'intersection de la cybersécurité et de l'ingénierie logicielle.*
