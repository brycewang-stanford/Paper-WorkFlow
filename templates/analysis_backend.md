# Analysis Backend

Project: <short name>
Selected at (Beijing): <YYYY-MM-DD HH:MM>

## 1. Backend Choice

- Primary backend: python-statspai / stata / r
- Secondary validation backend: none / python-statspai / stata / r
- Reason for choice:
- Expected script pattern: 03_analysis/<script>.py / 03_analysis/<script>.do / 03_analysis/<script>.R
- Child skill or route:

## 2. Environment Check

| Tool | Required for selected backend? | Version / status | Notes |
|---|---:|---|---|
| Python / StatsPAI MCP or package | no | pending |  |
| Stata executable and packages | no | pending |  |
| R / renv / Quarto packages | no | pending |  |
| Table export stack | yes | pending | Word / Excel / LaTeX support |
| Figure export stack | yes | pending | PDF + PNG at 300 dpi |

## 3. Output Contract

| Artifact | Expected path | Backend owner |
|---|---|---|
| Main estimation script | 03_analysis/<script> |  |
| Main results JSON | 03_analysis/results/main_results.json |  |
| Method diagnostics | 03_analysis/results/<diagnostic> |  |
| Robustness artifacts | 03_analysis/robustness/ |  |
| Table build script | 03_analysis/build_exhibits.<ext> |  |
| Tables | 04_results/*.{tex,docx,xlsx} |  |
| Figures | 04_results/*.{pdf,png} |  |

## 4. Fallback

- Missing dependency:
- Fallback backend:
- Artifact parity checked: yes / no
- Gate impact:
