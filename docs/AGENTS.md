# Documentation guidance

Documentation is part of the Black Line contract. Keep API behavior and
numeric manuscript claims bound to executable tests; state whether a claim is
computational, structural, methodological, or outside the instrument's
authority. `../data/claim_ledger.yaml` provides the machine-readable numeric
provenance consumed by the external template validator
(<https://github.com/docxology/template>); update it with the
binding tests when derived claims change.

Figures must be generated into `../output/figures/`, embedded with a labelled
relative path, and described with the same epistemic boundary recorded in the
figure registry. Rendering and rendered-output validation belong to that
external engine, cloned wherever you like (see `development.md`); do not
hand-edit generated PDF, HTML, or report files.
