# Multilevel modeling (User's Guide Ch. 9)

Mplus handles two-level, three-level, and cross-classified data via `TYPE = TWOLEVEL`, `TYPE = THREELEVEL`, and `TYPE = CROSSCLASSIFIED`. The MODEL block is split into `%WITHIN%` and `%BETWEEN%` (or `%BETWEEN level2%` / `%BETWEEN level3%`). This reference covers regression, CFA, SEM, growth, mediation, and random-slope variants. For multilevel mixture, see `references/multilevel-mixture.md`.

## Decision tree

```
User wants to model data that is...
├─ Nested (students in schools, repeated measures in people, etc.)
│   ├─ Just adjust SEs for clustering (not modeling between-level structure)
│   │   → TYPE = COMPLEX (single-level inference, robust SEs)
│   └─ Decompose variance / model both levels
│       → TYPE = TWOLEVEL (or THREELEVEL, CROSSCLASSIFIED)
├─ Random-intercept-only regression
│   → TYPE = TWOLEVEL; %WITHIN% y ON x; %BETWEEN% y ON w;
├─ Random slopes
│   → TYPE = TWOLEVEL RANDOM; %WITHIN% s | y ON x; %BETWEEN% s ON w;
├─ Two-level CFA / SEM
│   → factor structure in %WITHIN% and/or %BETWEEN%
├─ Multilevel growth (people repeated within clusters)
│   → growth in either %WITHIN% (time within person) or two-level (people in groups)
├─ Three levels (students in classes in schools)
│   → TYPE = THREELEVEL [RANDOM]; CLUSTER = school class;
├─ Cross-classified (e.g., students in both schools AND neighborhoods)
│   → TYPE = CROSSCLASSIFIED; CLUSTER = school neighborhood;
└─ Multilevel mediation
    → see end of this reference; latent centering is the modern best practice
```

## Skeletons

### Two-level random-intercept regression

```
TITLE:    two-level random-intercept regression
DATA:     FILE = data.dat;
VARIABLE: NAMES = y x w xm clus;
          WITHIN = x;                ! L1 covariate
          BETWEEN = w xm;            ! L2 covariates
          CLUSTER = clus;
DEFINE:   CENTER x (GRANDMEAN);      ! center L1 covariate (or GROUPMEAN)
ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%
          y ON x;
          %BETWEEN%
          y ON w xm;
OUTPUT:   STDYX TECH1;
```

This is `ex9.1a`. `y` is not in WITHIN or BETWEEN — Mplus automatically decomposes its variance into within and between parts. The L1 intercept (= cluster-mean of y) becomes the dependent variable in `%BETWEEN%`.

### Two-level random-slope regression

```
VARIABLE: WITHIN = x;
          BETWEEN = w;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL RANDOM;
MODEL:    %WITHIN%
          s | y ON x;                ! random slope of y on x
          %BETWEEN%
          y s ON w;                  ! L2 predictor of intercept and slope
          y WITH s;                  ! intercept-slope covariance
```

`TYPE = TWOLEVEL RANDOM` is required for random slopes. The `|` operator creates `s` as a latent random slope. In `%BETWEEN%`, `s` is now a variable you can regress on L2 predictors or covary with `y`.

### Two-level CFA

Factor structure on both levels (item variance decomposed):

```
VARIABLE: NAMES = y1-y6 clus;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%
          fw BY y1-y3;
          fw2 BY y4-y6;
          %BETWEEN%
          fb BY y1-y3;
          fb2 BY y4-y6;
OUTPUT:   STDYX;
```

Same items, different factor structures at each level. To enforce identical factor structure at both levels (typical for measurement invariance across levels), use the same loadings (or label them):

```
MODEL:    %WITHIN%
          fw BY y1
                y2-y3 (lam2-lam3);
          %BETWEEN%
          fb BY y1
                y2-y3 (lam2-lam3);
          y1-y3@0;                    ! kill L2 residuals if you assume only the factor varies at L2
```

`y1-y3@0;` in `%BETWEEN%` says the L2 residuals are zero — i.e., the only L2 variation in items comes through `fb`.

### Two-level SEM (latent regression at one or both levels)

