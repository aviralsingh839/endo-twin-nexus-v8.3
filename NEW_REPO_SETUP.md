# ENDO-TWIN Nexus V8.3 — New Repository Setup

Base source: user-supplied V8.3 Superbuild archive (commit `c3c22bb21450c24ead1f1f54070250076b27e075`).

Suggested new GitHub repository name:

`endo-twin-nexus-v8.3`

This copy is intentionally separate from `aviralsingh839/chrono-pcos-v8.1`.

## Create the empty GitHub repository

On GitHub, create a new **empty** repository named `endo-twin-nexus-v8.3`.
Do not add a README, .gitignore, or license during creation.

## Push this prepared copy

From this folder:

```bash
git init -b main
git add .
git commit -m "Base ENDO-TWIN Nexus V8.3 from supplied superbuild"
git remote add origin git@github.com:aviralsingh839/endo-twin-nexus-v8.3.git
git push -u origin main
```

After that, all new UI, science, Android, desktop-build and testing changes can
be made in this new repository without touching the original repository.
