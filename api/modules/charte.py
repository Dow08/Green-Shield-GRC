"""charte.py — identité visuelle des livrables GREEN SHIELD.

Le logo est embarqué en base64 : un livrable doit rester lisible hors ligne,
sans dépendre d'un serveur d'images ni d'un fichier joint qui se perdrait à la
transmission. Version 72 px (≈9 ko) — suffisante pour un en-tête de document
et un ordre de grandeur plus légère que l'original.
"""
from __future__ import annotations

import base64
import binascii
from html import escape

LOGO_BASE64 = (
    "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"
    "L96gd3J5AAAAAElFTkSuQmCC"
)

LOGO_DATA_URI = f"data:image/png;base64,{LOGO_BASE64}"

# Signatures binaires suffisantes pour distinguer une image réelle d'un texte
# quelconque envoyé par erreur — pas une validation de format complète, juste
# un garde-fou avant d'embarquer l'octet brut dans un document.
_SIGNATURES_IMAGE = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
}


def _type_image(donnees: bytes) -> str | None:
    for signature, type_mime in _SIGNATURES_IMAGE.items():
        if donnees.startswith(signature):
            return type_mime
    return None


def logo_bytes(logo_base64: str = "") -> bytes:
    """Octets du logo à embarquer dans un livrable : celui du cabinet si le
    consultant en a déposé un valide dans Réglages (PNG ou JPEG), sinon le
    logo GREEN SHIELD par défaut.

    Ne lève jamais : une image corrompue ou d'un format non pris en charge ne
    doit jamais faire échouer la génération d'un rapport, elle retombe
    silencieusement sur le logo par défaut.
    """
    if logo_base64:
        try:
            donnees = base64.b64decode(logo_base64, validate=True)
        except (binascii.Error, ValueError):
            donnees = b""
        if donnees and _type_image(donnees):
            return donnees
    return base64.b64decode(LOGO_BASE64)


def logo_data_uri(logo_base64: str = "") -> str:
    """Équivalent de `logo_bytes()` sous forme de `data:` URI pour le HTML."""
    if logo_base64:
        try:
            donnees = base64.b64decode(logo_base64, validate=True)
        except (binascii.Error, ValueError):
            donnees = b""
        type_mime = _type_image(donnees) if donnees else None
        if type_mime:
            return f"data:image/{type_mime};base64,{logo_base64}"
    return LOGO_DATA_URI


# L'application sert n'importe quel consultant, jamais un seul cabinet : ne
# jamais retomber en silence sur un nom d'entreprise ou de personne écrit en
# dur (retour utilisateur du 30/07/2026 — le NDA affichait "DP Cyber
# Consulting" quel que soit le cabinet réellement saisi dans Réglages).
_CABINET_DEFAUT = "Cabinet non renseigné"


def entete_markdown(titre_document: str, client: str, date_edition: str, reference: str,
                    cabinet: str = "") -> str:
    """En-tête d'un livrable **Markdown** : uniquement du Markdown.

    L'en-tête HTML+CSS ci-dessous était auparavant injecté dans les exports
    Markdown. Le résultat ne rendait correctement nulle part (constaté le
    30/07/2026) : GitHub retire les feuilles de style et bloque les images en
    `data:` URI, tandis qu'un navigateur affiche les tableaux Markdown en texte
    brut, tuyaux compris. Chaque format porte désormais sa propre mise en forme —
    Markdown pur ici, HTML complet dans `report_html.py`.

    `client`/`cabinet` sont échappés (`html.escape`) : ce Markdown est ensuite
    converti en HTML par `markdown.markdown()` côté appelant, qui laisse passer
    tel quel le HTML brut présent dans sa source.
    """
    client = escape(str(client)) if client else client
    cabinet_affiche = escape(str(cabinet)) if cabinet else cabinet
    return (f"**GREEN SHIELD** · {cabinet_affiche or _CABINET_DEFAUT} — Audit & Conseil Cybersécurité\n\n"
            f"> **{titre_document}** — {client}\n"
            f"> Édité le {date_edition} · Réf. `{reference}`\n"
            f"> **Document confidentiel — diffusion restreinte**\n")


def pied_markdown(empreinte: str, cabinet: str = "") -> str:
    """Pied d'un livrable Markdown."""
    cabinet_affiche = escape(str(cabinet)) if cabinet else cabinet
    return ("\n---\n\n"
            f"GREEN SHIELD — {cabinet_affiche or _CABINET_DEFAUT} · Document confidentiel, "
            "ne pas diffuser sans autorisation écrite.\n\n"
            f"Empreinte SHA-256 de l'état de la mission à l'édition : `{empreinte}`\n\n"
            "*Toute modification ultérieure de la mission, même rétablie, produit "
            "une empreinte différente.*\n")
