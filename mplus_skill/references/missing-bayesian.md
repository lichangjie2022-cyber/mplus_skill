# Missing data and Bayesian estimation (User's Guide Ch. 11)

Two related topics often treated together because Bayesian estimation handles missing data through MCMC imputation and produces credibility intervals that don't require asymptotic normality. This reference covers FIML, AUXILIARY for MAR, multiple imputation (data generation and analysis), Bayesian SEM, informative priors, and plausible-value imputation.

## Decision tree

```
User has missing data and wants...
├─ MAR-based likelihood (default for most cases)
│   → FIML, automatically activated with ESTIMATOR = ML/MLR/MLM when MISSING = ALL (code) is set
├─ Boost MAR plausibility with auxiliary correlates
│   → AUXILIARY = (m) z1 z2;
├─ Imputation pipeline (analyze with non-FIML methods or pool across multiple analyses)
│   → DATA IMPUTATION block (generate) + DATA: TYPE = IMPUTATION (analyze)
├─ NMAR / sensitivity analysis
│   → DATA MISSING block with TYPE = SDROPOUT (selection) or DDROPOUT (pattern-mixture)
└─ Bayesian inference (regardless of missingness)
    → ESTIMATOR = BAYES + PROCESSORS = N + FBITERATIONS = K + BSEED = seed
```

## FIML — the easy path

If you only have continuous data and the missingness can be assumed MAR, FIML is automatic:

```
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y4 x1-x3;
          MISSING = ALL (-99);       ! tell Mplus what means "missing"
ANALYSIS: ESTIMATOR = ML;            ! activates FIML automatically when MISSING is set
MODEL:    f BY y1-y4;
          f ON x1-x3;
```

FIML uses all available data for each parameter — observations with missing y2 contribute to estimation of all parameters except those needing y2.

### Caveats with FIML

1. **Missing on exogenous observed predictors drops cases.** If `x1` is missing for some rows and `x1` is purely a predictor (never an outcome of an equation), those rows are dropped because Mplus doesn't have a likelihood for `x1`. Workarounds:
   - Add a saturated model for x1: `[x1]; x1;` in MODEL.
   - Use AUXILIARY to keep them as MAR correlates.
   - Switch to multiple imputation.
2. **WLSMV does not use FIML.** WLSMV with `CATEGORICAL` uses pairwise present (effectively listwise on each bivariate). For categorical FIML, use `ESTIMATOR = ML; LINK = LOGIT;` (slower but uses all data).
3. **Bayesian estimation always uses all data** (MCMC imputes on the fly). For missing categorical outcomes, BAYES is often the easiest route.

## AUXILIARY variables for MAR plausibility

Variables not in your model but correlated with both `y` and the missingness mechanism can be added as auxiliary correlates:

```
VARIABLE: NAMES = y1-y4 x1-x3 z1 z2;
          USEVARIABLES = y1-y4 x1-x3;
          AUXILIARY = (m) z1 z2;    ! z1, z2 used to improve MAR plausibility
          MISSING = ALL (-99);
```

Mplus adds saturated covariances among AUXILIARY variables and all USEVARIABLES, raising the auxiliary's contribution to the likelihood **without changing the substantive model**. This is the Graham (2003) "saturated correlates" approach.

`AUXILIARY = (e)` is a different option — adds `z` to the **estimated mean and variance** matrix (extra dependent variables). Less common.

## Multiple imputation

Two-step workflow: (1) generate imputations, (2) analyze with TYPE = IMPUTATION.

### Step 1: generate imputations (Mplus DATA IMPUTATION)

```
TITLE:    impute missing data
DATA:     FILE = raw.dat;
VARIABLE: NAMES = y1-y4 x1-x3 z1 z2;
          USEVARIABLES = y1-y4 x1-x3 z1 z2;
          MISSING = ALL (-99);
DATA IMPUTATION:
          IMPUTE = y1-y4 x1-x3 (c) z1 z2;    ! (c) flags categorical vars to impute
          NDATASETS = 20;                     ! 20 imputations (rule of thumb: ≥ 20)
          SAVE = myimp*.dat;                  ! writes myimp1.dat .. myimp20.dat + a list file
ANALYSIS: TYPE = BASIC;                       ! TYPE = BASIC just imputes, no model
OUTPUT:   TECH8;
```

