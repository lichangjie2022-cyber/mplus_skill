# Mplus syntax fundamentals

Read this for every `.inp` you generate. The rules here are universal — every chapter, every analysis type assumes them.

## Block structure

A complete `.inp` is a sequence of named blocks. Each block begins with `BLOCKNAME:` and ends when the next block begins (or at end of file). The legal order is fixed; Mplus parses top-to-bottom and rejects out-of-order blocks.

```
TITLE:       (optional but always recommended — single description)
DATA:        (required: at minimum, FILE = ...)
VARIABLE:    (required: NAMES = ... at minimum)
DEFINE:      (optional: variable transformations, centering)
ANALYSIS:    (optional: defaults to ESTIMATOR = ML, TYPE = GENERAL)
MODEL:       (required: the model spec)
MODEL <suffix>:  (optional: MODEL INDIRECT, MODEL CONSTRAINT, MODEL POPULATION,
                  MODEL <groupname>, MODEL <classname>, MODEL PRIORS, MODEL MISSING)
OUTPUT:      (optional: what to print)
SAVEDATA:    (optional: write factor scores, residuals, imputations)
PLOT:        (optional: trajectories, posteriors, diagnostics)
MONTECARLO:  (replaces DATA / VARIABLE for simulation studies — see monte-carlo.md)
```

The four required blocks are TITLE, DATA, VARIABLE, MODEL. TITLE is "required" by convention more than the parser — omit at your own risk because output is hard to identify.

## Statement-level rules

- Every statement ends with `;`. Forgetting one is the #1 syntax error.
- Whitespace and newlines are insignificant within a block; long statements can wrap to the next line.
- Comments start with `!` and run to end of line. There is no block-comment syntax.
- Mplus is **case-insensitive** for keywords and variable names. The User's Guide uses lowercase variables and UPPERCASE keywords; copy that convention.
- Names are 1–8 characters, must start with a letter, alphanumeric + underscore. Names longer than 8 chars are silently truncated → name collisions.

## Variable naming and ranges

- `y1-y6` expands to `y1 y2 y3 y4 y5 y6`. Requires identical prefix + contiguous integer suffix.
- `y1-y10 x1 x2` mixes range and individual names.
- Ranges can be the LHS of `BY`, RHS of `BY`/`ON`/`WITH`, and inside `[]`. Examples:
  - `f BY y1-y6;` — load f on six indicators
  - `y1-y4 ON x1-x3;` — regress each of y1..y4 on x1..x3 (cross-product)
  - `[y1-y4];` — free four intercepts/means
  - `y1-y4@0;` — fix four variances to 0

## VARIABLE block — what goes where

```
VARIABLE:
  NAMES = y1-y6 x1 x2 g clus;     ! every column in the data file, in order
  USEVARIABLES = y1-y6 x1 x2;     ! what enters the analysis (default: all NAMES)
  MISSING = ALL (-99);            ! or: MISSING = y1-y6 (999) x (-1);
  CATEGORICAL = u1-u6;            ! ordered-categorical outcomes (use thresholds)
  NOMINAL = u1;                   ! unordered (use category-specific intercepts)
  COUNT = u1-u2;                  ! Poisson; (i) suffix for zero-inflated
  CENSORED = y (b);               ! (b) bottom, (a) above, (bi)/(ai) inflated
  GROUPING = g (1=male 2=female); ! multiple-group models
  CLUSTER = clus;                 ! multilevel nesting variable
  WITHIN = x1;                    ! L1-only variables (vary within cluster)
  BETWEEN = w1 w2;                ! L2-only variables (constant within cluster)
  CLASSES = c(3);                 ! latent class variable with 3 classes
  KNOWNCLASS = cg (g=0 g=1);      ! observed multinomial as a class variable
  AUXILIARY = (m) z1 z2;          ! keep z1 z2 as MAR correlates (FIML)
  WEIGHT = wt;                    ! complex-survey weights
  STRATIFICATION = strat;         ! complex-survey strata
  SURVIVAL = t (ALL);             ! event time(s)
  TIMECENSORED = tc (0=NOT 1=RIGHT);  ! censoring indicator + coding
  TSCORES = a1-a4;                ! individually-varying observation times
  LAGGED = y(1);                  ! y&1 = lag-1 (DSEM)
  IDVARIABLE = id;                ! used by SAVEDATA / TYPE=IMPUTATION
  CONSTRAINT = z;                 ! variable used inside MODEL CONSTRAINT
```

