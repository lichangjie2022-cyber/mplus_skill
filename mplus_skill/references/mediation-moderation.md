# Mediation, moderation, and conditional indirect effects

The classic "a × b" indirect effect appears across nearly every model family in Mplus. This reference unifies the syntax patterns for: simple mediation, parallel/serial mediators, moderated mediation (conditional indirect effects), latent-variable mediation, multilevel mediation, and Bayesian mediation. For multilevel mediation with latent centering see also `references/multilevel.md`.

## Decision tree

```
User has...
├─ All observed, simple x → m → y → MODEL INDIRECT (with BOOTSTRAP) [see regression-path.md]
├─ Multiple mediators (parallel m1, m2) → MODEL CONSTRAINT with NEW(...)
├─ Serial mediators (x → m1 → m2 → y) → MODEL INDIRECT VIA or NEW(...)
├─ Latent mediator → CFA-style MODEL, then MODEL INDIRECT for latent IND
├─ Moderation only (x × z → y) → DEFINE: xz = x * z; or XWITH for latent moderator
├─ Moderated mediation (a- or b-path moderated) → MODEL CONSTRAINT with NEW(...) at z values
├─ Multilevel mediation (1-1-1, 2-1-1, etc.) → see references/multilevel.md
└─ Bayesian indirect effects with credibility intervals → ESTIMATOR=BAYES + MODEL CONSTRAINT NEW(...)
```

## Skeletons

### Simple mediation (observed), bootstrap CI

```
TITLE:    simple mediation, bootstrap CI
DATA:     FILE = data.dat;
VARIABLE: NAMES = y m x c1 c2;
ANALYSIS: BOOTSTRAP = 5000;
MODEL:    y ON m (b) x c1 c2;
          m ON x (a) c1 c2;
MODEL INDIRECT:
          y IND m x;
OUTPUT:   CINTERVAL(BCBOOTSTRAP) STDYX;
```

- `BOOTSTRAP = 5000;` — at least 1000; 5000 is generous.
- `CINTERVAL(BCBOOTSTRAP)` — bias-corrected and accelerated bootstrap CIs (preferred for indirect effects).
- `MODEL INDIRECT: y IND m x;` — Mplus reports total, direct (x → y), and indirect (x → m → y) effects.

### Parallel multiple mediators

```
MODEL:    y ON m1 (b1) m2 (b2) x;
          m1 ON x (a1);
          m2 ON x (a2);
MODEL INDIRECT:
          y IND m1 x;          ! through m1
          y IND m2 x;          ! through m2
```

Or compute the specific indirects manually:

```
MODEL CONSTRAINT:
  NEW(ind1 ind2 total);
  ind1 = a1 * b1;
  ind2 = a2 * b2;
  total = ind1 + ind2;
```

### Serial mediation (x → m1 → m2 → y)

```
MODEL:    y ON m2 (b2) m1 (b1d) x;
          m2 ON m1 (d) x (a2d);
          m1 ON x (a1);
MODEL INDIRECT:
          y IND m2 m1 x;       ! serial path: x → m1 → m2 → y
```

Or with explicit constraints:
```
MODEL CONSTRAINT:
  NEW(serial);
  serial = a1 * d * b2;
```

### Mediation with a latent mediator

```
MODEL:    fm BY m1-m4;          ! latent mediator
          fy BY y1-y4;          ! latent outcome
          fm ON x (a);
          fy ON fm (b) x;
MODEL INDIRECT:
          fy IND fm x;
OUTPUT:   STDYX CINTERVAL;
```

If x is observed and bootstrap is desired, set `ANALYSIS: BOOTSTRAP = 5000;`. With latent variables, MODEL INDIRECT supports the IND syntax.

### Observed × observed moderation

```
DEFINE:   xz = x * z;
MODEL:    y ON x z xz;
OUTPUT:   STDYX;
```

Simple slopes at low/high z:
```
MODEL:    y ON x (b1) z (b2) xz (b3);
MODEL CONSTRAINT:
  NEW(slope_lo slope_hi diff);
  slope_lo = b1 + b3 * (-1);   ! 1 SD below z's mean (assumes z standardized)
  slope_hi = b1 + b3 * (+1);
  diff = slope_hi - slope_lo;  ! difference in slopes
```

### Latent × observed moderation

```
ANALYSIS: TYPE = RANDOM;
          ALGORITHM = INTEGRATION;
MODEL:    f1 BY y1-y3;
          xz | f1 XWITH z;     ! latent f1 × observed z
          out ON f1 z xz;
```

### Latent × latent moderation

```
ANALYSIS: TYPE = RANDOM;
          ALGORITHM = INTEGRATION;
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
          f3 BY y7-y9;
          f1xf2 | f1 XWITH f2;
          f3 ON f1 f2 f1xf2;
```

### Moderated mediation (conditional indirect effects)

