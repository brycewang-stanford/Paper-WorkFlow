#!/usr/bin/env python3
"""Execute data-to-DOCX acceptance cases in isolation (no network, no real study claims).

This is an integration exercise, not an LLM behavior/academic-quality score.
Requires requirements-dev.txt; Pandoc cases execute when available and are reported
as skipped otherwise. --require-pandoc makes that skip a failure for CI.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import assemble_manuscript_docx as assembler
import check_deliverable_contract as deliverable

ANALYSIS = '''import json
from pathlib import Path
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
w = Path(__file__).resolve().parents[1]
df = pd.read_csv(w / "02_data/raw/survey.csv")
assert not df["respondent"].duplicated().any()
sample = df.dropna(subset=["score", "assigned"])
fit = sm.OLS(sample.score, sm.add_constant(sample.assigned)).fit(cov_type="HC2")
ci = fit.conf_int().loc["assigned"].tolist()
r = {"estimate": float(fit.params["assigned"]), "se": float(fit.bse["assigned"]),
     "ci": ci, "n": int(fit.nobs), "raw_n": len(df), "model": "OLS ITT, HC2",
     "data_kind": "synthetic software acceptance fixture"}
(w / "03_analysis/results/main_results.json").write_text(json.dumps(r, indent=2))
pd.DataFrame([["Assigned treatment", f"{r['estimate']:.6f}", f"{r['se']:.6f}"],
              ["N", str(r['n']), ""]], columns=["Term", "Estimate", "SE"]).to_csv(
              w / "04_results/main.csv", index=False)
fig, ax = plt.subplots(figsize=(5.4, 2.4))
ax.errorbar([r["estimate"]], [0], xerr=[[r["estimate"]-ci[0]], [ci[1]-r["estimate"]]], fmt="o", capsize=5)
ax.axvline(0, color="gray", linestyle="--"); ax.set_yticks([0], ["Assigned treatment"])
ax.set_xlabel("Score difference with 95% confidence interval")
fig.tight_layout(); fig.savefig(w / "04_results/effect.png", dpi=160); plt.close(fig)
'''
PLAN = '''# Pre-Registration & Analysis Plan
## Lock Status
- locked: software fixture plan version 1
- lock_commit: n/a
- locked_before_estimation: yes
- analyst: deterministic acceptance script, not a human study
- primary_design: synthetic individual randomized assignment
## Confirmatory Hypotheses
| ID | Hypothesis | Outcome (Y) | Estimand | Primary specification | Predicted sign |
|---|---|---|---|---|---|
| H1 | assigned intervention raises score | score | ITT | OLS, HC2 | positive |
## Primary Specification Lock
- main estimator: OLS with assigned treatment and intercept
- standard errors: HC2; independent individuals in synthetic DGP
- multiple-testing: one outcome, no multiplicity adjustment
## Confirmatory vs Exploratory
- E1: missingness diagnostic, exploratory, all rows retained in raw data
## Deviations from Plan
- None in this software fixture. This is not an externally registered study.
'''

def command(args, *, expected=0):
    proc = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    if expected == 0:
        assert proc.returncode == 0, (args, proc.stdout[-3000:], proc.stderr[-3000:])
    else:
        assert proc.returncode != 0, ('unexpected success', args, proc.stdout)
    return proc


def exercise(root: Path, *, require_pandoc: bool):
    ws = root / '研究 空间'
    subprocess.run(['bash', str(ROOT / 'assets/init_workspace.sh'), str(ws)], check=True, capture_output=True)
    state_path = ws / '00_meta/workflow_state.json'
    fresh = command([ROOT/'scripts/pw.py', '--json', 'check', ws])
    assert json.loads(fresh.stdout)['ok'], 'a pending workspace should not owe final submission gates'
    state = json.loads(state_path.read_text())
    state['manuscript']['format'] = 'markdown'
    state['design_lock'].update(status='locked', locked_before_estimation=True, confirmatory_count=1)
    state_path.write_text(json.dumps(state))
    (ws / '00_meta/preregistration.md').write_text(PLAN)
    # idea entry: a plan exists before the synthetic input is generated.
    (ws / '01_proposal/proposal.md').write_text('Synthetic training assignment and scores; test the software pipeline, not a substantive claim.')
    rng = random.Random(20260910)
    rows = []
    for i in range(160):
        assigned = i % 2
        score = 30 + 1.5 * assigned + rng.gauss(0, 4)
        rows.append([i, assigned, '' if i in {9, 40, 83} else score])
    raw = ws / '02_data/raw/survey.csv'
    with raw.open('w', newline='') as f:
        writer = csv.writer(f); writer.writerow(['respondent', 'assigned', 'score']); writer.writerows(rows)
    original_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    (ws / '02_data/sample_audit.md').write_text('160 synthetic rows; 3 missing scores; complete-case sample 157; no duplicate respondent IDs.')
    (ws / '02_data/codebook.md').write_text('respondent: unique ID; assigned: randomized assignment; score: synthetic points.')
    (ws / '03_analysis/design_register.md').write_text('ITT score difference, independent individuals, OLS HC2, artificial data only.')
    plan_hash = hashlib.sha256((ws / '00_meta/preregistration.md').read_bytes()).hexdigest()
    entry = command([ROOT / 'scripts/pw.py', '--json', 'enter', '3', ws])
    assert json.loads(entry.stdout)['ok']
    script = ws / '03_analysis/estimate.py'; script.write_text(ANALYSIS)
    command([script])
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == original_hash
    assert hashlib.sha256((ws / '00_meta/preregistration.md').read_bytes()).hexdigest() == plan_hash
    result_path = ws / '03_analysis/results/main_results.json'
    result = json.loads(result_path.read_text())
    # Independent algebraic oracle; does not reuse the statsmodels model.
    groups = [[float(r[2]) for r in rows if r[1] == k and r[2] != ''] for k in (0, 1)]
    means = [sum(g)/len(g) for g in groups]
    variance = [sum((x-m)**2 for x in g)/(len(g)-1) for g,m in zip(groups,means)]
    expected_se = (sum(v/len(g) for v,g in zip(variance,groups)))**0.5
    assert abs(result['estimate'] - (means[1]-means[0])) < 1e-10
    assert abs(result['se'] - expected_se) < 1e-10 and result['n'] == 157
    # Rebuild from raw produces identical result values.
    command([script]); assert json.loads(result_path.read_text()) == result
    # Real verified method source, not an invented reference for our artificial study.
    (ws / '05_draft/ref.bib').write_text('''@article{white1980,
 author={White, Halbert}, title={A Heteroskedasticity-Consistent Covariance Matrix Estimator and a Direct Test for Heteroskedasticity},
 journal={Econometrica}, year={1980}, volume={48}, number={4}, pages={817--838}, doi={10.2307/1912934}}
''')
    body = f'''# Synthetic survey analysis acceptance specimen

## Purpose and research question

This document exercises the data-to-paper software path using generated records. It is not a completed empirical study and offers no real-world policy conclusion. The question concerns assignment and a synthetic score; observations do not represent actual people. Data access, ethics review, literature positioning, and substantive identification have not been certified by this fixture.

## Data and analysis

The generated input contains {result['raw_n']} rows. After excluding three missing outcomes, the analysis uses {result['n']} rows. The assignment contrast is {result['estimate']:.6f} score points with an HC2 standard error of {result['se']:.6f}. The independent difference-in-means computation agrees with the regression. Missingness is deliberately included to exercise the sample accounting path. These numbers describe only this fixture.

{{{{ include: main.csv }}}}

![Synthetic assignment contrast](effect.png)

## Limitations and conclusion

The input is synthetic, the design is simplified, and a successful build says nothing about publication quality. Further scientific review would be required before making substantive claims. The example verifies that a recorded sample and an executed script can supply consistent values to prose, tables, and a figure. All method and submission readiness gates remain pending.
'''
    source = ws / '05_draft/main.md'; source.write_text(body)
    built = assembler.run(ws, converter='builtin'); assert built['ok'], built
    docx = ws / '09_submission/main.docx'
    assert not deliverable.evaluate(ws, strict=True).failures
    assert f"{result['estimate']:.6f}" in assembler.docx_text(docx)
    old = docx.read_bytes(); old_state = state_path.read_bytes()
    source.write_text(body + '\n{{ include: missing.csv }}\n')
    failed = assembler.run(ws, converter='builtin')
    assert not failed['ok'] and docx.read_bytes() == old and state_path.read_bytes() == old_state
    assert any(c == 'freshness:inputs' for _,c,_ in deliverable.evaluate(ws, strict=True).failures)
    source.write_text(body)
    table = ws / '04_results/main.csv'; table_text = table.read_text()
    table.write_text(table_text.replace(f"{result['estimate']:.6f}", '999.000000'))
    assert any(c == 'freshness:inputs' for _,c,_ in deliverable.evaluate(ws, strict=True).failures)
    table.write_text(table_text)
    with zipfile.ZipFile(docx) as z: parts = {n: z.read(n) for n in z.namelist()}
    parts['word/document.xml'] = parts['word/document.xml'].replace(b'95%', b'90%') + b'\n'
    with zipfile.ZipFile(docx, 'w') as z:
        for n,b in parts.items(): z.writestr(n,b)
    assert any(c == 'freshness:output' for _,c,_ in deliverable.evaluate(ws, strict=True).failures)
    assert assembler.run(ws, converter='builtin')['ok']

    # Runtime CLI must emit exactly one JSON document for failed as well as passed gates.
    route = ws/'00_meta/entry_routing.md'
    routing_text = route.read_text(); route.unlink()
    for argv in [('enter','999'), ('enter','1L'), ('exit','3')]:
        p = command([ROOT/'scripts/pw.py', '--json', *argv, ws], expected=1)
        assert not json.loads(p.stdout)['ok']
    route.write_text(routing_text)
    p = command([ROOT/'scripts/pw.py','--json','final',ws], expected=1)
    final = json.loads(p.stdout)
    assert any('--require-complete' in g['argv'] and not g['ok'] for g in final['gates'])
    # Markdown entry: no phantom main.tex is required.
    (ws/'06_polish/main.md').write_text(body)
    command([ROOT/'scripts/pw.py','--json','enter','7',ws])

    # Existing-results entry must be honest and still allowed to analyze.
    retrospective = PLAN.replace('locked_before_estimation: yes','locked_before_estimation: no')
    retrospective = retrospective.replace('## Lock Status', '''## Lock Status
- analysis_mode: retrospective
- prior_results_seen: the supplied fixture results have already been inspected
- analysis_history: one OLS specification; raw data and code preserved
- prospective_validation: none; current-data results remain exploratory''')
    retrospective = '\n'.join(line for line in retrospective.splitlines() if not line.startswith('| H1'))
    (ws/'00_meta/preregistration.md').write_text(retrospective)
    state = json.loads(state_path.read_text());state['design_lock'].update(status='retrospective',locked_before_estimation=False,confirmatory_count=0)
    state_path.write_text(json.dumps(state))
    command([ROOT/'scripts/check_preregistration.py',ws])
    command([ROOT/'scripts/pw.py','--json','enter','3',ws])
    state['design_lock']['locked_before_estimation']=True;state_path.write_text(json.dumps(state))
    command([ROOT/'scripts/check_preregistration.py',ws],expected=1)
    command([ROOT/'scripts/pw.py','--json','enter','3',ws],expected=1)
    state['design_lock']['locked_before_estimation']=False;state_path.write_text(json.dumps(state))
    pandoc_status = 'skipped: pandoc unavailable'
    if assembler.pandoc_available():
        # data-entry rich manuscript: actual citeproc, math, footnotes, lists, and caption.
        rich = body + '''
## Method source and notation

Robust inference follows the variance-estimation literature [@white1980].

$$y_i = \\alpha + \\tau D_i + \\varepsilon_i$$

1. Preserve the raw data.
2. Report the complete-case sample.[^sample]

[^sample]: This is a synthetic missingness check, not a real attrition finding.
'''
        (ws/'06_polish/main.md').unlink(); source.write_text(rich)
        built=assembler.run(ws,converter='pandoc');assert built['ok'],built
        text=assembler.docx_text(docx)
        assert 'White' in text and '@white1980' not in text
        assert text.count('Heteroskedasticity-Consistent Covariance') == 1
        with zipfile.ZipFile(docx) as z:
            xml=z.read('word/document.xml').decode()
            assert 'oMath' in xml and 'numPr' in xml and 'footnoteReference' in xml
            assert b'synthetic missingness check' in z.read('word/footnotes.xml')
            ET.fromstring(xml)
        assert not deliverable.evaluate(ws,strict=True).failures
        before=docx.read_bytes()
        source.write_text(rich+'\nAn unresolved citation [@missing2026].\n')
        assert not assembler.run(ws,converter='pandoc')['ok'] and docx.read_bytes()==before
        source.write_text(rich)
        pandoc_status='passed: citations, one bibliography, math, footnote, list, space-containing workspace'
    elif require_pandoc:
        raise AssertionError('Pandoc is required but unavailable')
    return {'workspace':str(ws),'estimate':result['estimate'],'se':result['se'],'n':result['n'],
            'data_kind':'synthetic','submission_ready':False,'pandoc':pandoc_status,
            'verified':['raw immutability','independent numerical oracle','rebuild parity','DOCX embeds',
                        'atomic failure','source/table/DOCX drift','stage JSON and incomplete final rejection',
                        'Markdown entry','honest retrospective entry and contradiction rejection']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, help='new empty directory to retain the acceptance workspace')
    p.add_argument('--require-pandoc',action='store_true')
    args=p.parse_args()
    if args.output:
        args.output.mkdir(parents=True,exist_ok=False)
        report=exercise(args.output.resolve(),require_pandoc=args.require_pandoc)
        (args.output/'acceptance.json').write_text(json.dumps(report,indent=2))
    else:
        with tempfile.TemporaryDirectory(prefix='pw-acceptance-') as tmp:
            report=exercise(Path(tmp),require_pandoc=args.require_pandoc)
            report['workspace']='temporary (cleaned)'
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