Rules:
- A variable can appear in **at most one** of `WITHIN`, `BETWEEN`. Variables in both levels (level-1 predictors with between-cluster variation) go in neither.
- `CATEGORICAL` and `NOMINAL` and `COUNT` and `CENSORED` are mutually exclusive per variable.
- Anything not in `USEVARIABLES` is invisible to MODEL. To keep a variable for missing-data purposes only, use `AUXILIARY`.

## DEFINE block — variable transformations

Runs *before* the model is fit. Useful for centering, log transforms, dummy creation, interaction terms.

```
DEFINE:
  CENTER x1 x2 (GRANDMEAN);     ! GROUPMEAN, GRANDMEAN, CLUSTERMEAN
  xz = x * z;                    ! create observed interaction
  IF (age GE 65) THEN old = 1;   ! conditional recode
  CUT score (2.5 5.0);           ! make a 3-category variable from continuous
  STANDARDIZE y1-y4;
```

DEFINE-created variables can be used in MODEL.

## ANALYSIS block — what's actually controllable

The most-used keys, with sensible defaults:

```
ANALYSIS:
  TYPE = GENERAL;            ! GENERAL is default; others: BASIC, MIXTURE, TWOLEVEL,
                             ! TWOLEVEL MIXTURE, TWOLEVEL RANDOM, THREELEVEL,
                             ! CROSSCLASSIFIED, EFA m n, RANDOM, IMPUTATION,
                             ! TWOLEVEL DYNAMIC RANDOM (DSEM)
  ESTIMATOR = ML;            ! ML (default for continuous), MLR (robust SE),
                             ! MLM, MLF, WLSMV (default with CATEGORICAL),
                             ! BAYES, GLS, ULS
  ALGORITHM = INTEGRATION;   ! needed for: latent interactions (XWITH), CATEGORICAL
                             ! latents + observed, RANDOM intercepts with categorical
  INTEGRATION = MONTECARLO(500);  ! or GAUSSHERMITE; reduces integration cost
  LINK = LOGIT;              ! LOGIT (default for CATEGORICAL+ML) or PROBIT
  PARAMETERIZATION = DELTA;  ! default; THETA for residual-variance parameterization
  MODEL = COVARIANCE;        ! COVARIANCE (default for SEM); NOMEANSTRUCTURE for
                             ! covariance-only models
  INFORMATION = EXPECTED;    ! EXPECTED (default with ML for continuous), OBSERVED
  STARTS = 500 50;           ! mixture: 500 random starts, refine best 50
  STITERATIONS = 20;         ! EM iterations per start
  PROCESSORS = 4;            ! parallel cores (Bayesian, mixture, integration)
  BOOTSTRAP = 1000;          ! resample-based CIs for indirect effects
  FBITERATIONS = 10000;      ! Bayesian: post-burn-in MCMC iterations
  BITERATIONS = (2000);      ! Bayesian: min/max iterations
  BSEED = 54321;             ! Bayesian: random seed
  BCONVERGENCE = 0.05;       ! Bayesian: PSRF threshold
```

## MODEL block — operators

Five operators do almost everything:

