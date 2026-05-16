---
name: mplus
description: Generate correct, runnable Mplus `.inp` syntax for any structural equation modeling, latent variable, multilevel, mixture, or longitudinal analysis the user describes. Use this skill whenever the user mentions Mplus, Muthen, .inp files, or any of these analyses (even if Mplus isn't named explicitly): SEM, structural equation modeling, CFA, confirmatory factor analysis, EFA, exploratory factor analysis, ESEM, latent variables, path analysis, mediation, moderation, moderated mediation, indirect effects, bootstrap confidence intervals, LGM, latent growth curve, growth modeling, growth mixture, GMM, LCGA, LCA, latent class analysis, LPA, latent profile analysis, factor mixture, LTA, latent transition, RI-LTA, multilevel SEM, two-level CFA, HLM, cross-classified, multilevel mediation, measurement invariance, configural/metric/scalar invariance, MGCFA, multiple-group CFA, MIMIC, alignment, BSEM, Bayesian SEM, informative priors, RI-CLPM, random intercept cross-lagged, DSEM, dynamic SEM, time-series SEM, intensive longitudinal, IRT, item response theory, 2PL, GRM, survival analysis, Cox regression, discrete-time survival, missing data, FIML, multiple imputation, Monte Carlo simulation, power analysis, sample size planning. Use this skill any time the user asks for help writing, debugging, or interpreting Mplus syntax — including translating R/lavaan, SAS PROC CALIS, or AMOS specifications into Mplus.
---

# Mplus syntax skill

This skill helps you write correct, runnable Mplus `.inp` files for any analysis the user requests. Mplus has its own quirky DSL — block-based, semicolon-terminated, and order-sensitive — so the most common failure mode is not "wrong statistics" but "wrong syntax that won't compile or that silently fits the wrong model". This skill closes that gap by routing every request to a vetted template.

## How to use this skill

1. **Read the user's request** and identify the analysis family. Pick the most specific match from the routing table below.
2. **Read the matching reference file** in `references/`. Each one contains: a decision tree, a minimal skeleton, a fully annotated example, common variants, and pitfalls.
3. **Adapt the template** to the user's variable names and structure. Do not paste in placeholder text — replace `y1-y6`, `x`, `clus`, etc. with the user's actual variable names.
4. **Always include `references/syntax-fundamentals.md`** when generating any `.inp`. It is short and contains the universal rules (block order, operator semantics, naming) that every Mplus program obeys.
5. **If the user gives you raw data**, also read `references/data-preparation.md` — Mplus is fussy about file format, missing codes, and categorical declarations.
6. **For canonical full-file examples**, point the user to `assets/examples/` and name a specific file. Do not regurgitate the example — Mplus syntax is small enough that a tailored skeleton beats a dumped canonical file.

## Routing table

Match the user's situation to the most specific row. If unsure between two rows, read both — you can always discard one. When multiple analyses combine (e.g. multilevel growth mixture), read each component reference.

| User says / situation | Read this reference |
|---|---|
| OLS regression, logistic regression, probit, censored/count outcome, simple path analysis with observed variables, bootstrap indirect effect on observed variables | `references/regression-path.md` |
| Exploring factor structure, "how many factors", ESEM with target rotation, bifactor EFA | `references/efa.md` |
| Measurement model with hypothesized factors; CFA; latent SEM (regressions among latents); MIMIC; multiple-group CFA / measurement invariance; latent interactions; bifactor CFA | `references/cfa-sem.md` |
| Indirect effects involving latent variables, moderated mediation, conditional indirect effects, the "a × b" pattern with bootstrap or Bayesian CI, MEDIATION via XWITH | `references/mediation-moderation.md` |
| Latent growth curve / LGM (linear, quadratic, free time scores), multiple-indicator growth, parallel-process growth, growth with TI / TV covariates, continuous- or discrete-time survival | `references/growth-survival.md` |
| Latent class analysis (binary/ordinal indicators), latent profile analysis (continuous indicators), factor mixture, mover-stayer, K-class enumeration, distal outcomes (BCH / 3-step), LCA with covariates | `references/lca-lpa.md` |
| Growth mixture model (GMM), latent class growth analysis (LCGA), latent transition analysis (LTA), multi-process LTA, parallel-process GMM | `references/mixture-longitudinal.md` |
| Two-level (random intercept / random slope) regression, two-level CFA / SEM, three-level / cross-classified models, multilevel growth, 1-1-1 mediation with latent centering | `references/multilevel.md` |
| Two-level mixture, multilevel LCA, multilevel growth mixture, between- vs within-level classes | `references/multilevel-mixture.md` |
| FIML with missing data, AUXILIARY variables for MAR, multiple imputation (generation + analysis on TYPE=IMPUTATION), Bayesian estimation (ESTIMATOR=BAYES), posterior predictive p-values, informative priors, plausible values | `references/missing-bayesian.md` |
| Monte Carlo simulation, power analysis, sample size determination, MODEL POPULATION vs MODEL, external-data MC | `references/monte-carlo.md` |
| RI-CLPM (random intercept cross-lagged), RI-LTA, BSEM with small-variance priors on cross-loadings, ESEM-within-CFA, alignment for many-group invariance, DSEM / RDSEM / TVEM (intensive longitudinal), IRT (2PL/GRM), latent moderated structural equations (XWITH) | `references/special-features.md` |
| Mplus printed an error, a warning, or fit a model with bizarre estimates; convergence failed; identification problems; non-positive-definite matrix | `references/common-errors.md` |

## Mandatory practice

1. **Generate complete, runnable files.** Always include TITLE, DATA, VARIABLE, and MODEL blocks. Even a one-line CFA needs them. Half-files cause more confusion than they save.
2. **Use lowercase variable names with hyphenated ranges** (`y1-y6`, `x1-x4`, `u1-u10`). Mplus is case-insensitive, but the entire User's Guide uses lowercase. Don't fight it.
3. **Declare categorical / nominal / count / censored / survival outcomes in VARIABLE**, not by inference. Mplus silently treats undeclared variables as continuous. Wrong declaration → wrong estimator → wrong results.
4. **State the estimator the user gets, even if it's the default.** If you write a categorical CFA without `ESTIMATOR =`, Mplus uses WLSMV. Tell the user that. Surprises cost trust.
5. **Match block order:** TITLE → DATA → VARIABLE → DEFINE → ANALYSIS → MODEL → MODEL INDIRECT / MODEL CONSTRAINT → OUTPUT → SAVEDATA → PLOT. Mplus parses top-to-bottom; misordered blocks fail.
6. **Comment with `!` only where the syntax is genuinely non-obvious** (e.g., why a residual is fixed at 0, what a labeled constraint means). Don't add `! this is the CFA model` — the TITLE already says that.
7. **When in doubt about a specific advanced syntax**, look in `assets/examples/` for the closest canonical file from Muthén & Muthén — the official User's Guide examples are the ground truth.

## Variable-naming and scoping rules (universal)

These appear in every Mplus program. Internalize them before you start writing:

- Names are 1–8 characters, alphanumeric + underscore, case-insensitive. `f1_lat` and `F1_LAT` refer to the same variable.
- Ranges: `y1-y6` expands to `y1 y2 y3 y4 y5 y6`. Works only when the prefix is identical and the suffix is a contiguous integer sequence.
- `NAMES` in VARIABLE must list **every column in the data file**, in order. Anything you don't analyze still needs to be named.
- `USEVARIABLES` (alias `USEV`) is the subset you actually analyze. If omitted, Mplus uses all NAMES. Variables omitted from USEVARIABLES are dropped from FIML — use `AUXILIARY = (m) name` to keep them as missing-data correlates.
- `MISSING` declares the code for missing. Default is the dot `.`; declare explicitly only for numeric codes (`MISSING = ALL (-99);`).
- Variables can appear only in **one** of `WITHIN`, `BETWEEN`, both, or neither — Mplus errors otherwise. Predictors that go on both levels are listed in neither.

## A note on tone

Mplus users span first-time grad students to seasoned methodologists. Default to brief, code-forward responses: a short paragraph explaining what the model does, the `.inp` file, and a list of "things to check / common variations" — not a textbook chapter on SEM. If the user clearly wants depth, expand; if they're debugging, focus on the minimal diff.
