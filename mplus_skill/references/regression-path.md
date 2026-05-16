# Regression and path analysis (User's Guide Ch. 3)

Covers the family of models where all variables are observed: linear, logistic, probit, Poisson, censored regression; path analysis (multiple equations with directional arrows among observed variables); bootstrap inference for indirect effects.

## Decision tree

```
User wants...
├─ A single outcome regressed on covariates
│   ├─ Continuous outcome → linear regression (default)
│   ├─ Binary / ordinal outcome → CATEGORICAL =, ESTIMATOR=WLSMV or ML with LINK=LOGIT
│   ├─ Count outcome → COUNT =, ML
│   ├─ Zero-inflated count → COUNT = u (i), ML
│   ├─ Censored outcome (top-/bottom-coded) → CENSORED = y (a)/(b), ML
│   └─ Nominal outcome (>2 unordered) → NOMINAL =, ML (multinomial logit)
│
├─ Several outcomes with a clear DAG (path analysis)
│   ├─ All observed, fully recursive → just write multiple ON statements
│   ├─ Need indirect effects → MODEL INDIRECT (observed) or MODEL CONSTRAINT
│   ├─ Need bootstrap CIs → ANALYSIS: BOOTSTRAP = N; OUTPUT: CINTERVAL(BOOTSTRAP);
│   └─ Non-recursive (feedback loop) → reciprocal regressions with extra constraints
│
└─ One outcome but two slopes (one per group)
    └─ Multiple-group regression → use GROUPING and MODEL <groupname>: overrides
```

## Skeletons

### Linear regression
```
TITLE:    linear regression
DATA:     FILE = data.dat;
VARIABLE: NAMES = y x1-x3;
MODEL:    y ON x1-x3;
OUTPUT:   STDYX;
```

### Logistic regression (binary outcome)
```
TITLE:    logistic regression
DATA:     FILE = data.dat;
VARIABLE: NAMES = u x1-x3;
          CATEGORICAL = u;
ANALYSIS: ESTIMATOR = ML;          ! WLSMV is default; ML gives logit/probit coefficients
          LINK = LOGIT;            ! or PROBIT
MODEL:    u ON x1-x3;
OUTPUT:   STDYX;
```

### Probit / multiple-category ordered probit
Default for `CATEGORICAL` with WLSMV is probit-link with delta parameterization. To request explicitly:
```
ANALYSIS: ESTIMATOR = WLSMV;
          PARAMETERIZATION = DELTA;   ! default; THETA scales residual variances to 1
```

### Poisson count regression
```
VARIABLE: NAMES = u x1 x2;
          COUNT = u;
ANALYSIS: ESTIMATOR = ML;
MODEL:    u ON x1 x2;
```

### Zero-inflated Poisson
```
VARIABLE: COUNT = u (i);            ! (i) requests zero-inflation
MODEL:    u ON x1 x2;               ! Poisson part
          u#1 ON x1;                ! inflation logit (u#1 is the inflation latent)
```

### Censored regression (Tobit-like)
```
VARIABLE: CENSORED = y (a);         ! top-coded; use (b) for bottom-coded
                                    ! (bi) / (ai) for inflated versions
MODEL:    y ON x1-x3;
```

### Multinomial logit (nominal outcome)
```
VARIABLE: NOMINAL = u;              ! values like 1, 2, 3
MODEL:    u#1 ON x1 x2;             ! contrast: category 1 vs last
          u#2 ON x1 x2;             ! category 2 vs last
```
The reference category is the **last** value of `u`. To change, recode.

### Path analysis with observed mediator
```
TITLE:    simple mediation: x → m → y
DATA:     FILE = data.dat;
VARIABLE: NAMES = y m x covariate;
MODEL:    y ON m x covariate;
          m ON x covariate;
MODEL INDIRECT:
          y IND m x;                ! indirect of x on y via m
OUTPUT:   STDYX CINTERVAL;
```

### Path analysis with bootstrap inference (preferred for indirect effects)
```
TITLE:    path analysis with bootstrap CIs
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1 y2 y3 x1 x2 x3;
ANALYSIS: BOOTSTRAP = 1000;
MODEL:    y1 y2 ON x1 x2 x3;
          y3 ON y1 y2 x2;
MODEL INDIRECT:
          y3 IND y1 x1;
          y3 IND y2 x1;
OUTPUT:   CINTERVAL (BOOTSTRAP);    ! BCBOOTSTRAP for bias-corrected
```

This is `ex3.16` from the User's Guide — the canonical pattern for bootstrap-CI mediation when all variables are observed.

### Multi-group regression (different slope per group)
```
VARIABLE: NAMES = y x1 x2 g;
          GROUPING = g (1=group1 2=group2);
MODEL:    y ON x1 x2;
MODEL group2:
          y ON x1;                  ! group2 has a different x1 slope; x2 slope still equal
```

