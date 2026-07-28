"""Module Copilote GRC — assistant transverse branché sur les constats réels.

Contrairement au Copilote embarqué en Phase 6 d'une mission (`projects.py`,
`run_project_copilot`, qui répond dans le contexte d'UN client), ce module
agrège les constats de TOUTES les missions du registre (tiers à risque TPRM,
événements redoutés EBIOS RM, non-conformités techniques AuditCraft-GRC,
Cyberdéparts en attente) pour que le consultant puisse prioriser son
portefeuille. Aucune donnée n'est inventée : chaque chiffre vient d'une
lecture directe des missions stockées (cf. philosophie « Factuel » de
REFERENTIEL.md).

Même bascule en ligne (Gemini, via `ai_gateway`) / hors-ligne que le Copilote
de mission : sans clé API, réponses de synthèse construites uniquement à
partir des chiffres agrégés réels.
"""
from __future__ import annotations

from fastapi import APIRouter

from . import ai_gateway, projects

router = APIRouter(prefix="/api")


def aggregate_context() -> dict:
    """Relit toutes les missions du registre et agrège leurs constats réels.
    Aucune donnée n'est inventée : chaque entrée provient d'un champ existant
    d'une mission (TPRM, EBIOS RM, scan technique, plan de traitement)."""
    all_projects = projects.list_projects()

    by_type: dict[str, int] = {"grc": 0, "consulting": 0}
    progress_sum = 0
    tiers_critiques: list[dict] = []
    redoute_events: list[dict] = []
    non_conformites: list[dict] = []
    quick_wins_en_attente = 0

    for p in all_projects:
        ptype = p.get("type", "consulting")
        by_type[ptype] = by_type.get(ptype, 0) + 1
        progress_sum += p.get("progress", 0) or 0
        steps = p.get("steps", {}) or {}

        for tier in (steps.get("tprm") or {}).get("tiers", []) or []:
            if tier.get("rating") in ("Critique", "Élevé"):
                tiers_critiques.append({
                    "project": p.get("name"),
                    "project_id": p.get("id"),
                    "tiers_name": tier.get("name"),
                    "score": tier.get("score"),
                    "rating": tier.get("rating"),
                })

        for ev in (steps.get("ebios") or {}).get("redoute_events", []) or []:
            if (ev.get("gravity") or 0) >= 3:
                redoute_events.append({
                    "project": p.get("name"),
                    "project_id": p.get("id"),
                    "event": ev.get("event"),
                    "gravity": ev.get("gravity"),
                })

        technical_results = (steps.get("evaluation") or {}).get("technical_results")
        if technical_results:
            for c in technical_results.get("controls", []) or []:
                if c.get("status") == "NON_CONFORME":
                    non_conformites.append({
                        "project": p.get("name"),
                        "project_id": p.get("id"),
                        "control": c.get("title"),
                        "severity": c.get("severity"),
                    })

        traitement = steps.get("traitement") or {}
        if not traitement.get("validated"):
            quick_wins_en_attente += len(traitement.get("quick_wins", []) or [])

    tiers_critiques.sort(key=lambda t: t.get("score") or 0, reverse=True)
    redoute_events.sort(key=lambda e: e.get("gravity") or 0, reverse=True)

    total = len(all_projects)
    return {
        "total_projects": total,
        "by_type": by_type,
        "avg_progress": round(progress_sum / total) if total else 0,
        "tiers_critiques": tiers_critiques[:10],
        "redoute_events": redoute_events[:10],
        "non_conformites": non_conformites[:15],
        "quick_wins_en_attente": quick_wins_en_attente,
    }


def _build_system_context(context: dict) -> str:
    return (
        "Tu es le Copilote GRC de GREEN SHIELD, assistant transverse d'un consultant "
        "senior en cybersécurité (ISO 27001, NIS2, EBIOS RM, RGPD). Voici l'état RÉEL "
        "et FACTUEL actuel du portefeuille de missions — n'invente aucune donnée en "
        "dehors de ce contexte, appuie chaque recommandation dessus :\n"
        f"- {context['total_projects']} mission(s) au total "
        f"(GRC : {context['by_type'].get('grc', 0)}, Conseil : {context['by_type'].get('consulting', 0)}), "
        f"progression moyenne {context['avg_progress']}%.\n"
        f"- {len(context['tiers_critiques'])} tiers à risque Critique/Élevé (TPRM).\n"
        f"- {len(context['redoute_events'])} événement(s) redouté(s) EBIOS RM de gravité ≥ 3.\n"
        f"- {len(context['non_conformites'])} non-conformité(s) technique(s) détectée(s) par AuditCraft-GRC.\n"
        f"- {context['quick_wins_en_attente']} mesure(s) Cyberdépart en attente de traitement."
    )


def _offline_reply(context: dict, prompt: str) -> str:
    if context["total_projects"] == 0:
        return (
            "### [Copilote GRC] Portefeuille vide\n\n"
            "Aucune mission n'existe encore dans le Registre de missions. Créez une "
            "première mission pour que le Copilote puisse prioriser des constats réels."
        )

    lines = [f"### [Copilote GRC] Synthèse du portefeuille ({context['total_projects']} mission(s))\n"]
    lines.append(
        f"Progression moyenne : **{context['avg_progress']}%** "
        f"(GRC : {context['by_type'].get('grc', 0)}, Conseil : {context['by_type'].get('consulting', 0)}).\n"
    )

    lines.append("**Priorités identifiées, par ordre de gravité :**")
    rang = 1
    for t in context["tiers_critiques"][:3]:
        lines.append(f"{rang}. [TPRM] « {t['tiers_name']} » ({t['project']}) — tiers {t['rating']} (score {t['score']}).")
        rang += 1
    for e in context["redoute_events"][:3]:
        lines.append(f"{rang}. [EBIOS RM] « {e['event']} » ({e['project']}) — gravité {e['gravity']}/4.")
        rang += 1
    for c in context["non_conformites"][:3]:
        lines.append(f"{rang}. [AuditCraft-GRC] « {c['control']} » ({c['project']}) — écart {c['severity']}.")
        rang += 1

    if rang == 1:
        lines.append("Aucun constat critique remonté à ce jour sur le portefeuille : poursuivez les diagnostics en cours.")

    if context["quick_wins_en_attente"] > 0:
        lines.append(
            f"\n**Cyberdépart :** {context['quick_wins_en_attente']} mesure(s) prioritaire(s) restent à valider "
            "en Phase 6 sur les missions non finalisées."
        )

    return "\n".join(lines)


@router.get("/copilot/context")
def get_copilot_context() -> dict:
    return aggregate_context()


@router.post("/copilot/ask")
def ask_copilot(data: dict) -> dict:
    prompt = data.get("prompt", "")
    api_key = (data.get("key") or "").strip()
    context = aggregate_context()

    if api_key:
        online_text = ai_gateway.call_gemini(api_key, _build_system_context(context), prompt)
        if online_text is not None:
            return {"status": "success", "response": online_text, "source": "online", "context": context}

    return {
        "status": "success",
        "response": _offline_reply(context, prompt),
        "source": "offline_fallback" if api_key else "offline",
        "context": context,
    }
