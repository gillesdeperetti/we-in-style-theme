# Vérifie que les templates/sections JSON de la boutique sont compatibles avec les schémas du thème.
import sys, os, re, json, collections
theme = sys.argv[1]
sys.path.insert(0, os.path.dirname(__file__))
src = open(os.path.join(os.path.dirname(__file__), 'merge_locales.py')).read().split('base_dir, ours_dir')[0]
exec(src)  # load()

def schema(path):
    s = open(path, encoding='utf-8').read()
    m = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', s, re.S)
    return json.loads(m.group(1)) if m else {}

def ids(settings): return {x['id'] for x in settings or [] if 'id' in x}

sections = {f[:-7]: schema(os.path.join(theme, 'sections', f)) for f in os.listdir(os.path.join(theme, 'sections')) if f.endswith('.liquid')}
blocks = {f[:-7]: schema(os.path.join(theme, 'blocks', f)) for f in os.listdir(os.path.join(theme, 'blocks')) if f.endswith('.liquid')}
issues = collections.defaultdict(set)

def check_blocks(where, parent_schema, bl):
    for bid, b in (bl or {}).items():
        t = b.get('type', '')
        if t.startswith('shopify://') or t == '@app': continue
        local = {x.get('type'): x for x in parent_schema.get('blocks', []) if 'settings' in x or 'name' in x}
        if t in blocks: sch = blocks[t]
        elif t in local: sch = local[t]
        else: issues[f"bloc introuvable '{t}'"].add(where); continue
        for k in set((b.get('settings') or {})) - ids(sch.get('settings')):
            issues[f"réglage supprimé/renommé '{t}.{k}'"].add(where)
        check_blocks(where, sch, b.get('blocks'))

files = [os.path.join('templates', f) for f in os.listdir(os.path.join(theme, 'templates')) if f.endswith('.json')]
files += [os.path.join('sections', f) for f in os.listdir(os.path.join(theme, 'sections')) if f.endswith('.json')]
for rel in sorted(files):
    d = load(os.path.join(theme, rel))
    for sid, s in (d.get('sections') or {}).items():
        t = s.get('type', '')
        if t.startswith('shopify://') or t == 'apps': continue
        if t not in sections: issues[f"section introuvable '{t}'"].add(rel); continue
        for k in set((s.get('settings') or {})) - ids(sections[t].get('settings')):
            issues[f"réglage supprimé/renommé '{t}.{k}'"].add(rel)
        check_blocks(rel, sections[t], s.get('blocks'))

gs = ids(sum((g.get('settings', []) for g in json.load(open(os.path.join(theme, 'config/settings_schema.json')))), []))
cur = load(os.path.join(theme, 'config/settings_data.json')).get('current', {})
if isinstance(cur, dict):
    for k in set(cur) - gs - {'sections', 'content_for_index', 'blocks'}:
        issues[f"réglage global supprimé/renommé '{k}'"].add('config/settings_data.json')
for k in sorted(issues): print(f"{k}  ← {', '.join(sorted(issues[k]))[:200]}")
print(f"TOTAL {len(issues)}")
