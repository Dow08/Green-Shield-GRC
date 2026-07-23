"""parser.py — Extraction factuelle des directives de configuration.

Parsing 100 % HORS-LIGNE et tolérant : on n'exécute rien, on ne se connecte à
rien, on lit des fichiers. Chaque directive extraite conserve sa ligne d'origine
(numéro + texte brut) pour servir de PREUVE dans le rapport d'audit.

Deux formats sont pris en charge :
  * style « clé valeur »   -> OpenSSH (sshd_config)
  * style « directive args; » -> nginx

Robustesse : une ligne malformée est simplement ignorée. Aucune exception n'est
levée à cause d'une syntaxe cible incorrecte (c'est justement ce qu'on audite).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Directive:
    """Une directive de configuration extraite d'un fichier cible."""
    key: str
    value: str
    line: int          # numéro de ligne (1-indexé) — preuve
    raw: str           # ligne brute d'origine — preuve


# --- expressions régulières compilées une fois ---
_SSHD_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s+(.+?)\s*$")
_NGINX_STMT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s+([^;{}]+);")


def _strip_comment(line: str) -> str:
    """Retire le commentaire ('#' jusqu'à la fin de ligne)."""
    idx = line.find("#")
    return line if idx < 0 else line[:idx]


def parse_sshd(text: str) -> list[Directive]:
    """Parse un fichier de style OpenSSH ('Clé Valeur' par ligne)."""
    directives: list[Directive] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        match = _SSHD_LINE.match(line)
        if match is None:
            continue  # ligne malformée -> ignorée sans planter
        directives.append(
            Directive(key=match.group(1), value=match.group(2).strip(), line=n, raw=raw.strip())
        )
    return directives


def parse_nginx(text: str) -> list[Directive]:
    """Parse un fichier nginx en directives 'nom args;' (blocs/commentaires ignorés)."""
    directives: list[Directive] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        match = _NGINX_STMT.search(line)
        if match is None:
            continue  # ouverture/fermeture de bloc ou ligne sans instruction -> ignorée
        directives.append(
            Directive(key=match.group(1), value=match.group(2).strip(), line=n, raw=raw.strip())
        )
    return directives


# Aiguillage par nom de fichier -> fonction de parsing adaptée.
_PARSERS = {
    "sshd_config": parse_sshd,
    "nginx.conf": parse_nginx,
}


def parse_file(filename: str, text: str) -> list[Directive]:
    """Parse `text` selon le type déduit de `filename`.

    Repli : si le nom est inconnu, on tente le style 'clé valeur' (le plus courant).
    """
    parser = _PARSERS.get(filename, parse_sshd)
    return parser(text)


def effective(directives: list[Directive], key: str) -> Directive | None:
    """Renvoie la directive effective pour `key` (première occurrence, insensible à
    la casse), ou None si la clé est absente. La première occurrence prime — c'est
    la sémantique d'OpenSSH ; nos cibles ne déclarent chaque clé qu'une fois."""
    key_low = key.lower()
    for directive in directives:
        if directive.key.lower() == key_low:
            return directive
    return None