| Operator | Meaning | Example |
|---|---|---|
| `BY` | factor → indicators (measurement) | `f1 BY y1 y2 y3;` |
| `ON` | DV ← IV (regression) | `y1 ON x1 x2;` |
| `WITH` | covariance (residual or factor) | `f1 WITH f2;` |
| `\|` | latent variable definition (growth, random slope, latent interaction) | `i s \| y1@0 y2@1 y3@2;` |
| `XWITH` | latent-by-latent interaction | `f1xf2 \| f1 XWITH f2;` |

Inside MODEL, scaling and constraints use single characters:

| Character | Meaning | Example |
|---|---|---|
| `@value` | fix parameter to value | `f1@1;`  `y1@0;`  `f BY y1@1;` |
| `*value` | free parameter with starting value | `f BY y1*0.8;`  `[i*2 s*0.5];` |
| `*` alone | free parameter, no start | `f BY u1-u6*;` |
| `(label)` | parameter label (for equality, MODEL CONSTRAINT) | `y1 (resvar);`  `y1-y2 (1);` |
| `[var]` | mean / intercept | `[y1];`  `[f1@0];` |
| `[var$k]` | k-th threshold for CATEGORICAL var | `[u1$1] (a1);` |
| `var#k` | k-th class (latent or known) | `c#1`  `[c#1*0.5];` |

### BY conventions and identification

Default for `f1 BY y1 y2 y3;`:
- First indicator (`y1`) loading is fixed at 1 (scale).
- Other loadings (`y2`, `y3`) are free.
- Factor mean is fixed at 0 (default).
- Factor variance is free.

Alternate scaling — fix factor variance and free first loading (IRT-style):
```
f BY u1-u6*;
f@1;
```

To label loadings for equality across groups / time:
```
f1 BY y1 y2-y3 (lam2-lam3);   ! lam2 labels y2's loading, lam3 labels y3's
```

### ON conventions

`y1 y2 ON x1 x2;` regresses each LHS variable on the entire RHS set (cross product). For separate equations, list them on separate statements.

`y ON x;` defaults to:
- intercept free,
- residual variance free,
- slope free.

### WITH conventions

`y1 WITH y2;` adds a free covariance.

Default behavior:
- Without WITH, all observed exogenous variables are automatically correlated by Mplus (a key difference from lavaan).
- Endogenous variables (anything on the LHS of `ON`) are *not* correlated by default — request `WITH` explicitly.
- To suppress default covariances among exogenous: `<v1> WITH <v2>@0;`.

### Means and intercepts with `[]`

`[y1];` frees y1's mean (continuous) or intercept (if y1 is endogenous).
`[u1$1];` frees the first threshold of categorical u1.
`[i s];` frees the means of latent growth factors i and s.

A variable not in brackets has its mean/intercept estimated by default for endogenous and held at 0 for some structural roles. When unsure, write the bracket statement explicitly.

## OUTPUT options that matter

Always defensible defaults:

```
OUTPUT: SAMPSTAT STDYX MODINDICES (10) CINTERVAL;
```

- `SAMPSTAT` — sample statistics (means, covariances, thresholds). Lets the reader sanity-check the data.
- `STDYX` — fully standardized estimates (continuous predictors, continuous outcomes). Use for effect-size interpretation. `STDY` standardizes only the outcome (for categorical predictors).
- `MODINDICES (k)` — modification indices > k (default 10). Useful for CFA / SEM diagnosis; skip for mixture.
- `CINTERVAL` — 95% confidence intervals. Add `(BOOTSTRAP)` for bootstrap CIs (when ANALYSIS uses BOOTSTRAP=).
- `RESIDUAL` — residual covariance matrix (continuous SEM diagnostics).
- `TECH1` — parameter specification matrix (Σ, ν, α, etc.). Use to confirm the model you wrote is the model Mplus parsed.
- `TECH3` — covariance/correlation of parameter estimates.
- `TECH4` — model-implied means/covariances/correlations among latents.
- `TECH8` — iteration log (also Bayesian PSRF table).
- `TECH9` — Monte Carlo summary (parameter coverage, power).
- `TECH10` — bivariate fit info for CATEGORICAL outcomes.
- `TECH11` — Lo-Mendell-Rubin LRT for mixture (K vs K-1).
- `TECH14` — bootstrap LRT for mixture (K vs K-1, slower than TECH11).
- `TECH15` — joint and marginal class probabilities (LTA).

