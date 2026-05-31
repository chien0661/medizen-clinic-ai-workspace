#!/usr/bin/env python
"""Build index.html and EXPORT_REPORT.md from already-downloaded screens."""

import json, os, re, sys
from collections import Counter, defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

JFILE = r'C:\Users\chiendv\.claude\projects\E--MyProject-clinic-cms-workspace-claude-workspace\ea1403c6-aca7-43bf-ab59-7ac6983553c1\tool-results\mcp-stitch-list_screens-1777649929669.txt'
OUT_DIR = r'E:\MyProject\clinic-cms-workspace\claude-workspace\docs\design\medizen-modern\html-export'
SCREENS_DIR = os.path.join(OUT_DIR, 'screens')

def vi_slug(text):
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
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y','đ':'d',
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
        'Ỳ':'y','Ý':'y','Ỷ':'y','Ỹ':'y','Ỵ':'y','Đ':'d',
    }
    result = ''.join(replacements.get(ch, ch) for ch in text)
    result = result.lower()
    result = re.sub(r'[^a-z0-9]+', '-', result)
    return result.strip('-')

def categorize(title):
    t = title.lower()
    if any(x in t for x in ['dang nhap', 'quen mat khau', 'login', 'dang-nhap']):
        return 'Auth'
    if 'dang nhap' in vi_slug(t) or 'quen-mat-khau' in vi_slug(t):
        return 'Auth'
    if 'dashboard' in t:
        if 'bac si' in vi_slug(t) or 'doctor' in t: return 'Doctor'
        if 'duoc' in vi_slug(t): return 'Pharmacy'
        if 'dieu duong' in vi_slug(t): return 'Nursing'
        if 'le tan' in vi_slug(t): return 'Reception'
        if 'quan tri' in vi_slug(t) or 'admin' in t: return 'Admin'
        return 'Dashboard'
    ts = vi_slug(t)
    if any(x in ts for x in ['lich-hen', 'calendar', 'ca-truc', 'quan-ly-lich']):
        return 'Scheduling'
    if any(x in ts for x in ['benh-nhan', 'tiep-nhan', 'dang-ky', 'phong-cho', 'ho-so']):
        return 'Patient'
    if any(x in ts for x in ['kham', 'soap', 'chan-doan', 'sinh-hieu', 'can-lam-sang', 'ke-don', 'tom-tat']):
        return 'Clinical'
    if any(x in ts for x in ['duoc', 'kho-thuoc', 'danh-muc-thuoc', 'kiem-ke', 'nhap-kho', 'cap-phat', 'het-han']):
        return 'Pharmacy'
    if any(x in ts for x in ['thanh-toan', 'hoa-don', 'cong-no', 'bang-gia', 'billing', 'ar-aging']):
        return 'Billing'
    if any(x in ts for x in ['bhyt', 'bao-hiem']):
        return 'Insurance'
    if 'bao-cao' in ts or 'report' in ts:
        return 'Reports'
    if any(x in ts for x in ['cau-hinh', 'tich-hop', 'bao-mat', 'phong-kham', 'vai-tro', 'phan-quyen', 'audit']):
        return 'Admin'
    if any(x in ts for x in ['profile', 'ca-nhan']):
        return 'Profile'
    if any(x in ts for x in ['thong-bao', 'notification']):
        return 'Notifications'
    if any(x in ts for x in ['search', 'quick', 'clinic-switcher', 'chon-phong']):
        return 'Global UI'
    return 'Other'

