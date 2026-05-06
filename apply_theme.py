"""
Apply Bloomberg Terminal dark theme to main.py
Replaces: CSS variables, chart colors, inline styles in benchmark section
"""
import re

FILE = "src/main.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# ============================================================
# 1. Replace the entire <style>...</style> block
# ============================================================
NEW_CSS = r'''  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0a0a;
      --panel: #111111;
      --panel-2: #1a1a1a;
      --text: #e8e8e8;
      --muted: #777777;
      --accent: #ffffff;
      --accent-2: #cccccc;
      --border: #2a2a2a;
      --soft: #161616;
      --danger: #ff4444;
      --green: #00d26a;
      --red: #ff3b3b;
      --shadow: 0 4px 30px rgba(0,0,0,0.5);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text);
      background: var(--bg);
      -webkit-font-smoothing: antialiased;
    }
    .container { max-width: 1280px; margin: 0 auto; padding: 24px 20px 60px; }
    .hero {
      background: linear-gradient(160deg, #111 0%, #0a0a0a 50%, #111 100%);
      color: white;
      border-radius: 2px;
      padding: 40px 36px;
      border: 1px solid var(--border);
      overflow: hidden;
      position: relative;
    }
    .hero::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    }
    .eyebrow { text-transform: uppercase; letter-spacing: 0.25em; font-size: 11px; color: var(--muted); margin-bottom: 12px; font-family: 'JetBrains Mono', monospace; }
    h1 { margin: 0 0 12px; font-size: clamp(28px, 3.5vw, 42px); font-weight: 900; letter-spacing: -0.02em; }
    .hero p { margin: 0; max-width: 900px; line-height: 1.7; font-size: 15px; color: #999; }
    .toolbar { margin-top: 24px; display: flex; flex-wrap: wrap; gap: 14px; align-items: end; }
    .field {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 14px 16px;
      min-width: 200px;
    }
    .field label { display: block; font-size: 10px; color: var(--muted); margin-bottom: 6px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'JetBrains Mono', monospace; }
    .field select {
      width: 100%;
      border: 0;
      outline: none;
      background: rgba(255,255,255,0.06);
      color: white;
      font-size: 13px;
      padding: 10px;
      border-radius: 2px;
      cursor: pointer;
      font-family: 'Inter', sans-serif;
    }
    .field select option { background: #111; color: white; }
    .field select optgroup { background: #111; color: #999; font-weight: 700; }
    .button {
      border: 1px solid #fff;
      background: #ffffff;
      color: #000000;
      border-radius: 2px;
      font-size: 14px;
      font-weight: 800;
      padding: 14px 28px;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      transition: all 0.2s ease;
      font-family: 'Inter', sans-serif;
    }
    .button:hover { background: #000; color: #fff; border-color: #fff; }
    .notice, .card, .section, .table-wrap {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 2px;
    }
    .notice { margin-top: 18px; padding: 20px 24px; color: #aaa; line-height: 1.7; font-size: 14px; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin-top: 18px; background: var(--border); border: 1px solid var(--border); border-radius: 2px; overflow: hidden; }
    .card { padding: 20px; border-top: none; border: none; border-radius: 0; background: var(--panel); }
    .card .label { color: var(--muted); font-size: 10px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'JetBrains Mono', monospace; }
    .card .value { font-size: 24px; font-weight: 800; line-height: 1.1; color: #fff; font-family: 'JetBrains Mono', monospace; }
    .section { margin-top: 18px; padding: 28px; }
    .section h2 { margin: 0 0 14px; font-size: 18px; font-weight: 800; color: #fff; text-transform: uppercase; letter-spacing: 0.05em; }
    .section p, .section li { line-height: 1.75; color: #aaa; font-size: 14px; }
    .section ul { margin: 8px 0 0 18px; padding: 0; }
    .section li::marker { color: var(--muted); }
    .split { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 20px; align-items: start; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    .chip { background: transparent; border: 1px solid var(--border); padding: 8px 14px; border-radius: 2px; color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'JetBrains Mono', monospace; }
    .ui-icon { display: inline-flex; width: 16px; height: 16px; margin-right: 8px; vertical-align: -2px; color: var(--muted); }
    .ui-icon svg { width: 100%; height: 100%; display: block; }
    .chart { margin-top: 16px; overflow: hidden; border: 1px solid var(--border); border-radius: 2px; background: var(--panel); }
    .chart img { display: block; width: 100%; height: auto; }
    .table-wrap { margin-top: 16px; overflow: hidden; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
    th { background: var(--soft); font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace; }
    td { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #ccc; }
    tbody tr:nth-child(even) { background: rgba(255,255,255,0.02); }
    tbody tr:hover { background: rgba(255,255,255,0.04); }
    .footer-note { color: var(--muted); font-size: 12px; margin-top: 8px; font-family: 'JetBrains Mono', monospace; }
    .error { margin-top: 18px; padding: 14px 18px; background: rgba(255,60,60,0.08); color: var(--danger); border-radius: 2px; border: 1px solid rgba(255,60,60,0.2); }
    .cfg-panel { background:var(--panel); border:1px solid var(--border); border-radius:2px; margin-top:18px; padding:28px; }
    .cfg-panel h3 { margin:0 0 14px; font-size:13px; color:#fff; border-bottom:1px solid var(--border); padding-bottom:10px; text-transform:uppercase; letter-spacing:0.08em; font-weight:800; }
    .cfg-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; margin-bottom:18px; }
    .cfg-f label { display:block; font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; margin-bottom:4px; font-family:'JetBrains Mono',monospace; }
    .cfg-f input,.cfg-f select { width:100%; padding:9px 10px; border:1px solid var(--border); border-radius:2px; font-size:13px; background:var(--soft); color:var(--text); outline:none; }
    .cfg-f input:focus,.cfg-f select:focus { border-color:#555; box-shadow:0 0 0 2px rgba(255,255,255,.05); }
    .rt { width:100%; border-collapse:collapse; margin-bottom:8px; }
    .rt th { background:var(--soft); font-size:10px; padding:8px; text-align:left; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em; font-family:'JetBrains Mono',monospace; }
    .rt td { padding:5px 6px; border-bottom:1px solid var(--border); }
    .rt input { width:100%; padding:7px; border:1px solid var(--border); border-radius:2px; font-size:12px; background:var(--soft); color:var(--text); }
    .rt input[type=checkbox] { width:auto; accent-color:#fff; }
    .ba,.br { border:none; padding:6px 14px; border-radius:2px; font-size:11px; font-weight:700; cursor:pointer; text-transform:uppercase; letter-spacing:0.05em; }
    .ba { background:#fff; color:#000; }
    .ba:hover { background:#ccc; }
    .br { background:#333; color:#ff4444; }
    .br:hover { background:#444; }
    .cfg-chk { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
    .cfg-chk input[type=checkbox] { width:16px; height:16px; accent-color:#fff; }
    .cfg-chk label { font-size:13px; margin:0; color:#aaa; }
    .cfg-sec { margin-bottom:18px; }
    strong { color: #fff; }
    @media (max-width: 900px) {
      .grid, .split { grid-template-columns: 1fr; }
      .hero { padding: 24px; }
      .button { width: 100%; }
      .cfg-grid { grid-template-columns: 1fr; }
    }
  </style>'''

