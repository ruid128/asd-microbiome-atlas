# ASD Microbiome Atlas

Static publication-facing website for the frozen ASD Microbiome Atlas
`v1.1-rc1` release.

## Source of truth

The complete release files are stored in `data/release_v1_1/` and remain
repository-only. The website reads `web/data/atlas_public_v1_1.json`, a limited
projection containing only fields required by Overview and Atlas. Internal
curation notes, correction logs, release documents, and extended metadata are
not published with the website.

## Validate and synchronize

From the repository root in PowerShell:

```powershell
py -3.10 scripts\build_release_v1_1.py
node --check web\app.js
```

The release script stops on any SHA-256 mismatch, row/field-count mismatch,
canonical-entity mismatch, or failed critical-record assertion. After a pass,
it rebuilds the limited public JSON payload in `web/data/`.

## Local preview

```powershell
py -3.10 -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open `http://127.0.0.1:8765/`. A green status banner confirms that the curated
70-record public view loaded successfully.

## Deployment

`vercel.json` serves `web/` as the output directory. The public GitHub Pages
site is deployed from the separate `gh-pages` branch; merging source changes
into `main` alone does not update the public site unless the deployment process
also publishes the contents of `web/` to `gh-pages`.
