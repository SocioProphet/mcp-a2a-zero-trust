# Issue Standard

Every issue must include:

1) **Definition of Done (DoD)** — completion checklist
2) **Acceptance Criteria** — reviewer-verifiable outcomes (Given/When/Then preferred)

Recommended:
- **Test Evidence** — commands + expected outputs used in review

## Enforcement

- New issues opened via GitHub's "New issue" picker use one of the forms in
  `.github/ISSUE_TEMPLATE/` (`01-backlog-item.yml`, `02-bug.yml`); both already carry
  required `Definition of Done (DoD)` and `Acceptance Criteria` fields, so those headings
  are always present in the rendered body. `blank_issues_enabled: false` in
  `.github/ISSUE_TEMPLATE/config.yml` means the blank-issue option isn't offered.
- `.github/workflows/audit_issues.yml` independently checks every issue's body for both
  section headings (via `hasRequired()`), and runs on `workflow_dispatch`, the daily
  `schedule`, and now `issues: [opened, edited]` — so an issue created or edited outside
  the form (e.g. via the API) is still caught immediately rather than only on the next
  scheduled sweep.
