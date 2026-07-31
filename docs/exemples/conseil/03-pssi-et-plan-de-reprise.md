**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **PSSI & PLAN DE REPRISE** — Vernier Composites SAS
> Édité le 31/07/2026 11:10 · Réf. `audit_de_securite_et_analyse_de_risque_ebios_rm`
> **Document confidentiel — diffusion restreinte**

# POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI) & PLAN DE REPRISE (PRI)

**Client :** Vernier Composites SAS  
**Projet :** Audit de sécurité & analyse de risque EBIOS RM  
**Date :** 31/07/2026 11:10  
**Auteur :** Consultant, Cabinet non renseigné  

---

## I. POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI)



---

## II. PLAN DE REPRISE INFORMATIQUE & RÉSILIENCE (PRI)

### 2.1 Indicateurs Temporels de Continuité
*   **RTO (Recovery Time Objective / Temps de reprise max) :** `24 heures pour la ligne de production, 72 heures pour la bureautique`
*   **RPO (Recovery Point Objective / Perte de données max) :** `4 heures pour le MES, 24 heures pour les serveurs de fichiers`

### 2.2 Politique de Sauvegarde et d'Immuabilité
Objectif cible : règle 3-2-1 avec une copie immuable hors site et un test de restauration semestriel documenté. État constaté : sauvegarde quotidienne unique sur NAS secondaire du même VLAN, jamais restaurée en test.

### 2.3 Séquence de Remédiation en Gestion de Crise (E3R de l'ANSSI)
En cas de compromission majeure de l'Active Directory ou de l'infrastructure Cloud :

1.  **Endiguement (Contenir l'attaquant) :**  
    Isolement immédiat du VLAN production par coupure des liens inter-VLAN sur le cœur de réseau, arrêt contrôlé des fours selon la procédure de sécurité matière, déconnexion du VPN prestataires.
2.  **Éviction (Reprendre le contrôle du cœur de confiance) :**  
    Réinitialisation du compte krbtgt à deux reprises, révocation de tous les accès prestataires, réinitialisation des mots de passe des 12 comptes à privilèges, blocage des règles de transfert de messagerie créées durant l'incident.
3.  **Éradication (Nettoyage en profondeur des emprises) :**  
    Analyse hors ligne des deux contrôleurs de domaine, reconstruction plutôt que nettoyage en cas de doute, recherche des tâches planifiées et services persistants sur l'ensemble du parc, suppression des comptes dormants.
4.  **Reconstruction (Rebâtir de façon durcie dès la conception) :**
    Remontée de l'AD depuis une sauvegarde antérieure à la compromission, reconstruction des postes depuis un master durci, remise en service par vagues avec surveillance renforcée pendant 30 jours, retour d'expérience formalisé sous 15 jours.

### 2.4 Volet Stratégique — Arbitrage Direction
*   **Urgence de redémarrage :** 
*   **Coûts et risques d'un redémarrage précipité :** 
*   **Décision retenue et autorité :** 

---

### SIGNATURES POUR HOMOLOGATION DE SÉCURITÉ

| Pour Cabinet non renseigné | Pour la Direction de Vernier Composites SAS |
| :--- | :--- |
| **Consultant** | **Directeur Général / RSSI** |
| Signature : | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `3f13820ef901ac4680d862d6e113c1c9e43cdc87a055423bf6e3d5c0c1e27177`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
