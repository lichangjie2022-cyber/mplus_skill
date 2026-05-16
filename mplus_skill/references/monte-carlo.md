# Monte Carlo simulation and power analysis (User's Guide Ch. 12)

Mplus replaces the DATA + VARIABLE blocks with a single `MONTECARLO:` block that specifies population parameters, generates synthetic data, fits a model to each replicate, and aggregates results. Used for: power analysis, sample-size determination, performance evaluation of estimators, and testing model misspecification.

## Decision tree

```
User wants to...
├─ Estimate power for a planned study
│   → MONTECARLO + MODEL POPULATION (true effects) + MODEL (fitted) + OUTPUT: TECH9
├─ Determine required sample size
│   → Run MONTECARLO at multiple NOBSERVATIONS, find N where power ≥ .80
├─ Compare two estimators on the same data-generating model
│   → Two runs with same MODEL POPULATION, different ESTIMATOR in ANALYSIS
├─ Test a model fit under misspecification (e.g., LCA when truth is single class)
│   → MODEL POPULATION differs from MODEL
├─ Generate data to use elsewhere
│   → MONTECARLO with REPSAVE = ALL and SAVE = mygen*.dat
└─ Replicate a published power analysis
    → Translate authors' MODEL POPULATION into the MONTECARLO block
```

## Skeletons

### Power analysis for CFA with covariates (MIMIC) — `ex12.1`

```
TITLE:    Monte Carlo power for CFA MIMIC, missing data
MONTECARLO:
          NAMES = y1-y4 x1 x2;
          NOBSERVATIONS = 500;
          NREPS = 500;                       ! number of replicates
          SEED = 4533;
          CUTPOINTS = x2(1);                  ! make x2 dichotomous at point 1
          PATMISS = y1(.1) y2(.2) y3(.3) y4(1) |
                    y1(1) y2(.1) y3(.2) y4(.3);
          PATPROBS = .4 | .6;                 ! 40% pattern 1, 60% pattern 2

MODEL POPULATION:
          [x1-x2@0];
          x1-x2@1;
          f BY y1@1 y2-y4*1;
          f*.5;
          y1-y4*.5;
          f ON x1*1 x2*.3;

MODEL:    f BY y1@1 y2-y4*1;
          f*.5;
          y1-y4*.5;
          f ON x1*1 x2*.3;

OUTPUT:   TECH9;                              ! power summary
```

Key pieces:
- `NAMES` — variables to generate.
- `NOBSERVATIONS` — sample size per replicate.
- `NREPS` — replicates; 500 is typical for stable power estimates; 100 minimum.
- `SEED` — for reproducibility.
- `CUTPOINTS` — make a generated continuous variable into a dummy (e.g., `x2(1)` cuts x2 at z=1, ~16% above).
- `PATMISS` / `PATPROBS` — induce missing-data patterns.
- `MODEL POPULATION` — the true generating model (population parameters).
- `MODEL` — the analyst's fitted model (often identical, can differ for misspecification studies).
- `OUTPUT: TECH9;` — reports power = proportion of replicates in which each parameter is significant at α=.05.

### Power table to read

In TECH9, the relevant columns:
- **% Sig Coeff** — power (proportion of replicates where parameter is significant)
- **Average** — mean of estimates across replicates
- **Std Dev** — empirical SE
- **Average SE** — mean of model-reported SE (should match Std Dev if SEs are accurate)
- **Coverage** — % of 95% CIs containing the true value (target: .95)
- **% Sig** — power

Target: power ≥ .80 for parameters of interest, coverage ≈ .95.

### Multilevel MC (`ex12.7` family pattern)

```
MONTECARLO:
          NAMES = y1-y4 x w;
          NCSIZES = 3;
          CSIZES = 40(5) 50(10) 20(15);     ! 5 clusters size 40, 10 size 50, 15 size 20
          NREPS = 100;
          SEED = 12345;
          WITHIN = x;
          BETWEEN = w;

MODEL POPULATION:
          %WITHIN%
          x@1;
          iw sw | y1@0 y2@1 y3@2 y4@3;
          iw ON x*1;
          sw ON x*0.25;
          iw*1; sw*0.2;
          %BETWEEN%
          w@1;
          ib sb | y1@0 y2@1 y3@2 y4@3;
          y1-y4@0;
          ib ON w*0.5;
          sb ON w*0.25;
          [ib*1 sb*0.5];
          ib*0.2; sb*0.1;

ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%
          iw sw | y1@0 y2@1 y3@2 y4@3;
          y1-y4 (1);
          iw sw ON x;
          %BETWEEN%
          ib sb | y1@0 y2@1 y3@2 y4@3;
          y1-y4@0;
          ib sb ON w;
OUTPUT:   TECH9;
```