content = re.sub(
    r'  <style>.*?</style>',
    NEW_CSS,
    content,
    count=1,
    flags=re.DOTALL,
)

# ============================================================
# 2. Replace chart colors in build_charts (Project 1)
# ============================================================
# Price chart
content = content.replace(
    'color="#154360"',
    'color="#ffffff"',
    1,  # first occurrence only (price chart line)
)

# Wealth chart lines
content = content.replace(
    'label="Total Money Put In", color="#7f8c8d", linewidth=2',
    'label="Total Money Put In", color="#555555", linewidth=1.5, linestyle="--"',
)
content = content.replace(
    'label="Portfolio Value", color="#0b5345", linewidth=2.4',
    'label="Portfolio Value", color="#ffffff", linewidth=2',
)

# Drawdown chart
content = content.replace(
    'color="#c0392b", alpha=0.25)',
    'color="#ffffff", alpha=0.08)',
    1,
)
content = content.replace(
    'color="#922b21", linewidth=1.5)',
    'color="#aaaaaa", linewidth=1.2)',
    1,
)

# ============================================================
# 3. Replace chart colors in build_charts_project2
# ============================================================
# Growth chart
content = content.replace(
    'alpha=0.15, color="#7f8c8d"',
    'alpha=0.05, color="#555555"',
)
content = content.replace(
    'label="Money You Put In", color="#7f8c8d", linewidth=2, linestyle="--"',
    'label="Money You Put In", color="#555555", linewidth=1.5, linestyle="--"',
)
content = content.replace(
    'alpha=0.12, color="#0b5345"',
    'alpha=0.08, color="#ffffff"',
)
content = content.replace(
    'label="What It Became", color="#0b5345", linewidth=2.5',
    'label="What It Became", color="#ffffff", linewidth=2',
)

