# Proposed Public Evidence Review

**Status:** `USER APPROVED FOR REPOSITORY INCLUSION - NOT DEPLOYED`

This is a local publication-readiness audit of the proposed bundle described by
`data/proposed_public_demo/manifest.json`. The bundle contains 29 files totaling 2,347,455
bytes. The count includes the manifest itself, 7 compact records, 14 stereo-view images, and 7
diagnostic images.

The image review used the resized proposed assets. The checkerboard and intended validation object
were visible in every image group. No face or explicit personal identifier was observed in the
reviewed derivatives. Workspace/background objects remain visible in several captures, so the
owner must review them before any public release. Resizing is not treated as anonymization.

## Local visual review gallery

The local-only gallery is [`local_review/proposed_public_evidence_gallery.html`](../local_review/proposed_public_evidence_gallery.html).
The matching all-image contact sheet is
[`local_review/proposed_public_evidence_contact_sheet.jpg`](../local_review/proposed_public_evidence_contact_sheet.jpg).
Both are excluded by `.gitignore` and are not part of the Streamlit navigation or proposed public
bundle.

The page association below is the intended standalone page association. The standalone app now
resolves the manifest-defined compact records and display derivatives at runtime. The original
full-resolution records and captures remain outside the runtime path and are preserved locally.

| # | Relative path | Type | Size | Page association | Source experiment | Content/privacy review | Essential | Recommendation |
|---:|---|---|---:|---|---|---|:---:|---|
| 1 | `manifest.json` | JSON | 25,369 B | All pages | All proposed experiments | Bundle index and review metadata; no visual personal content | Yes | Keep as candidate; user review required |
| 2 | `records/experiment_01.json` | JSON | 8,428 B | Rectangle measurements | Flashcard | Path-free academic record and status; no visual personal content | Yes | Keep as candidate; user review required |
| 3 | `images/experiment_01_view1.jpg` | JPEG | 135,524 B | Rectangle measurements | Flashcard | Checkerboard and flashcard visible; nearby workspace/background objects remain visible | Yes | Candidate only; inspect background before release |
| 4 | `images/experiment_01_view2.jpg` | JPEG | 136,436 B | Rectangle measurements | Flashcard | Checkerboard and flashcard visible; nearby workspace/background objects remain visible | Yes | Candidate only; inspect background before release |
| 5 | `images/experiment_01_diagnostic.jpg` | JPEG | 225,140 B | Rectangle measurements | Flashcard | Correspondence diagnostic; checkerboard and scene background visible | Yes | Candidate only; inspect background before release |
| 6 | `records/experiment_02.json` | JSON | 6,533 B | Rectangle measurements | FREE ADMISSION first experiment | Path-free academic record and failed validation status | Yes | Keep as candidate; user review required |
| 7 | `images/experiment_02_view1.jpg` | JPEG | 83,584 B | Rectangle measurements | FREE ADMISSION first experiment | Checkerboard and card visible; surrounding board/background visible | Yes | Candidate only; inspect background before release |
| 8 | `images/experiment_02_view2.jpg` | JPEG | 82,450 B | Rectangle measurements | FREE ADMISSION first experiment | Checkerboard and card visible; portrait orientation and background visible | Yes | Candidate only; inspect background before release |
| 9 | `images/experiment_02_diagnostic.jpg` | JPEG | 119,878 B | Rectangle measurements | FREE ADMISSION first experiment | Correspondence diagnostic for card and checkerboard; background visible | Yes | Candidate only; inspect background before release |
| 10 | `records/experiment_03.json` | JSON | 6,877 B | Rectangle measurements | FREE ADMISSION second experiment | Path-free academic record and rejected geometry status | Yes | Keep as candidate; user review required |
| 11 | `images/experiment_03_view1.jpg` | JPEG | 87,579 B | Rectangle measurements | FREE ADMISSION second experiment | Checkerboard and card visible; surrounding board/background visible | Yes | Candidate only; inspect background before release |
| 12 | `images/experiment_03_view2.jpg` | JPEG | 83,522 B | Rectangle measurements | FREE ADMISSION second experiment | Checkerboard and card visible; surrounding board/background visible | Yes | Candidate only; inspect background before release |
| 13 | `images/experiment_03_diagnostic.jpg` | JPEG | 122,309 B | Rectangle measurements | FREE ADMISSION second experiment | Correspondence diagnostic; no face observed, background visible | Yes | Candidate only; inspect background before release |
| 14 | `records/experiment_04.json` | JSON | 9,785 B | Rectangle measurements | FREE ADMISSION third experiment | Path-free academic record and physical-accuracy failure status | Yes | Keep as candidate; user review required |
| 15 | `images/experiment_04_view1.jpg` | JPEG | 88,304 B | Rectangle measurements | FREE ADMISSION third experiment | Checkerboard and card visible; workspace edges/background visible | Yes | Candidate only; inspect background before release |
| 16 | `images/experiment_04_view2.jpg` | JPEG | 92,477 B | Rectangle measurements | FREE ADMISSION third experiment | Checkerboard and card visible; workspace edges/background visible | Yes | Candidate only; inspect background before release |
| 17 | `images/experiment_04_diagnostic.jpg` | JPEG | 133,414 B | Rectangle measurements | FREE ADMISSION third experiment | Correspondence diagnostic; workspace/background visible | Yes | Candidate only; inspect background before release |
| 18 | `records/experiment_05.json` | JSON | 3,925 B | Circle measurements | Yellow lid marked perimeter experiment | Path-free record preserving planarity rejection | Yes | Keep as candidate; user review required |
| 19 | `images/experiment_05_view1.jpg` | JPEG | 87,673 B | Circle measurements | Yellow lid marked perimeter experiment | Checkerboard and marked yellow lid visible; board/background visible | Yes | Candidate only; inspect background before release |
| 20 | `images/experiment_05_view2.jpg` | JPEG | 83,492 B | Circle measurements | Yellow lid marked perimeter experiment | Checkerboard and marked yellow lid visible; board/background visible | Yes | Candidate only; inspect background before release |
| 21 | `images/experiment_05_diagnostic.jpg` | JPEG | 144,636 B | Circle measurements | Yellow lid marked perimeter experiment | Correspondence diagnostic showing lid and board; background visible | Yes | Candidate only; inspect background before release |
| 22 | `records/experiment_06.json` | JSON | 2,441 B | Circle measurements | Yellow lid unmarked pending pair | Path-free pending record; no accepted diameter claimed | Yes | Keep as candidate; user review required |
| 23 | `images/experiment_06_view1.jpg` | JPEG | 86,459 B | Circle measurements | Yellow lid unmarked pending pair | Checkerboard and unmarked yellow lid visible; background visible | Yes | Candidate only; inspect background before release |
| 24 | `images/experiment_06_view2.jpg` | JPEG | 83,426 B | Circle measurements | Yellow lid unmarked pending pair | Checkerboard and unmarked yellow lid visible; background visible | Yes | Candidate only; inspect background before release |
| 25 | `images/experiment_06_diagnostic.jpg` | JPEG | 153,662 B | Circle measurements | Yellow lid unmarked pending pair | Correspondence diagnostic; no accepted circle geometry; background visible | Yes | Candidate only; inspect background before release |
| 26 | `records/experiment_07.json` | JSON | 9,325 B | Polygon measurements | Cardboard triangle | Path-free academic record and physical-accuracy limitation | Yes | Keep as candidate; user review required |
| 27 | `images/experiment_07_view1.jpg` | JPEG | 84,435 B | Polygon measurements | Cardboard triangle | Checkerboard and triangle visible; board/background visible | Yes | Candidate only; inspect background before release |
| 28 | `images/experiment_07_view2.jpg` | JPEG | 83,749 B | Polygon measurements | Cardboard triangle | Checkerboard and triangle visible; board/background visible | Yes | Candidate only; inspect background before release |
| 29 | `images/experiment_07_diagnostic.jpg` | JPEG | 76,507 B | Polygon measurements | Cardboard triangle | Vertex-correspondence diagnostic; background visible | Yes | Candidate only; inspect background before release |

