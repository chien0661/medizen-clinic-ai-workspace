#!/usr/bin/env python
"""
MediZen Modern — Stitch HTML Export Script
Downloads HTML for all 63 screens and builds index.html
"""

import json
import os
import sys
import re
import time
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

JFILE = r'C:\Users\chiendv\.claude\projects\E--MyProject-clinic-cms-workspace-claude-workspace\ea1403c6-aca7-43bf-ab59-7ac6983553c1\tool-results\mcp-stitch-list_screens-1777649929669.txt'
OUT_DIR = r'E:\MyProject\clinic-cms-workspace\claude-workspace\docs\design\medizen-modern\html-export'
SCREENS_DIR = os.path.join(OUT_DIR, 'screens')

os.makedirs(SCREENS_DIR, exist_ok=True)

# ── Vietnamese slug helper ──────────────────────────────────────────────────
def vi_slug(text):
    """Convert Vietnamese text to ASCII slug."""
    replacements = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a',
        'ă':'a','ắ':'a','ặ':'a','ằ':'a','ẳ':'a','ẵ':'a',
        'â':'a','ấ':'a','ậ':'a','ầ':'a','ẩ':'a','ẫ':'a',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e',
        'ê':'e','ế':'e','ệ':'e','ề':'e','ể':'e','ễ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o',
        'ô':'o','ố':'o','ộ':'o','ồ':'o','ổ':'o','ỗ':'o',
        'ơ':'o','ớ':'o','ợ':'o','ờ':'o','ở':'o','ỡ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u',
        'ư':'u','ứ':'u','ự':'u','ừ':'u','ử':'u','ữ':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y',
        'đ':'d',
        'À':'a','Á':'a','Ả':'a','Ã':'a','Ạ':'a',
        'Ă':'a','Ắ':'a','Ặ':'a','Ằ':'a','Ẳ':'a','Ẵ':'a',
        'Â':'a','Ấ':'a','Ậ':'a','Ầ':'a','Ẩ':'a','Ẫ':'a',
        'È':'e','É':'e','Ẻ':'e','Ẽ':'e','Ẹ':'e',
        'Ê':'e','Ế':'e','Ệ':'e','Ề':'e','Ể':'e','Ễ':'e',
        'Ì':'i','Í':'i','Ỉ':'i','Ĩ':'i','Ị':'i',
        'Ò':'o','Ó':'o','Ỏ':'o','Õ':'o','Ọ':'o',
        'Ô':'o','Ố':'o','Ộ':'o','Ồ':'o','Ổ':'o','Ỗ':'o',
        'Ơ':'o','Ớ':'o','Ợ':'o','Ờ':'o','Ở':'o','Ỡ':'o',
        'Ù':'u','Ú':'u','Ủ':'u','Ũ':'u','Ụ':'u',
        'Ư':'u','Ứ':'u','Ự':'u','Ừ':'u','Ử':'u','Ữ':'u',
        'Ỳ':'y','Ý':'y','Ỷ':'y','Ỹ':'y','Ỵ':'y',
        'Đ':'d',
    }
    result = ''
    for ch in text:
        result += replacements.get(ch, ch)
    result = result.lower()
    result = re.sub(r'[^a-z0-9]+', '-', result)
    result = result.strip('-')
    return result