By default, every parameter in MODEL is free per group. Overriding for one group changes only what you state. To force equality, label parameters: `y ON x1 (b1);` in the base MODEL.

### Path analysis with categorical mediator
WLSMV by default; for ML/probit:
```
VARIABLE: NAMES = y m x;
          CATEGORICAL = m;
ANALYSIS: ESTIMATOR = ML;
          LINK = PROBIT;
MODEL:    y ON m x;
          m ON x;
OUTPUT:   STDYX;
```

## Standardized estimates

- `STDYX` is what to ask for in continuous outcomes — both predictor and outcome standardized.
- `STDY` standardizes only the outcome — appropriate when the predictor is binary (Cohen's d-like interpretation).
- With CATEGORICAL outcomes, Mplus computes standardized estimates relative to the underlying continuous latent response, not the observed binary metric. Interpret carefully.

## MODEL INDIRECT — exact syntax

```
MODEL INDIRECT:
  y IND m x;              ! total indirect of x on y via m (one mediator)
  y IND m1 m2 x;          ! serial indirect: x → m2 → m1 → y
  y VIA m x;              ! all paths from x to y that pass through m (parallel + serial)
```

`IND` requires the path to be unambiguous (one path per IND statement). For complex mediation, write each path separately, then combine with MODEL CONSTRAINT:

```
MODEL:    y ON m1 m2 x;
          m1 ON x (a1);
          m2 ON x (a2);
          y ON m1 (b1) m2 (b2);
MODEL CONSTRAINT:
  NEW(ind1 ind2 total);
  ind1 = a1 * b1;
  ind2 = a2 * b2;
  total = ind1 + ind2;
```

`NEW(...)` declares free parameters with starting values; Mplus reports CIs on each.

## Bootstrap CI options

```
ANALYSIS: BOOTSTRAP = 1000;          ! 1000 resamples
OUTPUT:   CINTERVAL (BOOTSTRAP);     ! percentile CI (default)
          CINTERVAL (BCBOOTSTRAP);   ! bias-corrected and accelerated
          CINTERVAL (SYMMETRIC);     ! Wald-style symmetric (not really bootstrap)
```

Notes:
- BOOTSTRAP cannot combine with ESTIMATOR = MLR or BAYES. Use BAYES with credibility intervals as an alternative.
- Bootstrap requires complete data (or non-FIML missing handling). With FIML, listwise drops happen.
- 5000 resamples is generally adequate; 1000 is the User's Guide default. More resamples ≠ more accurate after a point.

## Common variants

**Centering before regression** (in DEFINE):
```
DEFINE:   CENTER x1 x2 (GRANDMEAN);
```

**Interaction of observed variables** — compute manually:
```
DEFINE:   xz = x * z;               ! create the product
MODEL:    y ON x z xz;
```

For latent interactions, see `references/cfa-sem.md` (XWITH operator).

**Simple slopes** — compute via MODEL CONSTRAINT:
```
MODEL:    y ON x (b1) z (b2) xz (b3);
MODEL CONSTRAINT:
  NEW(slope_lo slope_hi);
  slope_lo = b1 + b3 * (-1);        ! slope at z = -1 (1 SD below)
  slope_hi = b1 + b3 * (+1);        ! slope at z = +1
```

## Pitfalls

1. **Forgetting CATEGORICAL declaration.** If `u` is binary 0/1 and you don't declare it, Mplus treats it as continuous → linear probability model → standard errors wrong, fit indices meaningless.
2. **`MODEL INDIRECT` won't work with mixture or multilevel.** Compute the indirect in MODEL CONSTRAINT.
3. **`y ON x1 x2;` vs. `y1 y2 ON x1;`.** First: one regression with two predictors. Second: two regressions, each on x1. Mplus expands LHS × RHS — be deliberate.
4. **Default correlations.** All observed exogenous variables are correlated by default; all endogenous residuals are not. To free a residual covariance: `e1 WITH e2;`. To kill a default exogenous correlation: `x1 WITH x2@0;`.
5. **Bootstrap + STDYX.** STDYX bootstrap CIs are based on bootstrapping the unstandardized estimates and then standardizing each replicate — fine for inference, but reported point estimates may differ slightly from non-bootstrap STDYX.
6. **Multiple group + GROUPING with character labels.** `GROUPING = g (1=male 2=female);` — `male` and `female` are display labels for `MODEL male:` / `MODEL female:`. They are *not* values in your data; the values must be numeric (1, 2).

## Canonical examples in `assets/examples/`

- `ex3.1_regression.inp` — simplest linear regression
- `ex3.11_path.inp` — path analysis, multiple equations
- `ex3.16_path_bootstrap.inp` — path analysis with bootstrap indirect effects
