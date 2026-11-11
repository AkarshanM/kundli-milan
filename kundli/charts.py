"""South Indian style chart (fixed signs, 4 x 4 grid) as self-contained HTML.

Layout (sign index 0 = Mesha):
    Meena    Mesha     Vrishabha  Mithuna
    Kumbha   [ centre title ]     Karka
    Makara   [               ]    Simha
    Dhanu    Vrishchika  Tula     Kanya
"""
from __future__ import annotations

import html

# (row, col) of each sign in the 4x4 grid
SIGN_CELL = {11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3),
             10: (1, 0), 3: (1, 3),
             9: (2, 0), 4: (2, 3),
             8: (3, 0), 7: (3, 1), 6: (3, 2), 5: (3, 3)}


def south_indian_chart(contents: dict[int, list[str]], lagna_sign: int,
                       sign_labels: list[str], title: str, subtitle: str = "") -> str:
    """contents: sign index -> list of short labels (planets) to show.
    The Lagna's sign is marked with a diagonal stroke, the traditional
    South Indian convention."""
    cells = []
    for sign, (r, c) in SIGN_CELL.items():
        items = "".join(f"<span>{html.escape(x)}</span>" for x in contents.get(sign, []))
        lagna = " lagna" if sign == lagna_sign else ""
        cells.append(
            f'<div class="kc-cell{lagna}" style="grid-row:{r + 1};grid-column:{c + 1}">'
            f'<div class="kc-sign">{html.escape(sign_labels[sign])}</div>'
            f'<div class="kc-items">{items}</div></div>')
    centre = (f'<div class="kc-centre"><div class="kc-title">{html.escape(title)}</div>'
              f'<div class="kc-sub">{html.escape(subtitle)}</div></div>')
    return f"""
<style>
.kc-grid {{ display:grid; grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(4,1fr);
  aspect-ratio:1/1; max-width:420px; width:100%; border:2px solid rgba(128,128,128,.7);
  font-family:inherit; color:inherit; margin:0 auto; }}
.kc-cell {{ position:relative; border:1px solid rgba(128,128,128,.55); padding:4px 5px;
  overflow:hidden; display:flex; flex-direction:column; min-width:0; }}
.kc-cell.lagna {{ background:linear-gradient(to top right, transparent calc(50% - 1px),
  rgba(200,120,40,.65), transparent calc(50% + 1px)); background-size:22px 22px;
  background-repeat:no-repeat; background-position:top left; }}
.kc-sign {{ font-size:10px; opacity:.6; text-align:right; line-height:1.1; }}
.kc-items {{ display:flex; flex-wrap:wrap; gap:2px 6px; font-size:13px; font-weight:600;
  line-height:1.25; margin-top:2px; }}
.kc-centre {{ grid-row:2 / span 2; grid-column:2 / span 2; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; padding:6px; }}
.kc-title {{ font-size:16px; font-weight:700; }}
.kc-sub {{ font-size:11px; opacity:.7; margin-top:4px; }}
</style>
<div class="kc-grid">{''.join(cells)}{centre}</div>
"""
