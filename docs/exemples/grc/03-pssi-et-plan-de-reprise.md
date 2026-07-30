**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **PSSI & PLAN DE REPRISE** — Banque Aurore SA
> Édité le 30/07/2026 22:05 · Réf. `audit_de_conformite_iso_27001_et_dora`
> **Document confidentiel — diffusion restreinte**

# POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI) & PLAN DE REPRISE (PRI)

**Client :** Banque Aurore SA  
**Projet :** Audit de conformité ISO 27001 & DORA  
**Date :** 30/07/2026 22:05  
**Auteur :** Consultant, Cabinet non renseigné  

---

## I. POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI)



---

## II. PLAN DE REPRISE INFORMATIQUE & RÉSILIENCE (PRI)

### 2.1 Indicateurs Temporels de Continuité
*   **RTO (Recovery Time Objective / Temps de reprise max) :** `2 heures pour le paiement instantané (fonction critique DORA), 8 heures pour la banque en ligne`
*   **RPO (Recovery Point Objective / Perte de données max) :** `15 minutes pour les opérations de paiement, 1 heure pour les référentiels clients`

### 2.2 Politique de Sauvegarde et d'Immuabilité
Réplication synchrone entre les deux datacenters, sauvegarde immuable quotidienne conservée 35 jours hors site, test de bascule complet trimestriel avec procès-verbal transmis à l'ACPR.

### 2.3 Séquence de Remédiation en Gestion de Crise (E3R de l'ANSSI)
En cas de compromission majeure de l'Active Directory ou de l'infrastructure Cloud :

1.  **Endiguement (Contenir l'attaquant) :**  
    Isolement de la zone compromise par bascule sur le site de repli, gel des livraisons éditeur, activation de la cellule de crise avec astreinte RSSI sous 30 minutes.
2.  **Éviction (Reprendre le contrôle du cœur de confiance) :**  
    Révocation des certificats et jetons d'interconnexion, réinitialisation des comptes à privilèges et des comptes de service, rupture temporaire du lien avec l'éditeur.
3.  **Éradication (Nettoyage en profondeur des emprises) :**  
    Analyse forensique des binaires livrés, comparaison aux empreintes de référence, reconstruction des serveurs concernés depuis un socle durci vérifié.
4.  **Reconstruction (Rebâtir de façon durcie dès la conception) :**
    Remise en service progressive avec vérification d'intégrité comptable poste par poste, réconciliation des opérations sur la période suspecte, notification ACPR de clôture d'incident et retour d'expérience sous 30 jours.

### 2.4 Volet Stratégique — Arbitrage Direction
*   **Urgence de redémarrage :** 
*   **Coûts et risques d'un redémarrage précipité :** 
*   **Décision retenue et autorité :** 

---

### SIGNATURES POUR HOMOLOGATION DE SÉCURITÉ

| Pour Cabinet non renseigné | Pour la Direction de Banque Aurore SA |
| :--- | :--- |
| **Consultant** | **Directeur Général / RSSI** |
| Signature : | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `c6c4d45e568cff57cfe0161d28b9ae8c7b73842f56e0660190548ad3e4992b08`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
