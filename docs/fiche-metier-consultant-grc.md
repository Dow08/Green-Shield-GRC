# Guide et Fiche Métier : Consultant en Cybersécurité & GRC

> Contexte métier de référence pour GREEN SHIELD — sert de socle documentaire pour l'orientation
> fonctionnelle des modules (référentiels couverts, vocabulaire, périmètre du conseil GRC).
> Alimente notamment les briques à venir « Copilote GRC » et « Registre de missions » (cf. [README](../README.md)).

Ce document rassemble une vue d'ensemble détaillée des missions, outillages, fonctions transverses et aspects méconnus du métier de **Consultant en Cybersécurité & GRC (Gouvernance, Risque et Conformité)**.

---

## 1. Missions quotidiennes et anecdotiques

Le quotidien du consultant varie selon les phases du projet (audit, accompagnement, gestion de crise ou maintien en condition de sécurité).

### Missions récurrentes & stratégiques
* **Audits d'écart (Gap Analysis) & Conformité :** Évaluer la maturité sécurité d'une organisation par rapport à des standards et réglementations clés (ISO/IEC 27001, NIS 2, RGPD, PCI-DSS, DORA, EU AI Act).
* **Analyse de risques (EBIOS RM, ISO 27005) :** Identifier les biens essentiels/supports, modéliser les menaces, estimer les impacts business/juridiques et définir des plans de traitement du risque.
* **Rédaction de PSSI et politiques de sécurité :** Concevoir la Politique de Sécurité des Systèmes d'Information (PSSI), les chartes informatiques, les politiques de contrôle d'accès, de chiffrement et les procédures d'incident.
* **Accompagnement à l'homologation / certification :** Préparer les équipes clientes au passage d'un auditeur certificateur (AFNOR, BSI, DNV) ou à l'homologation de sécurité d'un système.
* **Sensibilisation et acculturation :** Animer des ateliers pour les collaborateurs (phishing, hygiène informatique) ou des sessions de gestion de crise pour le Comité de Direction (ComDir/Board).
* **Revue d'architecture & SecOps :** Valider la conformité des architectures SI (segmentation réseau, gestion des identités IAM, politique d'accès, durcissement/hardening).

### Le quotidien "de l'ombre" (et anecdotique)
* **Traduction technique vers l'exécutif :** Expliquer à un DSI ou un CEO pourquoi un *patch* critique non appliqué constitue une menace stratégique majeure, sans utiliser de jargon obscur.
* **Gestion de la résistance au changement :** Convaincre des administrateurs système chevronnés d'adopter le moindre privilège, la bastionisation ou le MFA sans perception de lourdeur administrative.
* **Réponse aux questionnaires sécurité clients (VRA / Vendor Risk Assessment) :** Remplir ou auditer des dizaines de grilles d'évaluation pour valider le niveau de sécurité d'un tiers dans la chaîne d'approvisionnement (*Supply Chain Risk*).
* **Arbitrage "Sécurité vs Métier" :** Trouver le compromis pragmatique lorsqu'une mesure de sécurité bloque un processus métier critique à forte valeur ajoutée.

---

## 2. Besoins pour réaliser la mission (Outillage & Compétences)