### Mixture MC (data generated from K classes, fit with k classes)

```
MONTECARLO:
          NAMES = y x;
          NOBSERVATIONS = 500;
          NREPS = 100;
          SEED = 12345;
          GENCLASSES = c(2);                  ! generating model has 2 classes
          CLASSES = c(1);                     ! fitted model is single-class (test misspec)

MODEL POPULATION:
          %OVERALL%
          c#1 ON x*0.5;
          [c#1*-1];
          %c#1%
          [y*0];
          y*1;
          %c#2%
          [y*2];
          y*1;

ANALYSIS: TYPE = MIXTURE;
MODEL:    y ON x;                              ! ignores class structure
OUTPUT:   TECH9;
```

### Survival MC

```
MONTECARLO:
          NAMES = t x;
          NOBSERVATIONS = 500;
          NREPS = 100;
          SEED = 12345;
          GENERATE = t(s 20*1);                 ! survival time, 20 intervals of width 1
          SURVIVAL = t(ALL);
          HAZARDC = t(0.5);                     ! cumulative hazard parameter

MODEL POPULATION:
          t ON x*0.5;
          [x@0]; x@1;

MODEL:    t ON x;
OUTPUT:   TECH9;
```

### External data Monte Carlo (analyze data generated elsewhere)

If the user has 500 datasets simulated externally (e.g., in R) and wants Mplus to fit a model to each and aggregate:

```
DATA:     FILE = mclist.dat;                    ! one filename per line
          TYPE = MONTECARLO;
VARIABLE: NAMES = y1-y4 x;
ANALYSIS: ...
MODEL:    ...
OUTPUT:   TECH9;
```

## Saving generated data

```
MONTECARLO:
          NAMES = ...;
          NREPS = 100;
          REPSAVE = ALL;                        ! save data from all reps
          SAVE = mygen*.dat;                    ! mygen1.dat .. mygen100.dat + a list file
```

## ANALYSIS settings

The ANALYSIS block in a Monte Carlo file works like in a regular Mplus run — it specifies how each replicate is fit. Common additions:

```
ANALYSIS: ESTIMATOR = ML;                       ! or MLR, BAYES, WLSMV
          TYPE = MIXTURE;                       ! for mixture MC
          STARTS = 20 5;                        ! mixture starts per replicate (keep small to stay fast)
          PROCESSORS = 4;
```

## Pitfalls

1. **MONTECARLO replaces DATA and VARIABLE.** Don't try to add a DATA block — Mplus rejects it.
2. **Population variances and intercepts must be set explicitly.** Leaving `f` or `y1-y4` variance unspecified means Mplus generates them as 1 — which may not be what you want. Use `f*0.5;` and `y1-y4*0.5;` in MODEL POPULATION.
3. **MODEL POPULATION uses starting-value syntax (`*value`)** to set true population values. Don't use `@value` (which would fix the parameter when fitting — different intent).
4. **PATMISS / PATPROBS sum to 1.** PATPROBS must sum to 1 across patterns.
5. **Power < 1 for fixed parameters.** A parameter fixed to a value (e.g., the marker loading at 1) is always "significant" with power 1. Real power questions concern freely-estimated parameters.
6. **Convergence failures in replicates.** TECH9 reports number of replicates that converged. If many fail, the model is not stably identified for that N — increase N or simplify model.
7. **Bayes Monte Carlo.** Possible but extremely slow (each replicate runs MCMC). Use only when ML is biased or unavailable.
8. **CUTPOINTS for categorical.** `CUTPOINTS = x(1);` cuts at z=1 (~16% above). Use `(0)` for a 50/50 split. For multiple thresholds, list multiple cutpoints: `x(-1 1)` makes a 3-category variable.
9. **NREPS too small.** 100 reps gives noisy power estimates (~ ±10 percentage points). 500 is a better default; 1000+ for publication-quality.
10. **External Monte Carlo paths.** Each filename in the list must resolve from the .inp's working directory; use a relative path or absolute path.

## Canonical examples in `assets/examples/`

- `ex12.1_mc_cfa_mimic.inp` — MIMIC power analysis with missing-data patterns
- `ex12.4_mc_multilevel_growth.inp` — multilevel growth Monte Carlo with NCSIZES