## Reproducibility finding

The standalone runtime now uses only tracked source/configuration and the manifest-defined
`data/proposed_public_demo/` bundle. It does not require the original full-resolution captures,
raw result directories, or absolute developer-machine paths. A clean-clone smoke test copied only
`app.py`, `pyproject.toml`, `src/`, `.streamlit/`, and the proposed bundle; Overview and all three
shape pages rendered without Streamlit exceptions, and every curated experiment selection was
exercised successfully.

The user approved the reviewed 21 image derivatives and seven compact records for repository
inclusion. The manifest records `publication_approved: true`; no remote repository, deployment, or
public release has been performed.

## JSON and metadata review

All seven compact records and the manifest were checked for absolute paths, external bundle
references, credentials, secrets, GPS/location fields, and serial/IMEI/UDID-style identifiers.
None were found. Original capture filenames were removed from derived explanatory text and replaced
with generic provenance labels. The iPhone 15 Pro Max model remains where it documents calibration
compatibility; it is not a unique device identifier. Calibration, pose, depth, geometry, measured
values, uncertainty, and validation classifications remain unchanged.

## Asset-level publication recommendation

The 21 reviewed images are approved for repository inclusion. They remain subject to the future
repository's normal review and deployment controls, and
all seven experiment groups show some unrelated workspace or background context. No face, person,
screen, or explicit personal identifier was observed in the local review. Resizing alone does not
resolve the background concern. Before publication, the owner should approve each image or request
a documented crop/mask derivative that preserves the checkerboard, object, and diagnostic labels.

## Proposed future tracking manifest

This records the approved staging policy. The Module 7 directory is now an independent local Git
repository on the authorized task branch; no commit, remote, push, or deployment has been made.

| Category | Proposed contents | Current disposition |
|---|---|---|
| Source and configuration | `app.py`, `pyproject.toml`, `.streamlit/config.toml`, `src/module7/`, approved scripts, bundle-builder script | Candidate for tracking after repository approval |
| Documentation | `README.md`, assignment documents, protocols, architecture, references, implementation plan/status, this review | Candidate for tracking after review |
| Tests | `tests/` including core, provider, design parity, public-copy, evidence, and smoke tests | Candidate for tracking |
| Curated evidence | `data/proposed_public_demo/` with 21 approved display images, 7 approved compact records, and `manifest.json` | Approved for local staging; not deployed |
| Local-only experimental records | Full `data/physical_validation/`, full `results/stereo_diagnostics/`, complete result JSON, audit history, ruler photographs, and working diagnostics | Preserve locally; do not stage by default |
| Ignored/generated files | Virtual environments, caches, bytecode, build output, temporary crops, secrets, and ignored raw directories listed in `.gitignore` | Keep ignored |
| Sensitive material | Any image with private surroundings, identifying content, credentials, or unapproved raw experiment data | Exclude until explicitly reviewed |

The current `.gitignore` protects calibration, stereo-pair, object, and room-video input trees,
the approximately 61 MB `data/physical_validation/` capture directory, the approximately 758 MB
`results/stereo_diagnostics/` directory, and `local_review/`. These remain local-only and are not
part of the staging allowlist.
