"""app.py — AuditCraft GRC · interface exécutive (Streamlit).

Tableau de bord d'audit de conformité : score global, failles critiques,
mapping écart technique -> impact normatif (ISO/RGPD), et export du rapport
COMEX en Markdown. Aucune logique métier ici : l'app orchestre engine + reporter.
"""
from __future__ import annotations

import html
import os
import time
from pathlib import Path

import streamlit as st

import engine
import reporter
from engine import COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE

# ------------------------------------------------------------------ config
st.set_page_config(page_title="AuditCraft GRC", page_icon="🛡️", layout="wide")

BASE = Path(__file__).resolve().parent
RULES_PATH = BASE / "grc_rules.yaml"
# En conteneur : /audit/target (monté :ro). En local : ../lab_target.
TARGET_DIR = os.environ.get("AUDIT_TARGET_DIR", str(BASE.parent / "lab_target"))

SEV_COLOR = {"Critique": "#f0455f", "Élevé": "#ff8a3d", "Moyen": "#f2c14e", "Faible": "#4ea1ff"}
STATUS_ICON = {COMPLIANT: "🟢", NON_COMPLIANT: "🔴", NOT_APPLICABLE: "⚪"}

CSS = """
<style>
  .block-container{padding-top:1.6rem;max-width:1180px}
  .ac-head{display:flex;align-items:center;gap:14px;border-bottom:1px solid #1d2c46;padding-bottom:14px;margin-bottom:18px}
  .ac-head .logo{font-size:30px}
  .ac-head h1{font-size:25px;margin:0;font-weight:800;letter-spacing:.01em;color:#e8eef8}
  .ac-head .eyebrow{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#64748b;font-weight:700}
  .ac-head .sub{color:#9fb0c8;font-size:13px}
  .ac-grid{display:flex;gap:14px;flex-wrap:wrap;align-items:stretch;margin:6px 0 8px}
  .ac-gauge{flex:0 0 auto}
  .ac-gauge .ring{width:132px;height:132px;border-radius:50%;display:flex;align-items:center;justify-content:center}
  .ac-gauge .hole{width:104px;height:104px;border-radius:50%;background:#0a1120;display:flex;flex-direction:column;align-items:center;justify-content:center}
  .ac-gauge .num{font-size:32px;font-weight:800;color:#e8eef8;line-height:1}
  .ac-gauge .num span{font-size:15px;color:#64748b}
  .ac-gauge .bd{font-size:10px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;margin-top:3px}
  .ac-kpi{flex:1 1 150px;min-width:150px;border:1px solid #1d2c46;border-radius:12px;background:#101a2c;padding:14px 16px}
  .ac-kpi .v{font-size:28px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums}
  .ac-kpi .l{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#64748b;font-weight:700;margin-top:6px}
  .ac-kpi .s{font-size:11px;color:#9fb0c8;margin-top:2px}
  table.ac-tbl{width:100%;border-collapse:collapse;font-size:13px;margin-top:4px}
  table.ac-tbl th{text-align:left;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#64748b;font-weight:700;padding:8px 10px;border-bottom:1px solid #1d2c46}
  table.ac-tbl td{padding:9px 10px;border-bottom:1px solid rgba(29,44,70,.55);color:#dbe4f2;vertical-align:middle}
  table.ac-tbl td.ic{text-align:center;font-size:14px}
  table.ac-tbl td.mono{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;color:#9fb0c8}
  table.ac-tbl td.norm{font-size:11.5px;color:#22d3ee}
  .sevtag{font-weight:700}
  .ac-foot{color:#64748b;font-size:11.5px;margin-top:6px}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    """<div class="ac-head"><div class="logo">🛡️</div>
       <div><div class="eyebrow">DP Cyber Consulting · Policy-as-Code</div>
       <h1>AuditCraft <span style="color:#ff7a2f">GRC</span></h1>
       <div class="sub">Audit de conformité hybride — technique × normatif (ISO 27001 / RGPD), 100 % hors-ligne.</div></div></div>""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ audit
def run_audit_animated() -> engine.AuditResult:
    """Exécute l'audit et affiche une barre de progression (feedback COMEX)."""
    bar = st.progress(0, text="Initialisation de l'audit…")
    result = engine.run_audit(RULES_PATH, TARGET_DIR)
    total = max(len(result.controls), 1)
    for i, control in enumerate(result.controls, start=1):
        time.sleep(0.15)
        bar.progress(i / total, text=f"Évaluation · {control.rule_id} — {control.title}")
    bar.empty()
    return result


