# SER Module — autonome

Ce dossier est **indépendant** du dépôt `insta-auto` d'origine. Il ne contient aucun projet arabe, maths, chimie, coréen, etc.
Le dépôt source a servi uniquement de référence pour comprendre la mécanique de publication Instagram.

## Ce que contient le module

- `ser.py` : moteur unique de publication/dry-run/validation
- `config/catalog.json` : les 15 niches SER + palettes/typographies
- `niches/<id>/ebook/` : e-book final ou brief de production
- `niches/<id>/posts/queue.json` : file de contenus Instagram
- `niches/<id>/slides/` : assets finaux des carrousels
- `niches/<id>/creative/visual.json` : charte visuelle et objets à montrer
- `state/history.json` : posts déjà publiés
- `.github/workflows/publish.yml` : automatisation GitHub Actions

## Règle de sécurité

Le moteur **ne publie que les posts avec `status: "ready"` ET dont toutes les slides existent**.
Les 14 niches encore en production sont présentes, mais en `draft`, donc impossibles à publier accidentellement.

## Guide 01

`administratif-fiscal` contient le vrai e-book final Micro-entreprise 2026 ainsi que le premier carousel premium validé.

## Test local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ser.py validate
python ser.py list
python ser.py dry-run --niche administratif-fiscal
```

## Publication réelle

Créer `.env` depuis `.env.example`, puis :

```bash
python ser.py publish --niche administratif-fiscal
```

Ne jamais committer `.env`.

## GitHub Actions

Configurer ces secrets :

- `IG_USER_ID_MRLIPTN`
- `IG_TOKEN_MRLIPTN`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Le workflow publie le prochain post `ready` non encore publié.