After this run, Mplus produces `myimp1.dat`, `myimp2.dat`, ..., `myimp20.dat`, plus a list file `myimplist.dat` containing those filenames one per line.

### Step 2: analyze on the imputed datasets

```
TITLE:    analysis on multiply-imputed data
DATA:     FILE = myimplist.dat;
          TYPE = IMPUTATION;                  ! triggers pooling
VARIABLE: NAMES = y1-y4 x1-x3 z1 z2;
ANALYSIS: ESTIMATOR = ML;
MODEL:    f BY y1-y4;
          f ON x1-x3;
OUTPUT:   STDYX;
```

Mplus runs the model on each imputed dataset, then pools per Rubin's rules. Reported standard errors include between-imputation variance.

### Importing imputations from elsewhere (R mice, SAS PROC MI, Stata mi)

Save each imputation to a separate `imp1.dat`, `imp2.dat`, ... text file (no header, same format as any Mplus data file). Create a text file `mylist.dat` listing the filenames one per line. Then:

```
DATA:     FILE = mylist.dat;
          TYPE = IMPUTATION;
```

### When MI beats FIML

- Categorical outcomes that can't use FIML
- Auxiliary variables you want to use repeatedly across multiple analyses (impute once, analyze many times)
- Combination of variables that's hard to fit in a single FIML model

## NMAR — selection and pattern-mixture models

For sensitivity analysis when MAR is questionable.

### Selection model (Diggle-Kenward)

Missingness depends on the unobserved value of the outcome:

```
DATA MISSING:
          NAMES = y1-y5;
          TYPE = SDROPOUT;            ! Selection (dropout depends on unobserved y)
          BINARY = d1-d5;             ! dropout indicators (1 = missing thereafter)
ANALYSIS: ALGORITHM = INTEGRATION;
MODEL:    i s | y1@0 y2@1 y3@2 y4@3 y5@4;
          d1 ON y0 (1) y1 (2);        ! dropout d_t depends on y at t-1 and t
          d2 ON y1 (1) y2 (2);
          d3 ON y2 (1) y3 (2);
          d4 ON y3 (1) y4 (2);
          d5 ON y4 (1) y5 (2);
```

### Pattern-mixture model

Missingness pattern *defines* a grouping; model varies by pattern:

```
DATA MISSING:
          NAMES = y1-y5;
          TYPE = DDROPOUT;            ! Dropout as known class
          BINARY = d1-d5;
MODEL:    i s | y1@0 y2@1 y3@2 y4@3 y5@4;
          i ON d1-d5;                  ! intercept depends on dropout pattern
          s ON d3-d5;
```

## Bayesian estimation

### Basics

```
ANALYSIS: ESTIMATOR = BAYES;
          PROCESSORS = 4;             ! parallel MCMC chains
          FBITERATIONS = 10000;        ! min post-burn-in iterations
          BCONVERGENCE = 0.05;         ! PSRF threshold (default; smaller = stricter)
          BSEED = 54321;               ! random seed (always set for reproducibility)
MODEL:    f BY y1-y6;
          f ON x;
OUTPUT:   STDYX TECH8;
PLOT:     TYPE = PLOT2;                ! trace plots for convergence diagnosis
```

`TECH8` reports the potential scale reduction factor (PSRF, Gelman-Rubin diagnostic). PSRF close to 1.00 = converged; > 1.05 = problematic.

### Bayesian fit indices

- **PPP** (posterior predictive p-value): closer to 0.5 = better fit. < 0.05 or > 0.95 = poor fit. Printed in MODEL FIT section.
- **DIC** (deviance information criterion): comparison across models; lower is better.
- **BIC** (printed): use cautiously for Bayesian models.

### Convergence diagnostics

1. PSRF < 1.05 for all parameters.
2. Trace plots (`PLOT: TYPE = PLOT2;`) show stationary mixing, not trends.
3. Run multiple chains (Mplus does this with PROCESSORS) and check that chains converge to the same posterior.
4. If non-convergence: increase FBITERATIONS to 50000+ or simplify model.

### Informative priors (`MODEL PRIORS`)