with open(JFILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
screens = data['screens']

# Build slugs
slug_counter = Counter()
for s in screens:
    title = s.get('title') or ''
    clean = re.sub(r'\s*[—-]\s*MediZen.*$', '', title).strip()
    base = vi_slug(clean) or 'screen'
    slug_counter[base] += 1

slug_used = Counter()
screen_info = []
for s in screens:
    title = s.get('title') or ''
    clean = re.sub(r'\s*[—-]\s*MediZen.*$', '', title).strip()
    base = vi_slug(clean) or 'screen'
    if slug_counter[base] > 1:
        slug_used[base] += 1
        slug = f"{base}-{slug_used[base]}"
    else:
        slug = base
    screen_id = s['name'].split('/')[-1]
    out_path = os.path.join(SCREENS_DIR, f"{slug}.html")
    exists = os.path.exists(out_path)
    file_size = os.path.getsize(out_path) if exists else 0
    screen_info.append({
        'title': title,
        'clean_title': clean,
        'slug': slug,
        'screen_id': screen_id,
        'name': s['name'],
        'width': int(s.get('width') or 1440),
        'height': int(s.get('height') or 900),
        'deviceType': s.get('deviceType', 'DESKTOP'),
        'status': 'ok' if exists else 'failed',
        'file': f"screens/{slug}.html" if exists else None,
        'file_size': file_size,
        'category': categorize(title),
    })

results_ok = [i for i in screen_info if i['status'] == 'ok']
results_fail = [i for i in screen_info if i['status'] != 'ok']
print(f"OK: {len(results_ok)}, Failed: {len(results_fail)}")

# Build index
by_category = defaultdict(list)
for info in screen_info:
    by_category[info['category']].append(info)

CATEGORY_ORDER = ['Auth', 'Dashboard', 'Reception', 'Patient', 'Clinical', 'Doctor', 'Nursing',
                  'Pharmacy', 'Billing', 'Insurance', 'Reports', 'Scheduling', 'Notifications',
                  'Profile', 'Admin', 'Global UI', 'Other']

cards_html_parts = []
for cat in CATEGORY_ORDER:
    items = by_category.get(cat, [])
    if not items:
        continue
    parts = [f'''
    <div class="category-section" data-category="{cat}">
      <h2 class="text-xl font-bold text-slate-700 mb-4 mt-8 pb-2 border-b border-slate-200">
        {cat} <span class="text-sm font-normal text-slate-400">({len(items)} man)</span>
      </h2>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">''']

    for info in items:
        slug = info['slug']
        w = info['width']
        h = info['height']
        scale = round(180 / max(h, 1), 3)
        clean = info['clean_title']
        sid_short = info['screen_id'][:12] + '...'

        if info['status'] == 'ok':
            iframe_src = 'screens/' + slug + '.html'
            status_badge = '<span class="badge-ok">&#10003; OK</span>'
            preview = (
                '<div class="preview-container" style="height:180px;overflow:hidden;background:#f8fafc;'
                'border:1px solid #e2e8f0;border-radius:6px;position:relative;">'
                '<iframe src="' + iframe_src + '"'
                ' style="width:' + str(w) + 'px;height:' + str(h) + 'px;border:none;'
                'transform-origin:top left;transform:scale(' + str(scale) + ');pointer-events:none;"'
                ' loading="lazy"></iframe>'
                '</div>'
            )
            card_open = '<a href="' + iframe_src + '" class="card-link">'
            card_close = '</a>'
        else:
            status_badge = '<span class="badge-fail">&#10007; FAILED</span>'
            preview = ('<div class="preview-container" style="height:180px;background:#fef2f2;'
                       'display:flex;align-items:center;justify-content:center;'
                       'border:1px solid #fecaca;border-radius:6px;color:#ef4444;font-size:12px;">Download failed</div>')
            card_open = '<div class="card-link-disabled">'
            card_close = '</div>'

        parts.append(
            card_open +
            '<div class="screen-card bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow" data-title="' + clean.lower() + '">' +
            preview +
            '<div class="p-3">' +
            '<div class="font-medium text-slate-800 text-sm leading-tight mb-1">' + clean + '</div>' +
            '<div class="flex items-center justify-between">' +
            '<span class="text-xs text-slate-400 font-mono">' + sid_short + '</span>' +
            status_badge +
            '</div></div></div>' +
            card_close
        )

    parts.append('</div></div>')
    cards_html_parts.append(''.join(parts))

cards_html = ''.join(cards_html_parts)

gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
total_screens = len(screen_info)
total_ok = len(results_ok)
total_fail = len(results_fail)

index_html = (
'<!DOCTYPE html>\n'
'<html lang="vi">\n'
'<head>\n'
'  <meta charset="UTF-8">\n'
'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
'  <title>MediZen Modern &#8212; Toan bo man (Stitch project 2542650746708884228)</title>\n'
'  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
'  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">\n'
'  <script src="https://cdn.tailwindcss.com"></script>\n'
'  <style>\n'
'    body { font-family: \'Inter\', sans-serif; background: #f8fafc; }\n'
'    h1, h2 { font-family: \'Plus Jakarta Sans\', sans-serif; }\n'
'    .badge-ok { background:#dcfce7;color:#16a34a;font-size:10px;padding:2px 6px;border-radius:9999px;font-weight:600; }\n'
'    .badge-fail { background:#fee2e2;color:#dc2626;font-size:10px;padding:2px 6px;border-radius:9999px;font-weight:600; }\n'
'    .card-link { text-decoration:none;color:inherit;display:block; }\n'
'    .card-link-disabled { color:inherit;display:block;opacity:0.6; }\n'
'    .screen-card { cursor:pointer; }\n'
'    .hidden-by-search { display:none!important; }\n'
'  </style>\n'
'</head>\n'
'<body class="min-h-screen">\n'
'  <header class="bg-white border-b border-slate-200 sticky top-0 z-50">\n'
'    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">\n'
'      <div>\n'
'        <h1 class="text-2xl font-bold text-slate-900">MediZen Modern</h1>\n'
'        <p class="text-sm text-slate-500 mt-0.5">Stitch project <code class="bg-slate-100 px-1 rounded">2542650746708884228</code>'
' &#183; ' + str(total_screens) + ' man &#183; ' + str(total_ok) + ' exported &#183; ' + str(total_fail) + ' failed</p>\n'
'      </div>\n'
'      <div class="flex gap-3 items-center">\n'
'        <input type="text" id="search" placeholder="Tim man..." oninput="filterScreens(this.value)"\n'
'          class="border border-slate-300 rounded-lg px-4 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500">\n'
'        <a href="https://stitch.withgoogle.com/projects/2542650746708884228" target="_blank"\n'
'          class="text-xs text-blue-600 hover:underline whitespace-nowrap">&#8599; Stitch Project</a>\n'
'      </div>\n'
'    </div>\n'
'  </header>\n'
'  <main class="max-w-7xl mx-auto px-6 pb-16">\n'
+ cards_html +
'\n  </main>\n'
'  <footer class="bg-white border-t border-slate-200 py-6 mt-8">\n'
'    <div class="max-w-7xl mx-auto px-6 text-center text-sm text-slate-500">\n'
'      <p>Generated: ' + gen_time + ' &#183; ' + str(total_ok) + '/' + str(total_screens) + ' screens exported successfully</p>\n'
'      <p class="mt-1">MediZen Modern UI Design &#8212; Clinic CMS Workspace</p>\n'
'    </div>\n'
'  </footer>\n'
'  <script>\n'
'    function filterScreens(query) {\n'
'      const q = query.toLowerCase().trim();\n'
'      document.querySelectorAll(\'.screen-card\').forEach(card => {\n'
'        const title = card.getAttribute(\'data-title\') || \'\';\n'
'        const parent = card.closest(\'.card-link, .card-link-disabled\');\n'
'        const el = parent || card;\n'
'        if (!q || title.includes(q)) { el.classList.remove(\'hidden-by-search\'); }\n'
'        else { el.classList.add(\'hidden-by-search\'); }\n'
'      });\n'
'      document.querySelectorAll(\'.category-section\').forEach(sec => {\n'
'        const visible = sec.querySelectorAll(\'.screen-card:not(.hidden-by-search)\').length;\n'
'        sec.style.display = visible ? \'\' : \'none\';\n'
'      });\n'
'    }\n'
'  </script>\n'
'</body>\n'
'</html>\n'
)

index_path = os.path.join(OUT_DIR, 'index.html')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_html)
print(f"index.html: {os.path.getsize(index_path)//1024}KB")

