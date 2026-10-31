# Thème WE IN STYLE (Horizon personnalisé)

## Organisation du dépôt

| Branche | Contenu |
|---|---|
| `upstream` | Horizon **tel que publié par Shopify** (aucune modif). Sert de référence pour la fusion. |
| `main` | Ton thème en ligne (Horizon + tes personnalisations). |
| `update-X.Y.Z` | Une mise à jour en cours de test. Fusionnée dans `main` une fois validée. |

Git compare la version d'origine (`upstream`), la tienne (`main`) et la nouvelle version de Shopify, puis reporte automatiquement tes modifications sur la nouvelle version.

Règles de fusion (`.gitattributes`) :
- **Contenus et réglages** (`templates/*.json`, `sections/*.json`, `config/settings_data.json`) : ta version est toujours conservée.
- **Langues** (`locales/*.json`) : fusion clé par clé (`tools/merge_locales.py`). Tes textes sont gardés, les nouvelles clés Shopify sont ajoutées.

## Mettre à jour (à chaque nouvelle version Horizon)

1. **Admin Shopify** : Thèmes → ton thème → *Mettre à jour* → *Ajouter aux thèmes brouillons*. Note l'ID du brouillon « Updated copy of… » (visible dans l'URL de l'éditeur). Shopify y a migré tes réglages et tes contenus.
2. **Terminal** :
   ```bash
   export SHOPIFY_FLAG_STORE=ta-boutique.myshopify.com   # une seule fois
   ./update-theme.sh 4.4.0 <ID_du_brouillon>
   ```
3. Si le script liste des fichiers en conflit : ouvre-les et cherche les marqueurs `<<<<<<<`. Le bloc `|||||||` montre l'original, `=======` la nouvelle version Shopify. Garde l'une ou l'autre, ou combine les deux, puis lance `git add -A && git commit`.
4. Le script affiche aussi les « réglages incompatibles » : des réglages que la nouvelle version ne reconnaît plus. Il devrait n'en rester aucun quand l'ID du brouillon a été fourni.
5. **Test** : `shopify theme push --unpublished --theme "Horizon 4.4.0 (test)"`, puis prévisualise.
6. **Validation** : `git checkout main && git merge update-4.4.0`, puis publie.

## Règles pour tes prochaines personnalisations (moins de conflits)

- Mets le code dans **tes propres fichiers** `snippets/custom-*.liquid`. Dans les fichiers Shopify, ajoute uniquement une ligne `{% render 'custom-…' %}`.
- Ne **ré-indente jamais** du code Shopify : ajoute des lignes avant et après plutôt que d'envelopper un bloc existant en le décalant.
- Marque chaque modification d'un fichier Shopify avec `[CUSTOM-GILLES]`. `grep -rn CUSTOM-GILLES` liste alors tout.
- Les modifications faites dans l'éditeur de code Shopify en ligne doivent être recopiées dans le dépôt (`shopify theme pull`), sinon elles seront perdues à la prochaine mise à jour.

## Tes personnalisations (fichiers `custom-*` et marqueurs `[CUSTOM-GILLES]`)

| Personnalisation | Fichiers |
|---|---|
| Masquage Dior (France, visiteur non connecté) | `snippets/custom-restricted`, `snippets/brand-access-control`, sections `main-collection`, `product-list`, `product-recommendations`, `search-results`, `collection-links`, `collection-list`, `predictive-search`, `product-information` |
| Données structurées JSON-LD | `snippets/custom-structured-data`, `custom-online-store-schema`, `custom-product-schema` |
| Performance (LCP, préchargements, scripts différés) | `snippets/custom-head-start`, `custom-font-preload`, `custom-lazy-scripts`, `scripts`, `view-transition-opt-in`, `card-gallery`, `product-media` |
| Mentions taxes TTC / international | `blocks/price` |
| Newsletter : prénom + tag `newsletter` | `blocks/email-signup` |
| Accordéons et sections vides masqués | `blocks/_accordion-row` + `snippets/custom-accordion-visibility`, `sections/section` |
| Guide des tailles (popup) | `blocks/popup-link` |
| Badge « CLUB REWARDS » (tag `reward-ready`) | `snippets/custom-reward-badge`, `blocks/_product-card-gallery`, `snippets/card-gallery` |
| Filtre prix fermé par défaut | `snippets/price-filter` |
| Anti-bot / filtrage géographique | `snippets/geo-bot-protection` (appelé dans `layout/theme.liquid`) |
| Icônes de paiement perso, tailles de police, etc. | `blocks/payment-icons`, `blocks/_inline-collection-title`, `blocks/accordion`, `snippets/tax-info`, `assets/slideshow.js` |
| Fichiers créés (guides des tailles, FAQ, Klarna, estimation de livraison…) | 24 fichiers propres à la boutique, jamais touchés par les mises à jour |
