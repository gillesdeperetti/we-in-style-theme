# Migration ponctuelle Horizon 3.x -> 4.x : la migration Shopify convertit les fonds des schémas de
# couleurs mais pas les couleurs de texte. On rétablit la couleur de texte de l'ancien schéma
# (texte, titres, icônes) sur les blocs qui la proposent en 4.x.
# Usage : migrate_scheme_text_colors.py <ancien thème 3.x> <thème 4.x à corriger> <couleur texte page 4.x>
import os, re, sys, json
exec(open(os.path.join(os.path.dirname(__file__), 'merge_locales.py')).read().split('base_dir, ours_dir')[0])
old, fin, page_text = sys.argv[1], sys.argv[2], sys.argv[3].lower()
def schema(path):
    s = open(path, encoding='utf-8').read(); m = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', s, re.S)
    return json.loads(m.group(1)) if m else {}
colors = {}
for d in ('sections', 'blocks'):
    for f in os.listdir(os.path.join(fin, d)):
        if f.endswith('.liquid'):
            colors[f[:-7]] = {x['id'] for x in schema(os.path.join(fin, d, f)).get('settings', []) if x.get('type') == 'color'}
schemes = load(os.path.join(old, 'config/settings_data.json'))['current']['color_schemes']
default = 'scheme-1'
VAR = {'var(--color-foreground)': 'foreground', 'var(--color-foreground-heading)': 'foreground_heading', 'var(--color-primary)': 'primary'}
n = 0
def walk(old_node, new_node, scheme, where):
    global n
    st = old_node.get('settings') or {}
    if st.get('color_scheme') and not st.get('inherit_color_scheme', False) and st['color_scheme'] in schemes:
        scheme = st['color_scheme']
    sc = schemes[scheme]['settings']
    want = sc[VAR.get(st.get('color'), 'foreground')]
    t = new_node.get('type'); ns = new_node.setdefault('settings', {})
    for key in ('text_color', 'icon_color'):
        if key in colors.get(t, ()) and not ns.get(key) and want.lower() != page_text:
            ns[key] = want; n += 1
            print(f"  {where}: {t}.{key} = {want}  (schéma {scheme[:14]})")
    for bid, ob in (old_node.get('blocks') or {}).items():
        nb = (new_node.get('blocks') or {}).get(bid)
        if nb and nb.get('type') == ob.get('type'): walk(ob, nb, scheme, where)
for d in ('templates', 'sections'):
    for f in sorted(os.listdir(os.path.join(old, d))):
        fp = os.path.join(fin, d, f)
        if not f.endswith('.json') or not os.path.exists(fp): continue
        o, nw = load(os.path.join(old, d, f)), load(fp); before = n
        for sid, s in (o.get('sections') or {}).items():
            ns = (nw.get('sections') or {}).get(sid)
            if ns and ns.get('type') == s.get('type'): walk(s, ns, default, f"{d}/{f}")
        if n > before: json.dump(nw, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"{n} couleur(s) de texte rétablie(s)")