# Report
dup_titles = {t:c for t,c in Counter(s['title'] for s in screen_info).items() if c>1}
total_size = sum(i.get('file_size',0) for i in screen_info)

lines = [
    '# MediZen Modern — HTML Export Report',
    '',
    f'**Generated:** {gen_time}',
    '**Project:** Stitch 2542650746708884228',
    '',
    '## Summary',
    '',
    '| Metric | Value |',
    '|--------|-------|',
    f'| Total screens in list | {total_screens} |',
    f'| Exported successfully | {total_ok} |',
    f'| Failed | {total_fail} |',
    f'| Total HTML size | {total_size//1024} KB |',
    '',
]
if results_fail:
    lines += ['## Failed Screens','','| Title | Slug | Reason |','|-------|------|--------|']
    for ff in results_fail:
        lines.append(f'| {ff["title"]} | {ff["slug"]} | not downloaded |')
    lines.append('')
if dup_titles:
    lines += ['## Duplicate Titles (auto-disambiguated)','','| Title | Count |','|-------|-------|']
    for title, cnt in dup_titles.items():
        lines.append(f'| {title} | {cnt} |')
    lines.append('')
lines += ['## File Sizes','','| Slug | Size |','|------|------|']
for info in screen_info:
    if info['status'] == 'ok':
        lines.append(f'| {info["slug"]} | {info["file_size"]//1024} KB |')

report_path = os.path.join(OUT_DIR, 'EXPORT_REPORT.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print(f"EXPORT_REPORT.md written")
print(f"\nDONE: {total_ok}/{total_screens} OK, {total_fail} failed")