```
MODEL:    f1 BY y1-y6*;
          f2 BY y1-y6*;
          ! cross-loadings on secondary factors
          f1 BY y4-y6 (cross1-cross3);
MODEL PRIORS:
          cross1-cross3 ~ N(0, 0.01);   ! small-variance priors → "nearly-zero" cross-loadings
```

This is the BSEM pattern (Muthén & Asparouhov 2012). See `references/special-features.md`.

Other prior types:
- `~ N(mean, var)` — normal
- `~ IG(shape, scale)` — inverse-gamma (for variances)
- `~ IW(D, df)` — inverse-Wishart (for covariance matrices)
- `~ U(a, b)` — uniform
- `~ G(shape, scale)` — gamma

## Plausible values (saving)

For multiply-imputed factor scores or item responses:

```
SAVEDATA: FILE = plaus.dat;
          SAVE = FSCORES(20) LRESPONSES;    ! 20 plausible values per factor + latent responses
          IDVARIABLE = id;
```

These can be analyzed with TYPE = IMPUTATION in a follow-up run.

## Complete annotated example — Bayesian CFA + MI

```
TITLE:    Bayesian multiple-indicator growth, multiple imputation
          ex11.7 pattern

DATA:     FILE = ex11.7.dat;
VARIABLE: NAMES = u11 u21 u31 u12 u22 u32 u13 u23 u33;
          CATEGORICAL = u11-u33;            ! 9 ordinal items, 3 waves
ANALYSIS: ESTIMATOR = BAYES;
          PROCESSORS = 2;
MODEL:
          f1 BY u11
                u21-u31 (1-2);              ! loadings invariant across waves
          f2 BY u12
                u22-u32 (1-2);
          f3 BY u13
                u23-u33 (1-2);
          [u11$1 u12$1 u13$1] (3);           ! thresholds invariant
          [u21$1 u22$1 u23$1] (4);
          [u31$1 u32$1 u33$1] (5);
          i s | f1@0 f2@1 f3@2;              ! growth on latent factors

DATA IMPUTATION:
          NDATASETS = 20;
          SAVE = ex11.7imp*.dat;             ! save 20 imputed datasets

OUTPUT:   TECH1 TECH8;

SAVEDATA: FILE = ex11.7plaus.dat;
          SAVE = FSCORES(20) LRESPONSES;     ! 20 plausible values per latent score
```

## Pitfalls

1. **FIML silently disabled.** If MISSING is not declared, Mplus may listwise-delete. Always declare `MISSING = ALL (-99);` (or whatever your code is) explicitly.
2. **Categorical FIML.** WLSMV doesn't do FIML — only pairwise-present. For full likelihood on categorical, use ML with LINK and INTEGRATION (slow) or Bayesian.
3. **Auxiliary variables that overlap USEVARIABLES.** Listing a variable in both is an error; Mplus warns.
4. **Imputation list file format.** The list file is a plain text file with one filename per line. No header, no quotes, no commas.
5. **Pooling results.** With `TYPE = IMPUTATION`, output is the pooled estimate; per-imputation results are not shown by default. Use `OUTPUT: TECH1;` to confirm structure.
6. **Bayesian convergence false positives.** PSRF < 1.05 is necessary but not sufficient. Check trace plots and run with different seeds. If posterior credibility intervals are very wide, increase FBITERATIONS.
7. **Diffuse priors with small N.** Diffuse default priors on variances (e.g., IG(-1, 0)) can produce unstable estimates with small N. Use weakly informative priors (e.g., IG(1, 0.5)) for small samples.
8. **BAYES + complex models.** Convergence can be slow; consider using ML for initial model selection and BAYES for final inference.
9. **Plausible values vs FSCORES default.** `SAVE = FSCORES;` (no number) saves point estimates and SEs (regression scoring). `SAVE = FSCORES(K);` saves K plausible values per observation, sampling from the posterior — appropriate for multiply-imputed secondary analysis.

## Canonical examples in `assets/examples/`

- `ex11.6_multiple_imputation_growth.inp` — generate and analyze MI with growth model
- `ex11.7_bayesian_multi_indicator_growth.inp` — Bayesian + MI + multiple-indicator growth with invariance
