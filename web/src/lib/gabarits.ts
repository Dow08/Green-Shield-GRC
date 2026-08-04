/**
 * Gabarits métier proposés dans les sélecteurs des phases 1 et 2.
 * Extraits de Projects.tsx lors du découpage du 29/07/2026 : plusieurs
 * composants de phase les consomment, ils n'appartiennent donc plus à une page.
 */

export const SUGGESTED_METIER = [
  { id: "VM-BDD", name: "Base de données Clients", description: "Contient les identités, contrats et coordonnées.", is_personal_data: true },
  { id: "VM-RD", name: "Fichier de R&D / Brevets", description: "Données de propriété intellectuelle stratégique.", is_personal_data: false },
  { id: "VM-FACT", name: "Système de Facturation", description: "Données de transactions bancaires et comptables.", is_personal_data: true },
  { id: "VM-RH", name: "Dossiers RH & Fiches de Paie", description: "Données confidentielles sur les collaborateurs.", is_personal_data: true },
  { id: "VM-WEB", name: "Portail Client (E-commerce)", description: "Service web hébergeant l'expérience client active.", is_personal_data: true }
];

export const SUGGESTED_SUPPORT = [
  { id: "BS-AD", name: "Active Directory (AD)", type: "Logiciel", description: "Annuaire d'identité d'administration centralisé.", owner: "Administrateur SI" },
  { id: "BS-BK", name: "Serveur de Sauvegardes", type: "Matériel", description: "Héberge les sauvegardes immuables locales.", owner: "Administrateur SI" },
  { id: "BS-FW", name: "Pare-feu de périmètre", type: "Réseau", description: "Contrôle d'accès et filtrage de flux.", owner: "Équipe Réseau" },
  { id: "BS-WORK", name: "Postes de travail", type: "Matériel", description: "Flotte d'ordinateurs d'utilisateurs avec EDR.", owner: "RSSI / SecOps" },
  { id: "BS-VPN", name: "Passerelle VPN d'accès", type: "Réseau", description: "Tunnel d'accès sécurisé pour les télétravailleurs.", owner: "Équipe Réseau" },
  { id: "BS-SIEM", name: "Console SIEM (Logs)", type: "Logiciel", description: "Centralisation et analyse des journaux d'audit.", owner: "Équipe SOC/SecOps" }
];

export const SUGGESTED_RGPD = [
  { id: "RG-PAYE", name: "Gestion de la paie & RH", purpose: "Virement des salaires et suivi de carrières.", data_categories: "NIR, Coordonnées bancaires, Échelon", retention: "5 ans" },
  { id: "RG-CRM", name: "Gestion de la Relation Client (CRM)", purpose: "Suivi commercial et prospection.", data_categories: "Nom, Prénom, Téléphone, Email", retention: "Fin de relation + 3 ans" },
  { id: "RG-MESS", name: "Messagerie Professionnelle (Email)", purpose: "Communication interne et externe des collaborateurs.", data_categories: "Email, Logs de connexion, Contenu des flux", retention: "1 an (logs)" }
];
