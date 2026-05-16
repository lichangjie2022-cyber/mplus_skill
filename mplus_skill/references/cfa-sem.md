# CFA, SEM, and measurement invariance (User's Guide Ch. 5)

The largest and most-used family. This reference covers confirmatory factor analysis (CFA), structural equation models with latent variables (SEM), latent-variable interactions (XWITH), bifactor CFA, second-order CFA, multiple-group CFA, measurement invariance (configural / metric / scalar / strict), and MIMIC models.

## Decision tree

```
User has hypothesized latent factor structure...
├─ Single group, continuous indicators → basic CFA
├─ Single group, categorical indicators → CATEGORICAL =, ESTIMATOR=WLSMV (default)
├─ Latent regressions (factor → factor) → SEM
├─ Latent × observed interaction → XWITH operator
├─ Multiple groups, same model
│   ├─ Asking "are loadings/intercepts equal across groups?" → measurement invariance ladder
│   ├─ Want covariates to predict latent → MIMIC
│   └─ Many groups (>10), too many to invariance-test → alignment (see special-features.md)
├─ One general factor + several specific factors → bifactor
├─ Factors at two strata (e.g., facets → domains → general) → second-order CFA
└─ Need to keep exploring loadings → ESEM (see special-features.md)
```

## Skeletons

### Basic CFA, continuous indicators
```
TITLE:    two-factor CFA
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y6;
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
OUTPUT:   STDYX MODINDICES(10);
```

This is `ex5.1`. By default:
- First loading per factor fixed at 1 (`y1`, `y4`)
- Other loadings free
- Factor variances free
- Factor means at 0
- Factor covariance free
- Residual variances free
- Residual covariances 0 (request `y1 WITH y2;` to free)

### CFA with categorical indicators
```
VARIABLE: NAMES = u1-u6;
          CATEGORICAL = u1-u6;
MODEL:    f1 BY u1-u3;
          f2 BY u4-u6;
OUTPUT:   STDYX;
```

Defaults change:
- ESTIMATOR = WLSMV (mean- and variance-adjusted weighted least squares)
- Thresholds estimated instead of intercepts
- PARAMETERIZATION = DELTA (default; scales residual variances)

### SEM with latent regressions
```
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          f3 BY y7-y9;
          f3 ON f1 f2;          ! structural equation: f3 depends on f1, f2
          f1 WITH f2;            ! covariance among exogenous latents
OUTPUT:   STDYX;
```

### SEM with observed covariates (MIMIC)
```
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          f1 f2 ON x1-x3;        ! exogenous covariates → latent factors
OUTPUT:   STDYX;
```

### CFA with correlated residuals
```
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          y1 WITH y4;            ! residuals of y1 and y4 covary (common method)
```

### Higher-order (second-order) CFA
```
MODEL:    f1 BY y1-y3;           ! first-order factors
          f2 BY y4-y6;
          f3 BY y7-y9;
          g BY f1 f2 f3;         ! second-order general factor
```

### Bifactor CFA (one general + several specific, all orthogonal)
```
MODEL:    g BY y1-y9;            ! general factor: all items load
          s1 BY y1-y3;           ! specific factor 1
          s2 BY y4-y6;           ! specific factor 2
          s3 BY y7-y9;
          g WITH s1@0 s2@0 s3@0; ! orthogonality (some users use ROTATION instead)
          s1 WITH s2@0 s3@0;
          s2 WITH s3@0;
```

### Latent interaction (XWITH)
```
ANALYSIS: TYPE = RANDOM;
          ALGORITHM = INTEGRATION;
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          f3 BY y7-y9;
          f1xf2 | f1 XWITH f2;   ! create the interaction latent
          f3 ON f1 f2 f1xf2;     ! main effects and interaction
OUTPUT:   STDYX;                  ! standardized output for moderation
```

XWITH requires `TYPE = RANDOM; ALGORITHM = INTEGRATION;` (numerical integration). Slow for many indicators; consider product-indicator alternatives if speed matters.

## Multiple-group CFA / measurement invariance

