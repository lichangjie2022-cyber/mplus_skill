# Latent growth curves and survival analysis (User's Guide Ch. 6)

Growth and survival models share the `|` operator and rely on careful time-score / event-time coding. This reference covers: linear and quadratic latent growth, free time scores, parallel-process growth, multiple-indicator growth, growth with covariates (time-invariant and time-varying), continuous-time (Cox) and discrete-time survival.

## Decision tree

```
Growth questions...
├─ Repeated measures of one outcome, want trajectory
│   ├─ Linear → i s | y1@0 y2@1 ... yT@(T-1)
│   ├─ Quadratic → i s q | y1@0 y2@1 ... yT@(T-1)^2
│   ├─ Free time → i s | y1@0 y2@1 y3* y4*  (estimate later time scores)
│   ├─ Unequal time gaps → i s | y1@0 y2@1.5 y3@4 y4@7 (whatever the gaps are)
│   └─ Individually varying times → TSCORES + TYPE=RANDOM + i s | y AT a
├─ Multiple-indicator growth (each wave has a CFA factor)
│   └─ f1 BY ... ; f2 BY ... ; ... ; i s | f1@0 f2@1 ...
├─ Two processes growing together
│   └─ Parallel-process: i1 s1 | ... ; i2 s2 | ... ; s1 ON i2 etc.
├─ Growth on categorical outcomes
│   └─ CATEGORICAL = y1-yT; ESTIMATOR = WLSMV (or ML)
├─ Predictors of trajectory
│   ├─ Time-invariant covariate → i s ON x
│   ├─ Time-varying covariate → yT ON aT (per wave)
│   └─ Both → combine
└─ Discontinuous / piecewise growth
    └─ Two slopes: s1 | y1@0 y2@1 y3@1 y4@1; s2 | y1@0 y2@0 y3@0 y4@1;

Survival questions...
├─ Continuous-time event (Cox-like)
│   └─ SURVIVAL = t; TIMECENSORED = tc(0=NOT 1=RIGHT); MODEL: t ON x;
├─ Discrete-time event (intervals)
│   └─ Multiple binary indicators u1-uK per interval; CATEGORICAL = u1-uK
├─ Event predicted by latent factor
│   └─ Latent factor BY indicators + t ON factor
└─ Mixture of growth + survival (joint model)
    └─ See chap6 ex6.23 (joint trajectory + event)
```

## Growth model skeletons

### Linear growth, four waves, continuous outcome

```
TITLE:    linear growth, 4 waves
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y4;
MODEL:    i s | y1@0 y2@1 y3@2 y4@3;
OUTPUT:   STDYX TECH4;
```

The `|` operator simultaneously defines two latent variables (`i`, `s`) and sets:
- Loadings of i on y1..y4 fixed at 1 (intercept)
- Loadings of s on y1..y4 fixed at 0,1,2,3 (linear slope time scores)
- Means and variances of i, s freely estimated
- Covariance of i, s freely estimated
- Residual variances of y1..y4 freely estimated

### Quadratic growth

```
MODEL:    i s q | y1@0 y2@1 y3@4 y4@9;     ! time-squared scores
```

For 4 waves with gaps 0, 1, 2, 3, time-squared is 0, 1, 4, 9.

### Free time scores (estimating non-linear shape)

```
MODEL:    i s | y1@0 y2@1 y3* y4*;     ! 3rd and 4th time scores estimated
```