with st.sidebar:
    st.markdown("### ⚙️ Audit")
    st.caption(f"**Cible :** `{TARGET_DIR}`")
    st.caption(f"**Référentiel :** `{RULES_PATH.name}`")
    st.caption("Lecture seule · analyse hors-ligne · aucun scan réseau.")
    relance = st.button("▶  Lancer / relancer l'audit", type="primary", use_container_width=True)

# Lance au premier chargement, ou à la demande.
if relance or "result" not in st.session_state:
    try:
        st.session_state.result = run_audit_animated()
    except Exception as exc:  # cible/référentiel introuvable -> message clair, pas de crash
        st.error(f"Échec de l'audit : {exc}")
        st.stop()

result: engine.AuditResult = st.session_state.result


# ------------------------------------------------------------------ dashboard
score = result.score
band = result.band
band_color = "#33d69f" if band == "Maîtrisée" else "#f2c14e" if band == "À surveiller" else "#f0455f"

gauge = f"""
<div class="ac-gauge"><div class="ring" style="background:conic-gradient({band_color} {score*3.6}deg,#1d2c46 0)">
  <div class="hole"><div class="num">{score}<span>%</span></div>
  <div class="bd" style="color:{band_color}">{band}</div></div></div></div>"""

kpis = "".join([
    f'<div class="ac-kpi"><div class="v" style="color:#f0455f">{result.critical_count}</div><div class="l">Failles critiques</div><div class="s">à traiter en priorité</div></div>',
    f'<div class="ac-kpi"><div class="v" style="color:#ff8a3d">{len(result.gaps)}</div><div class="l">Écarts identifiés</div><div class="s">non-conformités</div></div>',
    f'<div class="ac-kpi"><div class="v" style="color:#33d69f">{len(result.compliant)}/{len(result.evaluated)}</div><div class="l">Contrôles conformes</div><div class="s">sur {len(result.controls)} règles</div></div>',
])
st.markdown(f'<div class="ac-grid">{gauge}{kpis}</div>', unsafe_allow_html=True)

# --- table mapping technique -> normatif ---
st.subheader("Cartographie conformité — écart technique × impact normatif")
rows = []
for c in result.controls:
    icon = STATUS_ICON.get(c.status, "⚪")
    sev_color = SEV_COLOR.get(c.severity, "#9fb0c8")
    norm = html.escape(c.frameworks[0]) if c.frameworks else "—"
    if c.status == NON_COMPLIANT:
        ecart = html.escape(f"{c.key} = {c.actual}  (attendu : {c.expected})")
    elif c.status == COMPLIANT:
        ecart = "conforme"
    else:
        ecart = "non applicable"
    rows.append(
        f"<tr><td class='ic'>{icon}</td>"
        f"<td><span class='sevtag' style='color:{sev_color}'>{c.severity}</span></td>"
        f"<td>{html.escape(c.title)}</td>"
        f"<td class='mono'>{ecart}</td>"
        f"<td class='norm'>{norm}</td></tr>"
    )
st.markdown(
    "<table class='ac-tbl'><tr><th>Statut</th><th>Sévérité</th><th>Contrôle</th>"
    "<th>Écart constaté</th><th>Référentiel (extrait)</th></tr>" + "".join(rows) + "</table>",
    unsafe_allow_html=True,
)
st.markdown("<div class='ac-foot'>🟢 conforme · 🔴 non conforme · ⚪ non applicable</div>", unsafe_allow_html=True)

# --- écarts détaillés (plan d'action) ---
gaps = result.gaps_sorted()
if gaps:
    st.subheader(f"Plan d'action — {len(gaps)} écart(s) à corriger")
    for c in gaps:
        with st.expander(f"{STATUS_ICON[NON_COMPLIANT]}  [{c.severity}] {c.title}  ·  {c.rule_id}"):
            st.markdown(f"**Constat (preuve) :** `{c.evidence}`")
            st.markdown(f"**Attendu :** `{c.expected}`  —  **Observé :** `{c.actual}`")
            st.markdown(f"**Risque EBIOS RM (gravité {c.ebios_gravity}/4) :** {c.ebios_event}")
            st.markdown("**Exigences normatives :**")
            for fw in c.frameworks:
                st.markdown(f"- {fw}")
            st.success(f"**Recommandation :** {c.recommendation}")
            st.caption(c.rationale)
else:
    st.success("Aucun écart : la configuration est conforme au référentiel. ✅")

# --- export ---
st.divider()
report_md = reporter.build_markdown(result)
st.download_button(
    "⬇  Télécharger le rapport COMEX (Markdown)",
    data=report_md,
    file_name="rapport_auditcraft_grc.md",
    mime="text/markdown",
    type="primary",
)
with st.expander("Aperçu du rapport"):
    st.markdown(report_md)
