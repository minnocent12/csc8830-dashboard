# CSc 8830 Computer Vision Assignments Dashboard

Single web entry point that mounts the Module 2, Module 3, and Module 4 assignment apps into
one Streamlit sidebar, so every assignment is reachable from one link.

Each module remains an independently submittable, independently runnable project in its own
repository:

- Module 2: https://github.com/minnocent12/csc8830-module-2
- Module 3: https://github.com/minnocent12/csc8830-module-3
- Module 4: https://github.com/minnocent12/csc8830-module-4

This repository does not contain module implementation code of its own. It pulls each module
in as a git submodule and reuses each module's `moduleN.webapp.pages.get_pages()` provider
through the shared dashboard shell in `dashboard/`.

## Run locally

```bash
git clone --recurse-submodules https://github.com/minnocent12/csc8830-dashboard.git
cd csc8830-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If you already cloned without `--recurse-submodules`, run:

```bash
git submodule update --init --recursive
```

## Updating a module

Each `Module_N/` directory is a submodule pointer to that module's own repository. To pull in
the latest commit from a module after it changes:

```bash
git submodule update --remote Module_2
git add Module_2
git commit -m "Update Module 2 submodule"
```

## Deployment

Deployed on Streamlit Community Cloud from this repository's `main` branch, entry point
`app.py`.
