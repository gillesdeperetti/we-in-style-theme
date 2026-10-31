#!/usr/bin/env bash
# =============================================================================
#  Mise à jour du thème Horizon de WE IN STYLE en conservant les personnalisations
#
#  Usage :  ./update-theme.sh <version Horizon> [<ID du thème "Updated copy">]
#  Exemple: ./update-theme.sh 4.4.0 187654321098
#
#  - <version>  : version Horizon à installer (ex. 4.4.0), récupérée sur
#                 github.com/Shopify/horizon (dépôt officiel Shopify).
#  - <ID>       : optionnel mais recommandé quand Shopify change des réglages.
#                 Dans l'admin : Thèmes > ton thème > « Mettre à jour » >
#                 « Ajouter aux thèmes brouillons ». L'ID de ce brouillon
#                 « Updated copy of … » sert à récupérer tes réglages et contenus
#                 déjà migrés par Shopify (templates, sections, settings_data).
#
#  Prérequis : git, python3, Shopify CLI (npm i -g @shopify/cli) connecté à la
#  boutique. Indique l'adresse .myshopify.com une fois pour toutes :
#     export SHOPIFY_FLAG_STORE=ta-boutique.myshopify.com
# =============================================================================
set -euo pipefail

VERSION="${1:?Version Horizon manquante, ex. ./update-theme.sh 4.4.0}"
COPY_ID="${2:-}"
STORE="${SHOPIFY_FLAG_STORE:-}"   # ex. export SHOPIFY_FLAG_STORE=ta-boutique.myshopify.com
DIRS="assets blocks config layout locales sections snippets templates"
BRANCH="update-$VERSION"

cd "$(dirname "$0")"
[ -z "$(git status --porcelain)" ] || { echo "❌ Des modifications ne sont pas commitées."; exit 1; }
git show-ref -q --verify "refs/heads/$BRANCH" && { echo "❌ La branche $BRANCH existe déjà (git branch -D $BRANCH pour recommencer)."; exit 1; }
git checkout -q main
git config merge.ours.driver true
git config merge.conflictStyle zdiff3

echo "▶ 1/6  Récupération de Horizon $VERSION depuis GitHub…"
git fetch -q https://github.com/Shopify/horizon.git main
COMMIT=$(git log FETCH_HEAD --format='%H %s' | awk -v v="Horizon v$VERSION" '{h=$1; $1=""; sub(/^ /,""); if ($0==v) {print h; exit}}')
[ -n "$COMMIT" ] || { echo "❌ Version $VERSION introuvable. Versions récentes :"; git log FETCH_HEAD --format='  %s' | head -8; exit 1; }

echo "▶ 2/6  Mise à jour de la branche upstream (thème Shopify d'origine)…"
PREV_UPSTREAM=$(git rev-parse upstream)
git checkout -q upstream
git rm -rq --ignore-unmatch $DIRS
git archive "$COMMIT" $DIRS | tar -x
git add -A $DIRS
git commit -qm "Horizon v$VERSION (Shopify)" || echo "  (aucun changement)"

echo "▶ 3/6  Fusion avec tes personnalisations (branche $BRANCH)…"
git checkout -q -b "$BRANCH" main
git merge upstream --no-commit --no-ff >/dev/null 2>&1 || true

echo "▶ 4/6  Fusion clé par clé des fichiers de langue…"
TMP=$(mktemp -d)
mkdir -p "$TMP/base" "$TMP/ours" "$TMP/theirs" "$TMP/out"
git archive "$PREV_UPSTREAM" locales | tar -x -C "$TMP/base"
git archive main locales | tar -x -C "$TMP/ours"
git archive upstream locales | tar -x -C "$TMP/theirs"
python3 -I tools/merge_locales.py "$TMP/base/locales" "$TMP/ours/locales" "$TMP/theirs/locales" "$TMP/out" | sed 's/^/  /'
rm -f locales/*.json && cp "$TMP/out/"*.json locales/ && git add -A locales
rm -rf "$TMP"

if [ -n "$COPY_ID" ]; then
  [ -n "$STORE" ] || { echo "❌ Définis d'abord SHOPIFY_FLAG_STORE=ta-boutique.myshopify.com"; exit 1; }
  echo "▶ 5/6  Récupération des réglages migrés par Shopify (thème $COPY_ID)…"
  shopify theme pull --store "$STORE" --theme "$COPY_ID" --path . \
    --only 'templates/*.json' --only 'sections/*.json' --only 'config/settings_data.json'
  git add -A templates sections config
else
  echo "▶ 5/6  (pas d'ID de copie migrée : réglages et contenus conservés tels quels)"
fi

echo "▶ 6/6  Vérifications…"
echo "  Réglages incompatibles avec la nouvelle version :"
python3 -I tools/check_json.py . | sed 's/^/    /'
CONFLICTS=$(git diff --name-only --diff-filter=U)
echo
if [ -n "$CONFLICTS" ]; then
  echo "⚠️  Fichiers à arbitrer à la main (marqueurs <<<<<<< / ||||||| / ======= / >>>>>>>) :"
  echo "$CONFLICTS" | sed 's/^/    /'
  echo
  echo "Une fois résolus :  git add -A && git commit -m \"Horizon $VERSION + personnalisations\""
else
  git commit -qm "Horizon $VERSION + personnalisations WE IN STYLE"
  echo "✅ Fusion terminée sans conflit (branche $BRANCH)."
fi
cat <<EOF

Étapes suivantes :
  1. Tester :      shopify theme push --store ${STORE:-ta-boutique.myshopify.com} --unpublished --theme "Horizon $VERSION (test)"
  2. Vérifier la prévisualisation (accueil, collection, produit, recherche, panier, newsletter).
  3. Valider :     git checkout main && git merge $BRANCH && git push
EOF