```
ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%
          fw1 BY y1-y3;
          fw2 BY y4-y6;
          fw2 ON fw1;
          %BETWEEN%
          fb1 BY y1-y3;
          fb2 BY y4-y6;
          fb2 ON fb1;
```

### Multilevel growth (people in clusters)

When repeated measurements are within people and people are within clusters, treat time as L1, person as L2 (longitudinal) — or treat person as L1, cluster as L2 (cross-sectional with growth at L1):

```
! pattern: T waves per person, people clustered in groups
VARIABLE: NAMES = y1-y4 x w clus;
          WITHIN = x;
          BETWEEN = w;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%
          iw sw | y1@0 y2@1 y3@2 y4@3;
          y1-y4 (1);                  ! equal residual variances (often imposed)
          iw sw ON x;
          %BETWEEN%
          ib sb | y1@0 y2@1 y3@2 y4@3;
          y1-y4@0;                    ! only intercept and slope vary at L2 (no item-level residual)
          ib sb ON w;
```

### Three-level model (e.g., students in classes in schools)

```
VARIABLE: CLUSTER = school class;          ! L3 first, L2 second
          WITHIN = x;
          BETWEEN = (class) w_class (school) w_school;
ANALYSIS: TYPE = THREELEVEL RANDOM;
MODEL:    %WITHIN%
          s | y ON x;
          %BETWEEN class%
          s ON w_class;
          y ON w_class;
          %BETWEEN school%
          s ON w_school;
          y ON w_school;
```

### Cross-classified (each unit nested in two non-hierarchical L2 factors)

```
VARIABLE: CLUSTER = school neighborhood;
ANALYSIS: TYPE = CROSSCLASSIFIED;
MODEL:    %WITHIN%
          y ON x;
          %BETWEEN school%
          y ON w_school;
          %BETWEEN neighborhood%
          y ON w_nbhd;
```

## Multilevel mediation

The right approach depends on which level each variable sits at. Notation: `X→L`, `M→L`, `Y→L` where L = 1 (level-1) or 2 (level-2).

| Pattern | Where path lives | Approach |
|---|---|---|
| 2-2-1 (L2 predictor, L2 mediator, L1 outcome) | both paths at %BETWEEN% | Standard MODEL CONSTRAINT NEW(ab) |
| 2-1-1 (L2 predictor, L1 mediator, L1 outcome) | a-path at %BETWEEN% on cluster-mean of M; b-path within or between | Use latent centering (built into TYPE=TWOLEVEL) |
| 1-1-1 (all level-1) | both paths within; can also have between paths if M, Y vary at L2 | Latent centering essential — see ex9.27 or McNeish-style template |

### 1-1-1 mediation with latent centering

```
TITLE:    multilevel mediation, 1-1-1, latent centering
DATA:     FILE = data.dat;
VARIABLE: NAMES = y m x clus;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL RANDOM;
MODEL:    %WITHIN%
          y ON m (b_w);
          m ON x (a_w);
          %BETWEEN%
          y ON m (b_b);
          m ON x (a_b);
MODEL CONSTRAINT:
  NEW(ab_w ab_b);
  ab_w = a_w * b_w;
  ab_b = a_b * b_b;
OUTPUT:   STDYX CINTERVAL;
```

Note: `x`, `m`, `y` are listed in **neither** WITHIN nor BETWEEN — Mplus decomposes their variance into within and between components. This is "latent centering" (Asparouhov & Muthén 2019) — superior to manual group-mean centering because the cluster means are estimated, not point-computed.

For Bayesian inference (often better for multilevel mediation with small numbers of clusters):
```
ANALYSIS: TYPE = TWOLEVEL RANDOM;
          ESTIMATOR = BAYES;
          PROCESSORS = 4;
          FBITERATIONS = 20000;
```

## ANALYSIS settings

```
ANALYSIS: TYPE = TWOLEVEL;             ! random-intercept only
          TYPE = TWOLEVEL RANDOM;       ! adds random slopes via |
          TYPE = THREELEVEL [RANDOM];
          TYPE = CROSSCLASSIFIED [RANDOM];
          ESTIMATOR = MLR;              ! robust SE for non-normal data
          ESTIMATOR = BAYES;            ! for complex multilevel or small cluster N
          ALGORITHM = INTEGRATION;      ! required for categorical outcomes + RANDOM slopes
          INTEGRATION = MONTECARLO(500);
```