# ── Load screens ────────────────────────────────────────────────────────────
with open(JFILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

screens = data['screens']
print(f"Total screens in JSON: {len(screens)}")

# Build unique slugs (handle duplicates by appending screen ID suffix)
slug_counter = Counter()
screen_info = []

for s in screens:
    title = s.get('title', '') or s.get('displayName', '') or 'screen'
    # Remove " — MediZen" suffix for cleaner slug
    clean_title = re.sub(r'\s*[—-]\s*MediZen.*$', '', title).strip()
    base_slug = vi_slug(clean_title) or 'screen'
    slug_counter[base_slug] += 1
    screen_id = s['name'].split('/')[-1]
    hc = s.get('htmlCode', {})
    url = hc.get('downloadUrl', '')
    screen_info.append({
        'title': title,
        'clean_title': clean_title,
        'base_slug': base_slug,
        'screen_id': screen_id,
        'name': s['name'],
        'url': url,
        'width': s.get('width', 1440),
        'height': s.get('height', 900),
        'deviceType': s.get('deviceType', 'DESKTOP'),
    })

# Re-assign slugs — deduplicate
slug_seen = Counter()
for info in screen_info:
    bs = info['base_slug']
    slug_seen[bs] += 1

slug_used = Counter()
for info in screen_info:
    bs = info['base_slug']
    if slug_counter[bs] > 1:
        slug_used[bs] += 1
        info['slug'] = f"{bs}-{slug_used[bs]}"
    else:
        info['slug'] = bs

# ── Group by category ────────────────────────────────────────────────────────
def categorize(title):
    t = title.lower()
    if any(x in t for x in ['đăng nhập', 'quên mật khẩu', 'mật khẩu', 'login', 'auth']):
        return 'Auth'
    if any(x in t for x in ['dashboard']):
        if 'bác sĩ' in t or 'doctor' in t: return 'Doctor'
        if 'dược' in t or 'pharmacy' in t: return 'Pharmacy'
        if 'điều dưỡng' in t: return 'Nursing'
        if 'lễ tân' in t or 'reception' in t: return 'Reception'
        if 'quản trị' in t or 'admin' in t: return 'Admin'
        if 'tổng quan' in t: return 'Dashboard'
        return 'Dashboard'
    if any(x in t for x in ['lịch hẹn', 'lịch', 'calendar', 'ca trực', 'quản lý lịch']):
        return 'Scheduling'
    if any(x in t for x in ['bệnh nhân', 'tiếp nhận', 'đăng ký', 'phòng chờ', 'hồ sơ']):
        return 'Patient'
    if any(x in t for x in ['khám', 'soap', 'chẩn đoán', 'sinh hiệu', 'cận lâm sàng', 'kê đơn', 'tóm tắt']):
        return 'Clinical'
    if any(x in t for x in ['dược', 'kho thuốc', 'danh mục thuốc', 'kiểm kê', 'nhập kho', 'cấp phát', 'hết hạn']):
        return 'Pharmacy'
    if any(x in t for x in ['thanh toán', 'hoá đơn', 'hóa đơn', 'công nợ', 'bảng giá', 'billing', 'ar aging']):
        return 'Billing'
    if any(x in t for x in ['bhyt', 'bảo hiểm']):
        return 'Insurance'
    if any(x in t for x in ['báo cáo', 'report']):
        return 'Reports'
    if any(x in t for x in ['cấu hình', 'tích hợp', 'bảo mật', 'phòng khám', 'vai trò', 'phân quyền', 'audit']):
        return 'Admin'
    if any(x in t for x in ['profile', 'cá nhân']):
        return 'Profile'
    if any(x in t for x in ['thông báo', 'notification']):
        return 'Notifications'
    if any(x in t for x in ['search', 'quick', 'clinic switcher']):
        return 'Global UI'
    return 'Other'

for info in screen_info:
    info['category'] = categorize(info['title'])

# ── Download HTML ────────────────────────────────────────────────────────────
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — MediZen</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* Screen meta info bar */
    #meta-bar {{
      position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
      background: #1e293b; color: #94a3b8; font-family: monospace;
      font-size: 11px; padding: 4px 12px; display: flex; gap: 16px;
      align-items: center;
    }}
    #meta-bar a {{ color: #60a5fa; text-decoration: none; }}
    body {{ padding-top: 28px; }}
    /* Inline CSS from Stitch */
    {inline_css}
  </style>
</head>
<body>
  <div id="meta-bar">
    <span><strong style="color:#f1f5f9">{title}</strong></span>
    <span>ID: {screen_id}</span>
    <span>{width}×{height} {device}</span>
    <a href="../index.html">← Index</a>
  </div>
  {screen_html}