### Outillage méthodologique & Référentiels (Mis à jour 2026)
* **Cadres de gestion du risque :** EBIOS RM (méthode ANSSI), ISO 27005, NIST SP 800-30, FAIR (Quantitative Risk Analysis).
* **Standards & Normes ISO/IEC :** ISO/IEC 27001 (SMSI), ISO/IEC 27002 (Mesures de sécurité), ISO/IEC 27701 (Privacy), ISO/IEC 42001 (Systèmes de management de l'IA).
* **Réglementations européennes & Législation :**
  * **EU AI Act (Règlement sur l'IA) :** Classification des risques des systèmes d'IA (risque inacceptable, haut risque, risque limité), exigences de transparence, gouvernance des données, évaluation d'impact et conformité des modèles d'IA générative et souveraine.
  * **NIS 2 :** Directive sur la cybersécurité des entités essentielles et importantes (gestion des risques, obligation de notification d'incident, responsabilité des dirigeants).
  * **DORA (Digital Operational Resilience Act) :** Résilience opérationnelle numérique pour le secteur financier.
  * **RGPD / GDPR :** Protection des données à caractère personnel, AIPD (Analyses d'Impact relatives à la Protection des Données).
* **Frameworks techniques & Matrice de menaces :** MITRE ATT&CK, CIS Controls, OWASP Top 10 (Web, API, LLM/IA).

### Boîte à outils logicielle & Technique
* **Outils GRC & Gestion documentaire :** Logiciels de cartographie et de gestion des risques (MonEBIOS, ServiceNow GRC, LogicGate, Archer, interfaces personnalisées n8n/Python).
* **Outils de diagnostic & Audit technique :** Scanners de vulnérabilités (Nessus, OpenVAS, Trivy), scripts d'audit de configuration (Active Directory, Azure/AWS/GCP), outils de cartographie réseau et de gestion des identités.
* **Prototypage & Continuous Compliance :** Workflows d'automatisation (n8n, Python) pour collecter des preuves de conformité (*compliance-as-code*), requêter les API d'infrastructures et générer des rapports dynamiques.

### Soft Skills essentiels
* **Vulgarisation & Pédagogie :** Passer d'un discours technique de bas niveau à une restitution synthétique axée sur les risques métiers et financiers.
* **Diplomatie & Négociation :** Positionner la sécurité comme un vecteur de confiance et un levier business plutôt que comme un centre de coût ou un blocage.
* **Rigueur rédactionnelle :** Rédiger des livrables exploitables, juridiquement et méthodologiquement irréprochables.

---

## 3. Fonctions transverses requises en consulting

Afin d'exécuter correctement ses missions et d'apporter de la valeur, le consultant doit faire appel à des compétences et fonctions transverses au-delà du strict périmètre de la cybersécurité :

* **Fonction Juridique & Réglementaire (Cyber-droit) :** Comprendre l'articulation entre le droit du numérique, la responsabilité civile/pénale des dirigeants, les contrats fournisseurs, le droit du travail (surveillance, charte informatique) et les clauses d'assurance cyber.
* **Fonction Achats & Gestion de la Supply Chain :** Évaluer les risques tiers (*Third-Party Risk Management* - TPRM), auditer la chaîne de sous-traitance et intégrer des exigences de sécurité dans les appels d'offres et contrats.
* **Fonction Ressources Humaines & Conduite du Changement :** Gérer l'accompagnement au changement, former le personnel, structurer la sensibilisation selon les profils métiers et traiter l'impact des mesures de sécurité sur les conditions de travail.
* **Fonction Contrôle Interne, Audit & Gestion des Risques Globaux :** Alignement avec la gestion globale des risques d'entreprise (*Enterprise Risk Management* - ERM), intégration dans les cartographies de risques globales et articulation avec l'audit interne.
* **Fonction Communication de Crise & Relations Publiques :** Structurer la communication interne et externe lors d'une crise cyber majeure (notification aux autorités comme la CNIL/ANSSI, gestion des médias, clients, partenaires).
* **Fonction Finance & Contrôle de Gestion :** Justifier le ROI (Retour sur Investissement) ou le ROSI (*Return on Security Investment*), chiffrer les impacts financiers des scénarios de risques et gérer les budgets de remédiation.
* **Fonction Architecture Système & Ingénierie Cloud/DevOps :** Comprendre les pipelines CI/CD (DevSecOps), l'infrastructure-as-code (IaC), les environnements hybrides Multi-Cloud et la conteneurisation pour que les préconisations GRC soient pragmatiques et applicables par les équipes techniques.

---

## 4. Les coulisses et angles morts du métier (Réflexion avancée)

* **La diplomatie politique et la posture de "Tierce Partie Neutre" :** Être le catalyseur externe permettant de porter la voix des équipes techniques auprès de la direction pour débloquer des budgets ou arbitrages stratégiques.
* **La veille réglementaire & géopolitique permanente :** Suivre les évolutions jurisprudentielles, les sanctions CNIL, les nouvelles réglementations européennes (comme le AI Act) et l'évolution des menaces globales pour adapter les stratégies.
* **La conformité continue (*Compliance-as-Code*) :** Passer de la conformité statique basée sur des fiches Excel à un contrôle automatisé connecté aux API de l'infrastructure (Active Directory, Cloud, SIEM).
* **Facteur humain & Gestion du stress en crise :** Tester lors de simulations de crise non seulement les procédures écrites (PCA/PRA), mais aussi la capacité de décision sous fort niveau de stress du Comité de Direction.
* **Responsabilité morale et juridique du consultant :** Porter la responsabilité de l'exhaustivité des analyses de risques ; une omission importante peut impacter directement la posture de sécurité et la conformité du client.