The standard sequence is **configural → metric → scalar → strict**, plus often **partial** invariance steps. Mplus 8+ has shortcut syntax for this.

### Long-form syntax (shows what's being tested)

**Configural** — same factor structure, all parameters free per group:
```
VARIABLE: NAMES = y1-y6 g;
          GROUPING = g (1=g1 2=g2);
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
! With GROUPING, every parameter is free per group by default.
! For identification, mean of factors is 0 in group 1; factor variance is 1 in group 1.
```

**Metric (loading) invariance** — constrain loadings:
```
MODEL:    f1 BY y1
                y2-y3 (lam2-lam3);    ! same labels → equality across groups
          f2 BY y4
                y5-y6 (lam5-lam6);
          [f1@0 f2@0];                 ! identify by fixing g1 factor means at 0
          ! intercepts of y still vary per group → metric only
```

**Scalar (intercept) invariance** — constrain intercepts too:
```
MODEL:    f1 BY y1
                y2-y3 (lam2-lam3);
          f2 BY y4
                y5-y6 (lam5-lam6);
          [y1-y3] (i1-i3);            ! intercepts equal across groups
          [y4-y6] (i4-i6);
          [f1@0 f2@0];                 ! g1 factor means at 0
MODEL g2:                              ! free g2 factor means
          [f1 f2];
```

**Strict (residual) invariance** — also constrain residual variances:
```
          y1-y6 (e1-e6);              ! residual variances equal across groups
```

### Shortcut syntax (Mplus 8.0+)

For continuous indicators only:
```
VARIABLE: NAMES = y1-y6 g;
          GROUPING = g (1=g1 2=g2);
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
ANALYSIS: MODEL = CONFIGURAL METRIC SCALAR;
```
This runs all three models and reports change in fit (Δχ², ΔCFI). Add `OUTPUT: STANDARDIZED;` for STDYX in each.

For categorical, use the same long-form approach but constrain **thresholds** instead of intercepts. With WLSMV, the default scalar test uses thresholds and loadings simultaneously per Wu & Estabrook (2016) recommendations.

### MIMIC (uniform DIF)
A faster alternative when groups are nominal and you want to test if observed covariates predict latent factors or individual items:
```
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          f1 f2 ON x g;                ! covariates and group dummy on factors
          y1 ON g;                     ! direct effect of group on y1 → uniform DIF on y1
```

If `y1 ON g;` is significant and substantial → y1 has DIF beyond what's captured by the factor.

### Partial invariance

If full invariance fails, free the worst-fitting constraint(s):
```
MODEL:    f1 BY y1
                y2 (lam2)
                y3 ;                  ! y3 loading freed across groups (partial metric)
```

Modification indices in the constrained model point to which equality constraints to release.

## ANALYSIS settings

**For continuous CFA / SEM:**
```
ANALYSIS: ESTIMATOR = ML;              ! default
          ESTIMATOR = MLR;             ! robust SE & rescaled chi-square for non-normal data
          ESTIMATOR = MLM;             ! Satorra-Bentler scaled chi-square (similar to MLR)
```

**For categorical CFA:**
```
ANALYSIS: ESTIMATOR = WLSMV;           ! default
          PARAMETERIZATION = DELTA;    ! default; scales residual variances
          PARAMETERIZATION = THETA;    ! residual variances free; required for some MGCFA setups
```

**For multi-group:**
```
ANALYSIS: MODEL = NOMEANSTRUCTURE;     ! covariance-only (skip mean structure if not testing it)
          INFORMATION = EXPECTED;      ! sometimes more stable than OBSERVED for MGCFA
```

**For latent interactions:**
```
ANALYSIS: TYPE = RANDOM;
          ALGORITHM = INTEGRATION;
          INTEGRATION = MONTECARLO(500);   ! reduces cost; default is GAUSSHERMITE
```

## Output options

**For CFA / SEM:**
```
OUTPUT:   SAMPSTAT STDYX MODINDICES(10) RESIDUAL CINTERVAL TECH4;
```