# Growth chart title/labels
content = content.replace(
    'fontsize=14, fontweight="bold", color="#154360", pad=12',
    'fontsize=14, fontweight="bold", color="#ffffff", pad=12',
)
content = content.replace(
    'fontsize=11, color="#5f6b76"',
    'fontsize=11, color="#777777"',
)

# Equity vs Bond chart
content = content.replace(
    'alpha=0.3, color="#0b5345"',
    'alpha=0.1, color="#ffffff"',
)
content = content.replace(
    'alpha=0.3, color="#2e86c1"',
    'alpha=0.08, color="#666666"',
)
content = content.replace(
    'color="#0b5345", linewidth=1.8',
    'color="#ffffff", linewidth=1.5',
)
content = content.replace(
    'color="#2e86c1", linewidth=1.8',
    'color="#666666", linewidth=1.5',
)

# Drawdown chart (project2)
content = content.replace(
    'color="#c0392b", alpha=0.2)',
    'color="#888888", alpha=0.1)',
)
content = content.replace(
    'color="#922b21", linewidth=1.2)',
    'color="#aaaaaa", linewidth=1)',
)

# Benchmark vs Strategy chart
content = content.replace(
    'label="Our Strategy (Stocks + Bonds)", color="#0b5345", linewidth=2.5',
    'label="Our Strategy (Stocks + Bonds)", color="#ffffff", linewidth=2',
)
content = content.replace(
    'label="100% Stocks (Benchmark)", color="#c0392b", linewidth=2.5',
    'label="100% Stocks (Benchmark)", color="#666666", linewidth=2',
)
content = content.replace(
    'label="Money You Put In", color="#7f8c8d", linewidth=2, linestyle="--"',
    'label="Money You Put In", color="#444444", linewidth=1.5, linestyle="--"',
)

# Drawdown protection chart
content = content.replace(
    'color="#0b5345", alpha=0.2, label="Our Strategy Drawdown"',
    'color="#ffffff", alpha=0.06, label="Our Strategy Drawdown"',
)
content = content.replace(
    'color="#0b5345", linewidth=2)',
    'color="#ffffff", linewidth=1.5)',
)
content = content.replace(
    'color="#c0392b", alpha=0.2, label="100% Stock Drawdown"',
    'color="#666666", alpha=0.08, label="100% Stock Drawdown"',
)
content = content.replace(
    'color="#c0392b", linewidth=2)',
    'color="#888888", linewidth=1.5)',
)

# Drawdown benefit chart
content = content.replace(
    "color=\"#0b5345\", alpha=0.3, label=\"Strategy Better\"",
    "color=\"#ffffff\", alpha=0.1, label=\"Strategy Better\"",
)
content = content.replace(
    "color=\"#c0392b\", alpha=0.3, label=\"Benchmark Better\"",
    "color=\"#666666\", alpha=0.1, label=\"Benchmark Better\"",
)
content = content.replace(
    'color="#154360", linewidth=1.5)',
    'color="#aaaaaa", linewidth=1.2)',
)
content = content.replace(
    'color="#333333", linestyle="-", linewidth=0.8',
    'color="#555555", linestyle="-", linewidth=0.6',
)

# ============================================================
# 4. Make all matplotlib charts have dark backgrounds
# ============================================================
# Add dark style to figure_to_base64
old_fig_func = '''def figure_to_base64(figure) -> str:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight", dpi=160)'''

