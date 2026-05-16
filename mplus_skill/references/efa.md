# Exploratory factor analysis (User's Guide Ch. 4)

EFA in Mplus is invoked through `TYPE = EFA m n;` in the ANALYSIS block, which fits all factor counts from m to n in one run and reports fit for each. Mplus supports continuous, categorical, and multilevel EFA, plus ESEM (exploratory SEM with rotation embedded inside CFA).

## Decision tree

```
User wants to...
├─ Explore factor structure, no a priori model
│   ├─ Continuous items → TYPE = EFA m n; default ESTIMATOR = ML
│   ├─ Categorical items → TYPE = EFA m n; CATEGORICAL = u1-uK; ESTIMATOR = WLSMV
│   ├─ Mixed item types → use ESEM (CFA with target rotation) — see special-features.md
│   └─ Want bifactor structure → ROTATION = BI-GEOMIN or BI-CF-QUARTIMAX
│
├─ Already has a hypothesis
│   └─ Go to references/cfa-sem.md instead
│
├─ EFA at two levels (within & between clusters)
│   └─ TYPE = TWOLEVEL EFA mW nW UW mB nB UB; CLUSTER=clus
│
└─ ESEM (CFA framework with rotation, retains fit indices etc.)
    └─ See references/special-features.md (ESEM section)
```

## Skeletons

### Standard EFA, continuous indicators
```
TITLE:    EFA exploring 1 to 4 factors
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y10;
ANALYSIS: TYPE = EFA 1 4;             ! fit 1-, 2-, 3-, 4-factor solutions
          ROTATION = GEOMIN(OBLIQUE);  ! default; alternatives below
OUTPUT:   SAMPSTAT;
```

### EFA with categorical indicators
```
VARIABLE: NAMES = u1-u10;
          CATEGORICAL = u1-u10;
ANALYSIS: TYPE = EFA 1 4;
          ESTIMATOR = WLSMV;           ! default with CATEGORICAL
          ROTATION = GEOMIN(OBLIQUE);
```

### Bifactor EFA
```
ANALYSIS: TYPE = EFA 1 4;
          ROTATION = BI-GEOMIN(ORTHOGONAL);  ! a general factor + orthogonal group factors
```
Other bifactor rotations: `BI-CF-QUARTIMAX`, `BI-CF-EQUAMAX`.

### Multilevel EFA (within + between)
```
VARIABLE: NAMES = y1-y10 clus;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL EFA 1 4 UW 1 2 UB;
          ! 1-4 within factors with UW=1 to 2 unrestricted at within;
          ! syntax varies per User's Guide — see ex4.4-ex4.6 for exact form
```

### Mixture EFA
```
VARIABLE: CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE EFA 1 3;
          STARTS = 200 20;
```

## Rotation choices

| Rotation | Family | Use when |
|---|---|---|
| `GEOMIN(OBLIQUE)` | default oblique | general purpose; allows correlated factors |
| `GEOMIN(ORTHOGONAL)` | default orthogonal | factors theoretically uncorrelated |
| `PROMAX` | oblique | classic; produces simple-structure quickly |
| `VARIMAX` | orthogonal | classic; uncorrelated factors |
| `OBLIMIN` | oblique | general oblique alternative |
| `CF-QUARTIMAX(OBLIQUE)` | Crawford-Ferguson family | flexible |
| `CF-EQUAMAX(OBLIQUE)` | CF | balances complexity across rows/cols |
| `TARGET` | confirmatory rotation toward a target matrix | ESEM with hypothesized loading pattern (see special-features.md) |
| `BI-GEOMIN(ORTHOGONAL)` | bifactor | one general + several specific factors |

Syntax: `ROTATION = GEOMIN(OBLIQUE);` — the rotation type, then optionally `(OBLIQUE)` or `(ORTHOGONAL)` and an epsilon value: `GEOMIN(OBLIQUE, 0.5);`.

## What output to interpret

