from __future__ import annotations

"""Render a ProofArtifact as a self-contained HTML 'warrant card'.

Cockpit principle: *every surface shows its warrant.* This turns a governed
claim (see ``proofs.ProofArtifact`` / ``segment.release_to_proof_artifact``) into
a human-readable card whose colour encodes the ``epistemicLevel`` using the
Stardust palette. Stdlib-only string templating, fully inline CSS, **no external
requests** (no CDN/webfont) — the page makes zero network calls on render.
"""

import html
import json
from typing import Any, Dict

# Stardust epistemicLevel palette.
_LEVEL_COLOR = {
    "proved": "#4FD1C5",
    "bounded": "#63A6F5",
    "empirical": "#B79CF0",
    "synthetic": "#E5B94E",
    "speculative": "#E88B5A",
    "rejected": "#E05A64",
    "": "#8A949E",
}

_STATUS_COLOR = {"PROVED": "#4FD1C5", "INCONCLUSIVE": "#E5B94E", "VIOLATION": "#E05A64"}


def _esc(v: Any) -> str:
    return html.escape(str(v), quote=True)


def _rows(d: Dict[str, Any]) -> str:
    out = []
    for k in sorted(d):
        v = d[k]
        if isinstance(v, (dict, list)):
            v = json.dumps(v, sort_keys=True)
        out.append(f'<tr><td class="k">{_esc(k)}</td><td class="v">{_esc(v)}</td></tr>')
    return "".join(out) or '<tr><td class="v" colspan="2">—</td></tr>'


def render_warrant_card(artifact: Dict[str, Any]) -> str:
    """Return a complete, self-contained HTML document for one ProofArtifact."""
    claim = _esc(artifact.get("claim", "—"))
    status = str(artifact.get("status", ""))
    level = str(artifact.get("epistemicLevel", artifact.get("epistemic_level", "")))
    level_color = _LEVEL_COLOR.get(level, "#8A949E")
    status_color = _STATUS_COLOR.get(status, "#8A949E")

    precision = artifact.get("precision", {}) or {}
    witnesses = artifact.get("witnesses", {}) or {}
    violations = artifact.get("violations", []) or []

    warrant_rows = _rows(precision)
    prime_rows = _rows(witnesses.get("counts_by_prime", {}))
    realm_rows = _rows(witnesses.get("counts_by_realm", {}))
    inputs_rows = _rows(artifact.get("inputs", {}) or {})

    viol_html = ""
    if violations:
        items = "".join(f"<li>{_esc(json.dumps(v, sort_keys=True))}</li>" for v in violations)
        viol_html = f'<section><h2>Refusal / violations</h2><ul class="viol">{items}</ul></section>'

    level_badge = (
        f'<span class="badge" style="color:{level_color};border-color:{level_color}">'
        f'epistemicLevel: {_esc(level or "unspecified")}</span>'
    )
    status_badge = (
        f'<span class="badge" style="color:{status_color};border-color:{status_color}">'
        f'{_esc(status or "—")}</span>'
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Warrant — {claim}</title>
<style>
  :root {{ --ink:#0E1114; --panel:#161A1F; --rule:#2B333C; --text:#E4E8EC; --muted:#8A949E; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--ink); color:var(--text);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.5; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:32px 20px 64px; }}
  .eyebrow {{ font-family:ui-monospace,Menlo,monospace; font-size:11px; letter-spacing:.14em;
    text-transform:uppercase; color:var(--muted); margin:0 0 10px; }}
  h1 {{ font-size:26px; letter-spacing:-.02em; margin:0 0 14px; }}
  .badges {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:24px; }}
  .badge {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; padding:5px 10px;
    border:1px solid; border-radius:3px; background:transparent; }}
  section {{ background:var(--panel); border:1px solid var(--rule); border-radius:4px;
    padding:14px 16px; margin-bottom:16px; }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
    margin:0 0 10px; font-weight:600; }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
  td {{ padding:5px 8px; border-bottom:1px solid var(--rule); vertical-align:top; }}
  td.k {{ font-family:ui-monospace,Menlo,monospace; color:var(--muted); width:42%; word-break:break-word; }}
  td.v {{ font-variant-numeric:tabular-nums; word-break:break-word; }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:640px) {{ .cols {{ grid-template-columns:1fr; }} }}
  ul.viol {{ margin:0; padding-left:18px; font-family:ui-monospace,Menlo,monospace; font-size:12.5px; }}
</style></head>
<body><div class="wrap">
  <p class="eyebrow">SocioProphet · Governed Claim · Warrant</p>
  <h1>{claim}</h1>
  <div class="badges">{level_badge}{status_badge}</div>
  <section><h2>Warrant (privacy / DP parameters)</h2><table>{warrant_rows}</table></section>
  <div class="cols">
    <section><h2>Counts by prime</h2><table>{prime_rows}</table></section>
    <section><h2>Counts by realm</h2><table>{realm_rows}</table></section>
  </div>
  <section><h2>Inputs</h2><table>{inputs_rows}</table></section>
  {viol_html}
</div></body></html>
"""