new_fig_func = '''def figure_to_base64(figure) -> str:
    buffer = io.BytesIO()
    figure.patch.set_facecolor('#111111')
    for ax in figure.get_axes():
        ax.set_facecolor('#111111')
        ax.tick_params(colors='#777777', labelsize=9)
        ax.xaxis.label.set_color('#777777')
        ax.yaxis.label.set_color('#777777')
        ax.title.set_color('#ffffff')
        for spine in ax.spines.values():
            spine.set_color('#2a2a2a')
        ax.grid(True, alpha=0.08, color='#ffffff')
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor('#1a1a1a')
            legend.get_frame().set_edgecolor('#2a2a2a')
            for text in legend.get_texts():
                text.set_color('#aaaaaa')
    figure.savefig(buffer, format="png", bbox_inches="tight", dpi=160, facecolor='#111111')'''

content = content.replace(old_fig_func, new_fig_func)

# ============================================================
# 5. Replace inline styles in benchmark section
# ============================================================
# Benchmark section wrapper
content = content.replace(
    'style="margin-top: 32px; background: linear-gradient(135deg, #fdfefe 0%, #f4f6f7 100%); padding: 32px; border-radius: 12px; border: 1px solid #d5dbdb;"',
    'style="margin-top: 24px; background: #111; padding: 32px; border-radius: 2px; border: 1px solid #2a2a2a;"',
)
content = content.replace(
    'style="margin-top:0; color: #154360;"',
    'style="margin-top:0; color: #fff; text-transform:uppercase; letter-spacing:0.05em; font-size:18px;"',
)
content = content.replace(
    'style="margin-bottom: 24px;"',
    'style="margin-bottom: 24px; color: #888;"',
)

# Benchmark cards
content = content.replace(
    'style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #c0392b; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"',
    'style="background: #1a1a1a; padding: 20px; border-radius: 2px; border-left: 2px solid #666; border: 1px solid #2a2a2a;"',
)
content = content.replace(
    'style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #f39c12; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"',
    'style="background: #1a1a1a; padding: 20px; border-radius: 2px; border-left: 2px solid #888; border: 1px solid #2a2a2a;"',
)
content = content.replace(
    'style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"',
    'style="background: #1a1a1a; padding: 20px; border-radius: 2px; border-left: 2px solid #aaa; border: 1px solid #2a2a2a;"',
)

# Benchmark card labels
content = content.replace(
    'style="font-size: 13px; font-weight: 600; color: #7f8c8d; text-transform: uppercase; margin-bottom: 8px;"',
    'style="font-size: 10px; font-weight: 700; color: #666; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.08em; font-family: JetBrains Mono, monospace;"',
)

# Benchmark card text
content = content.replace(
    'style="margin: 0; font-size: 15px; line-height: 1.5;"',
    'style="margin: 0; font-size: 14px; line-height: 1.6; color: #aaa;"',
)

# Kitchen table quote styling
content = content.replace(
    'style="font-style: italic; line-height: 1.8; color: #154360;"',
    'style="font-style: italic; line-height: 1.8; color: #888; border-left: 2px solid #333; padding-left: 20px;"',
)

# Investment period label
content = content.replace(
    'style="margin-top: 12px; font-weight: 700; color: #154360;"',
    'style="margin-top: 12px; font-weight: 700; color: #ccc;"',
)

# Dataset file input styling
content = content.replace(
    'style="width:100%;color:white;background:rgba(255,255,255,0.08);padding:10px;border-radius:8px;border:0;"',
    'style="width:100%;color:#ccc;background:rgba(255,255,255,0.04);padding:10px;border-radius:2px;border:1px solid #2a2a2a;font-size:12px;"',
)

# ============================================================
# 6. Update the page title
# ============================================================
content = content.replace(
    '<title>Project 1 | NIFTY SIP Investor Report</title>',
    '<title>NIFTY Terminal | Quantitative Investment Analysis</title>',
)

# ============================================================
# Write back
# ============================================================
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Bloomberg terminal theme applied successfully!")
print("  - CSS variables: dark monochrome palette")
print("  - Typography: Inter + JetBrains Mono")
print("  - Charts: dark background, white/gray lines")
print("  - Inline styles: dark benchmark cards")
print("  - All borders: sharp 2px radius")
