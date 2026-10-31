# Réinjecte, après une migration Shopify, les valeurs des réglages ajoutés par tes personnalisations
# (réglages présents dans ton code mais pas dans le thème Shopify d'origine, donc supprimés par la migration).
# Usage : restore_custom_settings.py <ancien thème> <thème Shopify d'origine (nouvelle version)> <thème final>
import os, re, sys, json
exec(open(os.path.join(os.path.dirname(__file__), 'merge_locales.py')).read().split('base_dir, ours_dir')[0])
old, stock_dir, fin = sys.argv[1:4]
def schema(path):
    s = open(path, encoding='utf-8').read(); m = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', s, re.S)
    return json.loads(m.group(1)) if m else {}
def ids_of(root):
    r = {}
    for d in ('sections', 'blocks'):
        for f in os.listdir(os.path.join(root, d)):
            if f.endswith('.liquid'):
                r[f[:-7]] = {x['id'] for x in schema(os.path.join(root, d, f)).get('settings', []) if 'id' in x}
    return r
stock, final = ids_of(stock_dir), ids_of(fin)
def nodes(o, p, out):
    for sid, s in (o.get('sections') or {}).items(): node(s, p + (sid,), out)
def node(s, p, out):
    out[p] = s
    for bid, b in (s.get('blocks') or {}).items(): node(b, p + (bid,), out)
n = 0
for d in ('templates', 'sections'):
    for f in sorted(os.listdir(os.path.join(old, d))):
        fp = os.path.join(fin, d, f)
        if not f.endswith('.json') or not os.path.exists(fp): continue
        a, b = {}, {}; doc = load(fp)
        nodes(load(os.path.join(old, d, f)), (), a); nodes(doc, (), b)
        changed = False
        # 1) Sections créées par toi que Shopify a remplacées par une section standard : on les remet
        for k, s in a.items():
            t = s.get('type', '')
            if len(k) == 1 and t in final and t not in stock and k in b and b[k].get('type') != t:
                doc['sections'][k[0]] = s; b[k] = s; changed = True; n += 1
                print(f"  {d}/{f}: section '{t}' restaurée")
        for k, s in a.items():
            if k not in b or b[k].get('type') != s.get('type'): continue
            t = s.get('type'); custom = final.get(t, set()) - stock.get(t, set())
            for key in final.get(t, set()):
                old_v = (s.get('settings') or {}).get(key, None)
                if old_v is None: continue
                new_s = b[k].get('settings') or {}
                # 2) réglage ajouté par ton code (supprimé par la migration) ou 3) valeur effacée par la migration
                if (key in custom and new_s.get(key) != old_v) or (key not in custom and key not in new_s):
                    b[k].setdefault('settings', {})[key] = s['settings'][key]; changed = True; n += 1
                    print(f"  {d}/{f}: {s['type']}.{key} = {json.dumps(s['settings'][key], ensure_ascii=False)[:60]}")
        if changed: json.dump(doc, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"{n} réglage(s) personnalisé(s) restauré(s)")
