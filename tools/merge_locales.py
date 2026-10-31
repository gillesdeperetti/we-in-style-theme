# Fusion clé par clé des fichiers de langue : origine (base), boutique (ours), nouvelle version (theirs).
# Les textes modifiés/ajoutés dans la boutique sont conservés ; tout le reste suit la nouvelle version.
import sys, json, os, re

def load(path):
    if not os.path.exists(path): return None
    s = open(path, encoding='utf-8').read()
    out, i, n, in_str = [], 0, len(s), False
    while i < n:
        c = s[i]
        if in_str:
            out.append(c)
            if c == '\\': out.append(s[i+1]); i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if c == '"': in_str = True; out.append(c); i += 1; continue
        if s.startswith('//', i): i = s.find('\n', i); i = n if i < 0 else i; continue
        if s.startswith('/*', i): i = s.find('*/', i) + 2; continue
        out.append(c); i += 1
    txt = re.sub(r',(\s*[}\]])', r'\1', ''.join(out))
    return json.loads(txt)

def flat(d, p=()):
    r = {}
    for k, v in d.items():
        if isinstance(v, dict): r.update(flat(v, p + (k,)))
        else: r[p + (k,)] = v
    return r

def setp(d, path, v):
    for k in path[:-1]:
        if not isinstance(d.get(k), dict): d[k] = {}
        d = d[k]
    d[path[-1]] = v

def delp(d, path):
    for k in path[:-1]:
        d = d.get(k)
        if not isinstance(d, dict): return
    d.pop(path[-1], None)

base_dir, ours_dir, theirs_dir, out_dir = sys.argv[1:5]
report = []
names = sorted(set(os.listdir(ours_dir)) | set(os.listdir(theirs_dir)))
for name in names:
    if not name.endswith('.json'): continue
    b, o, t = (load(os.path.join(x, name)) for x in (base_dir, ours_dir, theirs_dir))
    if t is None: res = o; report.append(f"{name}: fichier créé par la boutique, conservé")
    elif o is None: res = t
    else:
        fb, fo, ft = flat(b or {}), flat(o), flat(t)
        res = json.loads(json.dumps(t))
        kept = conflicts = 0
        for k, v in fo.items():
            if fb.get(k) != v:            # modifié ou ajouté côté boutique
                if k in ft and fb.get(k) != ft[k] and ft[k] != v:
                    conflicts += 1
                    if name.endswith('.schema.json'): continue  # libellés de l'éditeur : version Shopify
                setp(res, k, v); kept += 1
        if kept: report.append(f"{name}: {kept} texte(s) de la boutique conservé(s)" + (f", dont {conflicts} aussi modifié(s) par Shopify (boutique gardée, sauf libellés éditeur *.schema.json)" if conflicts else ""))
    json.dump(res, open(os.path.join(out_dir, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(os.path.join(out_dir, name), 'a').write('\n')
print('\n'.join(report))
