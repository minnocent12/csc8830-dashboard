# CSc 8830 Computer Vision Assignments Dashboard

Single web entry point that mounts the Module 2, Module 3, and Module 4 assignment apps into
one Streamlit sidebar, so every assignment is reachable from one link.

Each module remains an independently submittable, independently runnable project in its own
repository:

- Module 2: https://github.com/minnocent12/csc8830-module-2
- Module 3: https://github.com/minnocent12/csc8830-module-3
- Module 4: https://github.com/minnocent12/csc8830-module-4

This repository carries no independent implementation of its own. `Module_2/src`,
`Module_3/src`, and `Module_4/src` are plain copies of each module's `src/` tree, kept only so
a static host (Streamlit Community Cloud) can import `moduleN.webapp.pages.get_pages()`
without needing git submodule support. The shared dashboard shell that wires the pages
together lives in `dashboard/`.

## Run locally

```bash
git clone https://github.com/minnocent12/csc8830-dashboard.git
cd csc8830-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Updating a module's copied source

After pushing changes to a module's own repository, refresh its vendored copy here with
`scripts/sync_module_src.sh`:

```bash
scripts/sync_module_src.sh Module_2
git add Module_2/src
git commit -m "Sync Module 2 source"
git push
```

Streamlit Community Cloud redeploys automatically on every push to `main`.

## Deployment

Deployed on Streamlit Community Cloud from this repository's `main` branch, entry point
`app.py`.