Do not request `MODINDICES` with Bayesian or mixture — it doesn't print and Mplus will warn.

## SAVEDATA block

```
SAVEDATA:
  FILE = fscores.dat;
  SAVE = FSCORES;              ! factor scores (and SEs)
  SAVE = FSCORES(20);          ! 20 plausible values per observation
  SAVE = CPROBABILITIES;       ! latent class posterior probs (mixture)
  SAVE = LRESPONSES;           ! latent response variables (categorical)
  SAVE = RESIDUAL;             ! casewise residuals
  TYPE = IMPUTATION;           ! signals a multiple-imputation file list (with DATA IMPUTATION)
```

The saved file is plain text; with `IDVARIABLE = id;` the first column is the id.

## PLOT block

```
PLOT:
  TYPE = PLOT1;                ! univariate distributions of observed
  TYPE = PLOT2;                ! observed vs. estimated; trace plots (BAYES)
  TYPE = PLOT3;                ! growth trajectories, class-specific plots, posteriors
  SERIES = y1-y4(s);           ! plot y1..y4 against time scores from slope s
  SERIES = y1-y4(*);           ! plot against position (1,2,3,4)
```

## Defaults to remember

These bite people who expect lavaan-like behavior:

- Observed exogenous variables are **all mutually correlated by default**. Equivalent to lavaan's `meanstructure=TRUE` with all `~~` among exogenous filled in.
- The first indicator's loading is **fixed at 1**, factor variance free. Opposite of some other programs.
- With `CATEGORICAL`, the default estimator changes from ML to WLSMV.
- With FIML (ML on data with `.` missing): missingness on the **outcomes** is fine; missingness on **observed exogenous predictors** drops those rows from the likelihood unless you explicitly include the predictors in the model (e.g., predict them with means/variances, or list them in AUXILIARY).
- `MODEL INDIRECT` requires named paths and only works for some model classes (mostly SEM with observed mediators or latent mediators with continuous indicators). For more complex indirect effects (mixture, multilevel, latent interactions), compute them in `MODEL CONSTRAINT` with `NEW(ab); ab = a * b;`.

## Minimal templates

The shortest legal `.inp` per analysis family — copy and adapt:

**Regression / path:**
```
TITLE:    short description
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = y x1-x3;
MODEL:    y ON x1-x3;
```

**CFA (continuous):**
```
TITLE:    cfa, two factors
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = y1-y6;
MODEL:    f1 BY y1-y3;
          f2 BY y4-y6;
OUTPUT:   STDYX;
```

**CFA (categorical):**
```
TITLE:    cfa, ordinal indicators
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = u1-u6;
          CATEGORICAL = u1-u6;
MODEL:    f1 BY u1-u3;
          f2 BY u4-u6;
OUTPUT:   STDYX;
```

**Two-level random-intercept regression:**
```
TITLE:    multilevel regression
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = y x w clus;
          WITHIN = x;
          BETWEEN = w;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL;
MODEL:    %WITHIN%  y ON x;
          %BETWEEN% y ON w;
```

**Linear growth:**
```
TITLE:    linear growth, four waves
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = y1-y4;
MODEL:    i s | y1@0 y2@1 y3@2 y4@3;
```

**Latent class analysis:**
```
TITLE:    LCA, six binary items, two classes
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = u1-u6;
          CATEGORICAL = u1-u6;
          CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
MODEL:    %OVERALL%
OUTPUT:   TECH11 TECH14;
```

From any of these, the corresponding `references/<topic>.md` file shows how to add covariates, constraints, group structure, etc.