For each factor solution m, Mplus reports:
- **Chi-square test of model fit** — significant means "fits worse than saturated", not "this many factors is wrong"
- **RMSEA, CFI, TLI** — incremental fit indices; SRMR for continuous, WRMR for categorical
- **Eigenvalues** for the sample correlation/covariance matrix
- **Geomin (or chosen) rotated loading matrix** with significance asterisks
- **Factor correlation matrix** (oblique rotations only)

Common selection criteria:
- Theory + interpretability above all
- Loading pattern: each item should load strongly on one factor (>.4), weakly on others (<.3) — Thurstone simple structure
- Scree plot inflection (`OUTPUT: PLOT3;` shows eigenvalues; PLOT3 also gives loading plots)
- Parallel analysis (run separately, not built into Mplus EFA — use R `psych::fa.parallel`)
- Add factors only if they're substantively meaningful (not solo loading factors)

## Complete annotated example

```
TITLE:    EFA of well-being items, 10 items, 1-4 factors
          comparing geomin and bifactor rotations

DATA:     FILE = wellbeing.dat;

VARIABLE: NAMES = id y1-y10 age gender;
          USEVARIABLES = y1-y10;
          MISSING = ALL (-99);

ANALYSIS: TYPE = EFA 1 4;
          ESTIMATOR = MLR;             ! robust SE
          ROTATION = GEOMIN(OBLIQUE);

OUTPUT:   SAMPSTAT MODINDICES(10);

PLOT:     TYPE = PLOT3;                ! loading plots, eigenvalues
```

To compare rotations, run twice (once per ROTATION line) and compare loadings.

## ESEM versus EFA

EFA returns a rotated loading matrix and fit indices but lacks the SEM framework — no covariates, no measurement invariance testing, no extension to latent regression. ESEM ("EFA within CFA") uses the same rotation machinery but inside a regular MODEL block, so you can:
- Add covariates predicting factors
- Constrain loadings across groups for invariance
- Combine with regular CFA factors in the same model

ESEM syntax uses `BY` with block-rotation flags:
```
MODEL:    f1 f2 f3 BY y1-y10 (*1);     ! '*1' = rotation block 1; loadings rotated jointly
          f1 BY y1@1;                  ! optional anchor
```

See `references/special-features.md` for the full ESEM treatment.

## Common variants

**Schmid-Leiman second-order to bifactor transformation** — fit a 2nd-order CFA in cfa-sem.md, then orthogonalize.

**Force a fixed number of factors** — use `TYPE = EFA k k;` (m and n both equal to k).

**EFA on subset of items, holding others as covariates** — Mplus EFA doesn't natively support; use ESEM instead.

**Robust estimation for non-normal continuous data** — `ESTIMATOR = MLR;` (default within `TYPE = EFA` is ML; specify MLR for robust SEs and chi-square adjustment).

## Pitfalls

1. **TYPE = EFA m n means inclusive**: `TYPE = EFA 1 4;` fits 4 separate solutions. Output is long; pick one based on theory and fit.
2. **EFA does not accept covariates**. To predict factor scores from covariates exploratorily, use ESEM.
3. **Geomin oblique with small epsilon (default 0.0001 for >3 factors) can be unstable**; if loadings look bizarre, try `GEOMIN(OBLIQUE, 0.5);`.
4. **Categorical EFA with WLSMV** uses polychoric correlations and tetrachorics. Categorical items must have at least 5 endorsed responses per category (else combine categories).
5. **Bifactor EFA without a strong general factor** can produce a degenerate general factor (some loadings near 0, others very high) — interpret cautiously; a CFA bifactor with explicit anchors is often preferable.
6. **Item residuals in EFA are not freely correlated** — that's a CFA freedom. If you suspect a method factor or correlated residuals, move to CFA / ESEM.

## Canonical examples in `assets/examples/`

- `ex4.1_efa_continuous.inp` — EFA 1-4 factors, continuous items, GEOMIN
- `ex4.7_efa_bifactor.inp` — bifactor EFA with BI-GEOMIN rotation