## OUTPUT to interpret

```
OUTPUT:   STDYX TECH1 TECH8 SAMPSTAT;
```

- `STDYX` — standardized estimates per level
- `SAMPSTAT` includes ICCs (intraclass correlations), within and between SD, etc.
- For random slopes: TECH4 shows latent slope mean & variance
- `RESIDUAL` — diagnostic at L1 only

## ICC and design effect

The output reports ICC for each L1 variable: ICC = variance L2 / (variance L1 + variance L2). Rule of thumb:
- ICC > 0.05 → multilevel modeling advised
- ICC ~ 0 → could safely ignore clustering (but use TYPE=COMPLEX for SE adjustment)

## Centering choices

```
DEFINE:   CENTER x (GRANDMEAN);          ! subtract grand mean (whole-sample mean)
DEFINE:   CENTER x (GROUPMEAN);          ! subtract cluster mean (= group-mean centering)
DEFINE:   CENTER x (CLUSTERMEAN);         ! synonym for GROUPMEAN
```

For multilevel models, the choice has consequences:
- **GRANDMEAN**: conflates within- and between-cluster effects (less interpretable).
- **GROUPMEAN**: cleanly separates within (group-mean-centered x) and between (cluster mean of x) effects. Add the cluster mean as a L2 predictor.
- **Latent centering** (no DEFINE; just list x in neither WITHIN nor BETWEEN): Mplus estimates the cluster mean and uses it; statistically preferred per Lüdtke et al. 2008.

For mediation in particular, use latent centering (do not declare WITHIN/BETWEEN for M, X, Y) — see 1-1-1 mediation template above.

## Pitfalls

1. **Wrong CLUSTER variable.** ICCs come out as 0 if CLUSTER points to something with one obs per value (e.g., subject id when you meant school id).
2. **WITHIN / BETWEEN allocation errors.** A variable that varies at both levels (e.g., student SES varies within school and schools have different mean SES) goes in **neither** — Mplus decomposes it. Putting it in WITHIN treats schools as identical on SES; putting it in BETWEEN treats students within a school as identical.
3. **Random slope on a BETWEEN variable.** A slope `s | y ON w;` where `w` is BETWEEN-only doesn't make sense; the slope can't vary within cluster if x doesn't vary within. Mplus will error or estimate a near-zero variance.
4. **L2 sample size matters more than L1.** With < 30 clusters, Bayesian estimation is more reliable than ML. With < 10 clusters, multilevel modeling may not be appropriate at all.
5. **`y1-y4@0` in BETWEEN.** This kills L2 residuals — fine if you're modeling all L2 variance through factors / growth factors. If you skip this and the L2 residuals are estimated, item-level variation at L2 competes with the factor variance → identification issues.
6. **`TYPE = COMPLEX` vs `TYPE = TWOLEVEL`.** COMPLEX gives a single set of parameter estimates with cluster-robust SEs (doesn't model between-cluster structure). TWOLEVEL gives separate within and between parameters. Use COMPLEX when between structure isn't of interest; TWOLEVEL when it is.
7. **Random slope variance near 0.** If the random slope variance is estimated near 0, the slope is essentially fixed across clusters. Constraining `s@0;` reduces a "TWOLEVEL RANDOM" to "TWOLEVEL" for that slope.
8. **Cross-level interaction.** A common pattern: `s | y ON x;` in %WITHIN%, then `s ON w;` in %BETWEEN%. This regresses the random slope on a level-2 variable → a cross-level interaction effect of `w * x` on `y`.
9. **Categorical outcomes in TWOLEVEL RANDOM.** Requires ALGORITHM = INTEGRATION, which is slow. Consider Bayesian estimation as a faster alternative.

## Canonical examples in `assets/examples/`

- `ex9.1a_twolevel_regression.inp` — two-level random-intercept regression
- `ex9.6_twolevel_cfa.inp` — two-level CFA with within and between factors