</body>
</html>'''

results = []
failed = []

print(f"\nDownloading {len(screen_info)} screens...")
print("-" * 60)

for idx, info in enumerate(screen_info):
    slug = info['slug']
    title = info['title']
    url = info['url']
    out_path = os.path.join(SCREENS_DIR, f"{slug}.html")

    print(f"[{idx+1:2d}/{len(screen_info)}] {title[:55]}")

    if not url:
        print(f"  ⚠ No download URL — skipping")
        failed.append({'title': title, 'slug': slug, 'reason': 'No download URL'})
        info['status'] = 'failed'
        info['file'] = None
        continue

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_html = resp.read().decode('utf-8', errors='replace')

        # The downloaded content is already full HTML from Stitch
        # Extract <style> blocks if any to put in inline_css
        style_matches = re.findall(r'<style[^>]*>(.*?)</style>', raw_html, re.DOTALL)
        inline_css = '\n'.join(style_matches)

        # Extract <body> content
        body_match = re.search(r'<body[^>]*>(.*?)</body>', raw_html, re.DOTALL)
        if body_match:
            screen_html = body_match.group(1)
        else:
            screen_html = raw_html  # use as-is if no body tag

        # Write wrapped HTML
        wrapped = HTML_TEMPLATE.format(
            title=title.replace('{', '{{').replace('}', '}}'),
            screen_id=info['screen_id'],
            width=info['width'],
            height=info['height'],
            device=info['deviceType'],
            inline_css=inline_css,
            screen_html=screen_html,
        )

        with open(out_path, 'w', encoding='utf-8') as fout:
            fout.write(wrapped)

        file_size = os.path.getsize(out_path)
        print(f"  ✓ {slug}.html ({file_size//1024}KB)")
        info['status'] = 'ok'
        info['file'] = f"screens/{slug}.html"
        info['file_size'] = file_size
        results.append(info)

    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.reason}")
        failed.append({'title': title, 'slug': slug, 'reason': f'HTTP {e.code}: {e.reason}'})
        info['status'] = 'failed'
        info['file'] = None
    except urllib.error.URLError as e:
        print(f"  ✗ URL Error: {e.reason}")
        failed.append({'title': title, 'slug': slug, 'reason': str(e.reason)})
        info['status'] = 'failed'
        info['file'] = None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed.append({'title': title, 'slug': slug, 'reason': str(e)})
        info['status'] = 'failed'
        info['file'] = None

    # Small delay to be polite (not a Stitch MCP call, just HTTP download)
    time.sleep(0.3)

print(f"\n\nDone: {len(results)} OK, {len(failed)} FAILED")
print("=" * 60)

# ── Build index.html ─────────────────────────────────────────────────────────
from collections import defaultdict
by_category = defaultdict(list)
for info in screen_info:
    by_category[info['category']].append(info)

CATEGORY_ORDER = ['Auth', 'Dashboard', 'Reception', 'Patient', 'Clinical', 'Doctor', 'Nursing',
                  'Pharmacy', 'Billing', 'Insurance', 'Reports', 'Scheduling', 'Notifications',
                  'Profile', 'Admin', 'Global UI', 'Other']

cards_html = ''
for cat in CATEGORY_ORDER:
    items = by_category.get(cat, [])
    if not items:
        continue
    cards_html += f'''
    <div class="category-section" data-category="{cat}">
      <h2 class="text-xl font-bold text-slate-700 mb-4 mt-8 pb-2 border-b border-slate-200">
        {cat} <span class="text-sm font-normal text-slate-400">({len(items)} màn)</span>
      </h2>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
    '''
    for info in items:
        if info['status'] == 'ok':
            iframe_src = f"screens/{info['slug']}.html"
            link = f'<a href="{iframe_src}" class="block">'
            status_badge = '<span class="badge-ok">&#10003; OK</span>'
            w = int(info.get('width') or 1440)
            h = int(info.get('height') or 900)
            scale = round(180 / max(h, 1), 3)
            iframe_block = (
                '<div class="preview-container" style="height:180px;overflow:hidden;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;position:relative;">'
                f'<iframe src="{iframe_src}"'
                f' style="width:{w}px;height:{h}px;border:none;transform-origin:top left;transform:scale({scale});pointer-events:none;"'
                f' loading="lazy" title="{info[\"title\"]}"></iframe>'
                '</div>'
            )
        else:
            link = '<div'
            status_badge = '<span class="badge-fail">&#10007; FAILED</span>'
            iframe_block = '<div class="preview-container" style="height:180px;background:#fef2f2;display:flex;align-items:center;justify-content:center;border:1px solid #fecaca;border-radius:6px;color:#ef4444;font-size:12px;">Download failed</div>'

        clean_title = info['clean_title']
        screen_id_short = info['screen_id'][:12] + '...'
        card_link_open = f'<a href="screens/{info["slug"]}.html" class="card-link">' if info['status'] == 'ok' else '<div class="card-link-disabled">'
        card_link_close = '</a>' if info['status'] == 'ok' else '</div>'

        cards_html += f'''
        {card_link_open}
        <div class="screen-card bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow" data-title="{clean_title.lower()}">
          {iframe_block}
          <div class="p-3">
            <div class="font-medium text-slate-800 text-sm leading-tight mb-1">{clean_title}</div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-slate-400 font-mono">{screen_id_short}</span>
              {status_badge}
            </div>
          </div>
        </div>
        {card_link_close}
        '''
    cards_html += '</div></div>'

gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
total_ok = len(results)
total_fail = len(failed)
total_screens = len(screen_info)

index_html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MediZen Modern — Toàn bộ màn (Stitch project 2542650746708884228)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: 'Inter', sans-serif; background: #f8fafc; }}
    h1, h2 {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    .badge-ok {{ background:#dcfce7;color:#16a34a;font-size:10px;padding:2px 6px;border-radius:9999px;font-weight:600; }}
    .badge-fail {{ background:#fee2e2;color:#dc2626;font-size:10px;padding:2px 6px;border-radius:9999px;font-weight:600; }}
    .card-link {{ text-decoration:none;color:inherit;display:block; }}
    .card-link-disabled {{ color:inherit;display:block;opacity:0.6; }}
    .screen-card {{ cursor:pointer; }}
    .hidden-by-search {{ display:none!important; }}
  </style>
</head>
<body class="min-h-screen">
  <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">MediZen Modern</h1>
        <p class="text-sm text-slate-500 mt-0.5">Stitch project <code class="bg-slate-100 px-1 rounded">2542650746708884228</code> · {total_screens} màn · {total_ok} exported · {total_fail} failed</p>
      </div>
      <div class="flex gap-3 items-center">
        <input type="text" id="search" placeholder="Tìm màn..." oninput="filterScreens(this.value)"
          class="border border-slate-300 rounded-lg px-4 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500">
        <a href="https://stitch.withgoogle.com/projects/2542650746708884228" target="_blank"
          class="text-xs text-blue-600 hover:underline whitespace-nowrap">↗ Stitch Project</a>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-6 pb-16">
    {cards_html}
  </main>

  <footer class="bg-white border-t border-slate-200 py-6 mt-8">
    <div class="max-w-7xl mx-auto px-6 text-center text-sm text-slate-500">
      <p>Generated: {gen_time} · {total_ok}/{total_screens} screens exported successfully</p>
      <p class="mt-1">MediZen Modern UI Design — Clinic CMS Workspace</p>
    </div>
  </footer>

  <script>
    function filterScreens(query) {{
      const q = query.toLowerCase().trim();
      document.querySelectorAll('.screen-card').forEach(card => {{
        const title = card.getAttribute('data-title') || '';
        const parent = card.closest('.card-link, .card-link-disabled');
        const el = parent || card;
        if (!q || title.includes(q)) {{
          el.classList.remove('hidden-by-search');
        }} else {{
          el.classList.add('hidden-by-search');
        }}
      }});
      // Hide empty category sections
      document.querySelectorAll('.category-section').forEach(sec => {{
        const visible = sec.querySelectorAll('.screen-card:not(.hidden-by-search)').length;
        sec.style.display = visible ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>'''

