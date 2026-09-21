from __future__ import annotations

from pathlib import Path


def write_preview(job_dir: Path, highlights: dict, meta: dict, output_mp4: Path | None) -> Path:
    rows = []
    for i, clip in enumerate(highlights.get("clips") or [], start=1):
        role = "ХУК (первый кадр)" if clip.get("role") == "hook" else "пик"
        keep = "да" if clip.get("keep", True) else "нет"
        rows.append(
            "<tr>"
            f"<td>{i}</td>"
            f"<td>{role}</td>"
            f"<td>{clip['start']:.1f} – {clip['end']:.1f} сек</td>"
            f"<td>{clip.get('duration', clip['end'] - clip['start']):.1f} сек</td>"
            f"<td>{keep}</td>"
            "</tr>"
        )
    out_line = (
        f"<p><b>Готовый ролик:</b> {output_mp4}</p>"
        if output_mp4
        else "<p>Ролик ещё не собран.</p>"
    )
    cta = (meta.get("subscribe_line") or "").strip()
    cta_safe = (
        cta.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    cta_block = (
        f"<div class=\"hint\"><p><b>Зачем подписываться (в описание):</b><br>{cta_safe}</p></div>"
        if cta_safe
        else ""
    )
    html = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Хайлайты</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; max-width: 720px; margin: 40px auto; color: #111; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; }}
th {{ background: #111; color: #fff; }}
.hint {{ background: #f4f4f1; padding: 12px 16px; border-radius: 10px; }}
</style></head>
<body>
<h1>Черновик шортса</h1>
<p>{meta.get('hook') or 'WOW'} — {meta.get('athletes') or ''} — {meta.get('event') or ''}</p>
<p>Исходник: {highlights.get('source')}<br>
Длина исходника: {highlights.get('duration_source')} сек · сборка: {highlights.get('total_sec')} сек</p>
<table>
<tr><th>#</th><th>Роль</th><th>Таймкод</th><th>Длина</th><th>Берём</th></tr>
{''.join(rows)}
</table>
{out_line}
{cta_block}
<div class="hint">
<p>Если кусок лишний — откройте файл <b>highlights.json</b> в этой же папке, поставьте <b>"keep": false</b> и снова запустите сборку.</p>
</div>
</body></html>
"""
    path = job_dir / "просмотр.html"
    path.write_text(html, encoding="utf-8")
    return path