Pattern: x → m → y with the a-path moderated by w (i.e., the strength of x → m depends on w).

```
DEFINE:   xw = x * w;          ! moderator-by-predictor interaction
MODEL:    y ON m (b) x;
          m ON x (a1) w (a2) xw (a3);
MODEL CONSTRAINT:
  NEW(ab_lo ab_hi diff);
  ab_lo = (a1 + a3 * (-1)) * b;   ! indirect at w = -1
  ab_hi = (a1 + a3 * (+1)) * b;   ! indirect at w = +1
  diff = ab_hi - ab_lo;           ! "index of moderated mediation" (Hayes)
```

This is the standard Edwards & Lambert / Hayes index of moderated mediation. With `BOOTSTRAP = 5000;`, Mplus reports bootstrap CIs on each `NEW` parameter.

### B-path moderated mediation

```
DEFINE:   mw = m * w;
MODEL:    y ON m (b1) w (b2) mw (b3) x;
          m ON x (a);
MODEL CONSTRAINT:
  NEW(ab_lo ab_hi);
  ab_lo = a * (b1 + b3 * (-1));
  ab_hi = a * (b1 + b3 * (+1));
```

### Multiple groups: do mediation paths differ?

```
VARIABLE: GROUPING = g (1=men 2=women);
MODEL:    y ON m (b_m) x;
          m ON x (a_m);
MODEL women:
          y ON m (b_w);
          m ON x (a_w);
MODEL CONSTRAINT:
  NEW(ab_m ab_w diff);
  ab_m = a_m * b_m;
  ab_w = a_w * b_w;
  diff = ab_m - ab_w;
```

Bootstrap CI on `diff` tests whether the indirect effect differs across groups.

### Bayesian mediation (alternative to bootstrap)

```
ANALYSIS: ESTIMATOR = BAYES;
          PROCESSORS = 4;
          FBITERATIONS = 20000;
MODEL:    y ON m (b) x;
          m ON x (a);
MODEL CONSTRAINT:
  NEW(ab);
  ab = a * b;
OUTPUT:   STDYX CINTERVAL(HPD);   ! highest posterior density credibility interval
```

Bayesian CIs handle the non-normal sampling distribution of `a × b` naturally (the posterior of the product captures asymmetry directly). For small samples or unequal coefficient magnitudes, Bayes is often a better choice than bootstrap.

## When MODEL INDIRECT works and when it doesn't

`MODEL INDIRECT` is convenient but limited:

| Works | Doesn't work / use NEW instead |
|---|---|
| Single-group SEM | Mixture models |
| Observed or latent mediators | Multilevel models |
| Linear paths | Conditional indirects (moderated mediation) |
| ML or WLSMV estimator | Bayesian — must use MODEL CONSTRAINT NEW |
| BOOTSTRAP available | Multiple imputation — must use NEW |

When in doubt, write the indirect manually with `MODEL CONSTRAINT NEW(...)`.

## Pitfalls

1. **Sobel test is wrong.** The product `a × b` is not normally distributed. Use bootstrap (`BCBOOTSTRAP`) or Bayesian credibility intervals. Mplus's "indirect" output reports the Sobel SE by default — ignore in favor of the bootstrap CI.
2. **STDYX with bootstrap.** Bootstrap CIs are computed on unstandardized estimates and then standardized per replicate. STDYX point estimates differ slightly from non-bootstrap STDYX.
3. **Categorical mediator + bootstrap.** WLSMV doesn't support BOOTSTRAP. Either use ESTIMATOR=ML (with LINK=LOGIT/PROBIT) and BOOTSTRAP, or use ESTIMATOR=BAYES.
4. **Interaction with centered vs. uncentered variables.** When using `DEFINE: xz = x * z;`, x and z should usually be centered (mean 0) for interpretable main effects. Add `DEFINE: CENTER x z (GRANDMEAN);` before computing xz.
5. **Latent interaction with too many indicators.** XWITH with INTEGRATION explodes computationally. Beyond ~5 indicators per factor, run time is hours.
6. **Multiple mediators with shared variance.** If m1 and m2 are highly correlated, `y ON m1 m2 x;` produces unstable b1, b2. Consider whether they're truly distinct mediators or one latent construct.
7. **Multilevel mediation requires latent centering** to avoid conflating within- and between-cluster effects. See `references/multilevel.md`.
8. **For Bayesian mediation, monitor convergence.** With PSRF (TECH8), values close to 1.00 are good; if some priors are diffuse and posteriors have heavy tails, increase FBITERATIONS to 50000+.

## Canonical examples in `assets/examples/`

- `ex3.16_path_bootstrap.inp` — bootstrap CI for indirect effect on observed variables
- `ex5.13_latent_interaction.inp` — XWITH latent moderation
- For multilevel mediation: see `mediation_multilevel_latentcentering.inp` if bundled (otherwise see `references/multilevel.md`)