index_path = os.path.join(OUT_DIR, 'index.html')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_html)
print(f"\n✓ index.html written: {os.path.getsize(index_path)//1024}KB")

# ── Export report ─────────────────────────────────────────────────────────────
report_path = os.path.join(OUT_DIR, 'EXPORT_REPORT.md')
total_size = sum(info.get('file_size', 0) for info in screen_info if info.get('file_size'))

report_lines = [
    f"# MediZen Modern — HTML Export Report",
    f"",
    f"**Generated:** {gen_time}",
    f"**Project:** Stitch 2542650746708884228",
    f"",
    f"## Summary",
    f"",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| Total screens in list | {total_screens} |",
    f"| Exported successfully | {total_ok} |",
    f"| Failed | {total_fail} |",
    f"| Total HTML size | {total_size//1024} KB |",
    f"",
]

if failed:
    report_lines += [
        "## Failed Screens",
        "",
        "| Title | Slug | Reason |",
        "|-------|------|--------|",
    ]
    for ff in failed:
        report_lines.append(f"| {ff['title']} | {ff['slug']} | {ff['reason']} |")
    report_lines.append("")

# Duplicate titles
dup_titles = {t: c for t, c in Counter(s['title'] for s in screen_info).items() if c > 1}
if dup_titles:
    report_lines += [
        "## Duplicate Titles (auto-disambiguated with suffix)",
        "",
        "| Title | Count |",
        "|-------|-------|",
    ]
    for title, cnt in dup_titles.items():
        report_lines.append(f"| {title} | {cnt} |")
    report_lines.append("")

report_lines += [
    "## File Sizes (OK screens only)",
    "",
    "| Slug | Size |",
    "|------|------|",
]
for info in screen_info:
    if info.get('status') == 'ok':
        kb = info.get('file_size', 0) // 1024
        report_lines.append(f"| {info['slug']} | {kb} KB |")

report_text = '\n'.join(report_lines) + '\n'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)
print(f"✓ EXPORT_REPORT.md written")

print(f"\n{'='*60}")
print(f"EXPORT COMPLETE")
print(f"  Screens: {total_ok}/{total_screens} OK, {total_fail} failed")
print(f"  Output:  {OUT_DIR}")
print(f"  Index:   {index_path}")
print(f"{'='*60}")