For identification, two time scores must be fixed (typically the first two at 0 and 1, defining the slope's metric).

### Individually-varying observation times

```
VARIABLE: NAMES = y1-y4 a1-a4;
          TSCORES = a1-a4;             ! individual observation times
ANALYSIS: TYPE = RANDOM;
MODEL:    i s | y1-y4 AT a1-a4;        ! AT keyword pairs y with time
```

### Time-invariant covariates predicting trajectory

```
MODEL:    i s | y1@0 y2@1 y3@2 y4@3;
          i s ON x1 x2;                 ! TI covariates on growth factors
```

### Time-varying covariates

```
MODEL:    i s | y1@0 y2@1 y3@2 y4@3;
          y1 ON a1;
          y2 ON a2;                     ! regression at each wave
          y3 ON a3;
          y4 ON a4;
```

### Parallel-process growth

```
MODEL:    i1 s1 | y11@0 y12@1 y13@2 y14@3;
          i2 s2 | y21@0 y22@1 y23@2 y24@3;
          s1 ON i2;                     ! does initial level of process 2 predict slope of process 1?
          s2 ON i1;
          i1 WITH i2;
          s1 WITH s2;
```

### Multiple-indicator growth (latent factors at each wave)

```
MODEL:    f1 BY y11
                y21-y31 (1-2);          ! loadings constrained equal across waves (1-2)
          f2 BY y12
                y22-y32 (1-2);
          f3 BY y13
                y23-y33 (1-2);
          [y11 y12 y13] (3);             ! intercept invariance
          [y21 y22 y23] (4);
          [y31 y32 y33] (5);
          i s | f1@0 f2@1 f3@2;          ! growth on latent factors
          [f1@0 f2@0 f3@0];               ! mean structure: factor means at 0 (i picks them up)
```

This is `ex6.14`. The labels `(1-2)`, `(3)`, etc. enforce **scalar invariance** of the measurement model across waves — a prerequisite for interpreting growth in the latent metric.

### Growth on categorical outcomes

```
VARIABLE: NAMES = u1-u4;
          CATEGORICAL = u1-u4;
MODEL:    i s | u1@0 u2@1 u3@2 u4@3;
          [u1$1-u4$1] (1);              ! threshold invariance across waves
OUTPUT:   TECH1;
```

WLSMV is the default estimator. The (1) constraint enforces invariant thresholds — necessary for the growth interpretation.

### Piecewise growth (two-piece linear, breakpoint at wave 3)

```
MODEL:    i s1 s2 | y1@0 y2@1 y3@2 y4@2 y5@2;     ! s1 = slope before wave 3
          i s1 s2 | y1@0 y2@0 y3@0 y4@1 y5@2;     ! s2 = slope after wave 3
```

(Note: pieces are commonly written as two separate `|` lines; check ex6.13 for exact syntax — the version above is illustrative.)

### Growth model with class-specific trajectories (GMM)

See `references/mixture-longitudinal.md`. The pattern adds `CLASSES = c(K)`, `TYPE = MIXTURE`, and `%c#k%` blocks within MODEL.

## Survival model skeletons

### Continuous-time survival (Cox regression)

```
TITLE:    Cox regression
DATA:     FILE = data.dat;
VARIABLE: NAMES = t x tc;
          SURVIVAL = t;
          TIMECENSORED = tc (0 = NOT 1 = RIGHT);
MODEL:    t ON x;
OUTPUT:   STDYX;
```

This is `ex6.20`. Time-to-event variable `t` is declared in SURVIVAL; censoring indicator `tc` has the value 1 = right-censored, 0 = event observed. The regression `t ON x;` is a hazard regression.

### Continuous-time with parametric baseline hazard

```
VARIABLE: NAMES = t x;
          SURVIVAL = t (20*1);         ! 20 intervals of width 1
          TIMECENSORED = tc (0=NOT 1=RIGHT);
ANALYSIS: BASEHAZARD = ON;
MODEL:    [t#1-t#21];                  ! intercepts for each interval
          t ON x;
```

`BASEHAZARD = ON` makes the baseline hazard non-parametric (step function); `OFF` enforces proportional hazards without estimating a baseline (Cox).

### Discrete-time survival

Code event status as a sequence of binary indicators u1, u2, ..., uK (one per interval; u_k = 1 means event in interval k, 0 if survived past it):

```
VARIABLE: NAMES = u1-u5 x;
          CATEGORICAL = u1-u5;
MODEL:    f BY u1-u5@1;                 ! latent frailty (all loadings = 1)
          f@0;                          ! variance fixed at 0 → discrete-time hazard model
          f ON x;                       ! covariate on hazard
```

Equivalent to a sequence of logistic regressions with a single set of covariate effects (proportional-odds discrete hazard model).

### Survival with covariates and latent predictors

```
VARIABLE: NAMES = t u1-u4 x tc;
          SURVIVAL = t;
          TIMECENSORED = tc;
          CATEGORICAL = u1-u4;
MODEL:    f BY u1-u4;
          t ON f x;
          f ON x;
```

### Joint trajectory + survival (growth + Cox)

```
VARIABLE: NAMES = y1-y4 t tc x;
          SURVIVAL = t;
          TIMECENSORED = tc;
ANALYSIS: ALGORITHM = INTEGRATION;
MODEL:    i s | y1@0 y2@1 y3@2 y4@3;
          i s ON x;
          t ON i s x;                    ! hazard depends on growth factors and covariate
```

## Output and plotting

```
OUTPUT:   STDYX TECH4 CINTERVAL;
PLOT:     TYPE = PLOT3;
          SERIES = y1-y4(s);             ! plot trajectories grouped by slope
```

`PLOT3` produces:
- Sample-mean and estimated-mean trajectories
- Individual estimated trajectories
- Loadings vs. time scores

For survival, `PLOT: TYPE = PLOT3;` produces Kaplan-Meier curves and estimated survival functions.

## Common variants

**Random slopes (within multilevel growth)** — see `references/multilevel.md`.

**Negative slope variance.** If `s` variance is estimated near 0 or negative, the slope is essentially fixed across people. Constrain `s@0` for a fixed-effects growth model.

**Non-equidistant time scores.** Always set time scores to reflect actual time, not wave number. If measurements are at months 0, 3, 6, 18, use `y1@0 y2@3 y3@6 y4@18`.

**Growth in standardized metric.** Constrain residual variances equal across waves, or use multiple-indicator growth with scalar invariance.

## Pitfalls

1. **Time scores fix the metric.** `y1@0 y2@1 ...` means: intercept = expected value at time 0, slope = expected change per unit time. If you write `y1@0 y2@1 y3@2 y4@3` but the actual gaps are 6 months apart, the slope is per-6-months.
2. **Quadratic growth needs lots of waves.** 3 waves: linear only. 4 waves: linear + quadratic identified but unstable. 5+ waves: comfortable for quadratic.
3. **Free time scores require fixing two anchors** (typically first and second waves at 0 and 1) for identification.
4. **Categorical growth requires threshold invariance** across waves (the `(1)` constraint) for the slope to have a clean interpretation in the latent-response metric.
5. **Discrete-time survival vs. growth confusion.** Both use repeated indicators. Discrete-time survival uses *cumulative* survival pattern (once event happens, subsequent intervals are missing or 1). Growth uses repeated measurement of the same construct over time. Get the data structure right before specifying the model.
6. **Right-censoring code direction.** `TIMECENSORED = tc (0 = NOT 1 = RIGHT);` means tc=0 → event observed, tc=1 → right-censored. Different conventions exist; always restate to the user which code means what.
7. **`SURVIVAL = t;` requires positive times.** A time of 0 = immediate event, can cause issues. Add a small constant or shift time slightly if needed.
8. **Parallel process model with too few waves.** Cross-process effects (s1 ON i2 etc.) need adequate within-process variance to be identified. 3 waves per process is bare minimum; 4+ recommended.

## Canonical examples in `assets/examples/`

- `ex6.1_lgm_linear.inp` — linear growth, 4 waves, continuous outcome (minimal)
- `ex6.10_lgm_covariates.inp` — LGM with time-invariant and time-varying covariates
- `ex6.14_multi_indicator_lgm.inp` — multiple-indicator linear growth with invariance constraints
- `ex6.20_survival_cox.inp` — continuous-time survival (Cox regression)