- `STDYX` — standardized factor loadings, regressions, correlations
- `MODINDICES(10)` — top modification indices (suggests freed parameters)
- `RESIDUAL` — observed vs. estimated covariance / mean
- `TECH4` — model-implied covariances and correlations among latents
- `CINTERVAL` — 95% CIs (BOOTSTRAP for bootstrap-based)

**For invariance testing:**
- `STANDARDIZED` (alias of STDYX STDY STD) — see all standardized forms
- `MODINDICES` — for partial invariance diagnosis

**For Bayesian SEM:** see `references/missing-bayesian.md` and `references/special-features.md`.

## Fit indices to interpret

| Index | Cutoff (rule of thumb) | Notes |
|---|---|---|
| χ² (model fit) | non-significant good | overpowered in large N; report alongside others |
| RMSEA | < .06 good, < .08 acceptable | with 90% CI |
| CFI / TLI | > .95 good, > .90 acceptable | incremental fit |
| SRMR | < .08 good (continuous) | standardized root-mean-square residual |
| WRMR | < 1.0 (categorical) | weighted root-mean-square residual |

Cutoffs are heuristics. Hu & Bentler 1999, Marsh et al., and many others critique them. Report all, discuss in context.

## Identifying the latent variable scale

Three equivalent identification choices for `f BY y1-y3`:
1. **Marker variable** (default): `f BY y1@1 y2-y3;` — fix first loading to 1, factor variance free.
2. **Standardized factor**: `f BY y1*-y3*; f@1;` — free all loadings, fix factor variance to 1.
3. **Effects coding** (Little, Slegers, Card 2006): constrain loadings to sum to k (number of indicators) — gives factor on the original indicator metric.

Marker variable is universal; standardized is needed for IRT-style identification (see `references/special-features.md`).

## Pitfalls

1. **Forgetting `STDYX` request.** Unstandardized loadings are in raw units — hard to compare. Always include for CFA/SEM.
2. **Default residual correlations are 0.** If a model fits poorly, MODINDICES often suggest `WITH` between two items in the same factor — fine if substantively defensible (e.g., near-identical wording).
3. **Multiple-group identification.** Default: in group 1, factor means are 0 and variances are 1; in other groups, free. To compare factor means across groups, you need scalar invariance.
4. **MODEL `<groupname>:` *overrides*, doesn't add.** If base MODEL says `f BY y1-y3;` and `MODEL g2: f BY y3;`, then in g2 only y3's loading differs from the base; the others remain equal. To free everything in g2, list everything.
5. **Latent interaction is slow.** XWITH with many indicators per factor + INTEGRATION can take hours. If speed is an issue, use the unconstrained product-indicator approach (Marsh et al. 2004) or matched-pair indicators.
6. **Bifactor identification.** Forgetting to constrain factor correlations to 0 (`g WITH s1@0;`) defeats the bifactor logic. Or use bifactor rotation in ESEM.
7. **PARAMETERIZATION = THETA** is needed in some multi-group categorical CFA cases where DELTA produces unstable estimates; if "non-positive definite" error appears with WLSMV invariance, try THETA.
8. **Categorical CFA fit indices.** WRMR is sometimes reported as 0 or missing — Mplus computes it under restrictive assumptions. Rely on RMSEA, CFI, TLI; chi-square is mean-adjusted (DIFFTEST is for nested model comparison).
9. **DIFFTEST for nested WLSMV models.** To compare nested categorical models, save the derivatives from the larger model and reference them in the smaller: `SAVEDATA: DIFFTEST = deriv.dat;` then in the constrained model `ANALYSIS: DIFFTEST = deriv.dat;`. Mplus reports the correct adjusted Δχ².

## Canonical examples in `assets/examples/`

- `ex5.1_cfa_basic.inp` — minimal two-factor CFA with continuous indicators
- `ex5.2_cfa_categorical.inp` — CFA with categorical indicators (WLSMV)
- `ex5.11_sem.inp` — SEM with latent-on-latent regressions
- `ex5.13_latent_interaction.inp` — XWITH latent interaction
- `ex5.14_mgcfa_mimic.inp` — multiple-group MIMIC pattern
