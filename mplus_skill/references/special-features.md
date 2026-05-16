# Special Mplus features: RI-CLPM, BSEM, ESEM, DSEM, IRT, alignment, RI-LTA

Contemporary modeling approaches not covered as discrete chapters in the User's Guide but heavily used in modern applied work. Each section is self-contained.

## Table of contents

1. [RI-CLPM (random-intercept cross-lagged panel)](#ri-clpm)
2. [BSEM (Bayesian SEM with informative priors)](#bsem)
3. [ESEM (exploratory SEM)](#esem)
4. [DSEM / RDSEM (dynamic SEM, intensive longitudinal)](#dsem)
5. [IRT (item response theory)](#irt)
6. [Alignment (many-group invariance)](#alignment)
7. [RI-LTA (random-intercept LTA)](#ri-lta)

---

## <a name="ri-clpm"></a>1. RI-CLPM — Random-intercept cross-lagged panel model

Separates stable between-person differences from within-person fluctuations. Each person gets a random intercept on each variable, and the cross-lagged structure operates on the residual within-person scores.

```
TITLE:    RI-CLPM: x and y measured at 4 waves
DATA:     FILE = data.dat;
VARIABLE: NAMES = x1-x4 y1-y4;
MODEL:
          ! Random intercepts (stable between-person factors)
          RIx BY x1@1 x2@1 x3@1 x4@1;
          RIy BY y1@1 y2@1 y3@1 y4@1;
          [x1-x4@0 y1-y4@0];                  ! item intercepts at 0; means in RIs
          [RIx RIy];                          ! free RI means

          ! Within-person residual scores at each wave
          wx1 BY x1@1; wx2 BY x2@1; wx3 BY x3@1; wx4 BY x4@1;
          wy1 BY y1@1; wy2 BY y2@1; wy3 BY y3@1; wy4 BY y4@1;
          x1-x4@0 y1-y4@0;                    ! observed residuals zero (variance absorbed by w*)

          ! Autoregressive and cross-lagged on within-person scores
          wx2 ON wx1 wy1;
          wx3 ON wx2 wy2;
          wx4 ON wx3 wy3;
          wy2 ON wy1 wx1;
          wy3 ON wy2 wx2;
          wy4 ON wy3 wx3;

          ! Residual covariances within wave
          wx1 WITH wy1;
          wx2 WITH wy2;
          wx3 WITH wy3;
          wx4 WITH wy4;

          ! RIs are orthogonal to time-1 within-person scores by construction
          RIx WITH wx1@0; RIy WITH wy1@0;
          RIx WITH wy1@0; RIy WITH wx1@0;
          RIx WITH RIy;
OUTPUT:   STDYX;
```

Variants:
- **Constrain autoregressive paths equal across waves**: label and equate.
- **Stationary RI-CLPM**: also equate cross-lagged and residual variances.
- **Extended RI-CLPM** with three or more variables: add a third RI factor and cross-lagged structure.

Pitfall: writing a normal CLPM (no RIs) and then claiming RI-CLPM interpretation is the most common error in this literature. The RI factor is essential.

---

## <a name="bsem"></a>2. BSEM — Bayesian SEM with informative priors

Bayesian estimation with small-variance priors on cross-loadings (or other parameters) to approximate "approximate zero" rather than the hard zero of a regular CFA. Useful when:
- A strict CFA fits badly because of small cross-loadings.
- Measurement invariance fails because of small intercept differences (approximate invariance).

```
TITLE:    BSEM with small-variance priors on cross-loadings

DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y10;

ANALYSIS: ESTIMATOR = BAYES;
          PROCESSORS = 4;
          FBITERATIONS = 20000;
          BSEED = 12345;

MODEL:    f1 BY y1-y5*0.8;
          f2 BY y6-y10*0.8;
          ! Cross-loadings: y1-y5 on f2; y6-y10 on f1
          f1 BY y6-y10*0 (cl1-cl5);
          f2 BY y1-y5*0 (cl6-cl10);
          f1@1; f2@1;
          [f1@0 f2@0];

MODEL PRIORS:
          cl1-cl10 ~ N(0, 0.01);              ! small-variance normal priors → nearly zero

OUTPUT:   STDYX TECH8;
PLOT:     TYPE = PLOT2;
```

The prior variance 0.01 means ~95% of the prior mass is within ±0.2 of zero. Tune based on metric of indicators.

Approximate invariance pattern:
```
MODEL PRIORS:
          interceptdiff1-interceptdiff5 ~ N(0, 0.05);  ! small intercept differences across groups
```

---

## <a name="esem"></a>3. ESEM — Exploratory SEM

EFA inside a CFA/SEM framework. Rotation is applied to a block of factors specified together. ESEM-within-CFA is a variant where the rotated solution is taken as fixed and embedded in a larger SEM.

### Basic ESEM

```
TITLE:    ESEM with target rotation

DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y10;

ANALYSIS: ROTATION = TARGET;                  ! or GEOMIN(OBLIQUE)

MODEL:    f1 f2 BY y1-y10 (*1);               ! '*1' = block rotation marker
          f1 BY y6-y10 ~ 0 (*1);              ! target zeros for f1 on items 6-10
          f2 BY y1-y5  ~ 0 (*1);              ! target zeros for f2 on items 1-5

OUTPUT:   STDYX;
```

The `~ 0` syntax marks intended zeros that rotation tries to achieve.

### ESEM-within-CFA

After identifying the rotation in ESEM, hard-code the rotated loadings as starting values in a regular CFA:

```
MODEL:    f1 BY y1*0.85 y2*0.78 y3*0.70 y4*0.65 y5*0.60
                y6*0.10 y7*0.05 y8*0.02 y9*0.01 y10*0.03;
          f2 BY y1*0.05 y2*0.10 y3*0.15 y4*0.08 y5*0.05
                y6*0.80 y7*0.75 y8*0.70 y9*0.65 y10*0.60;
          f1@1; f2@1;
          f1 WITH f2*0.3;
```

Then can extend with covariates, multi-group invariance, etc. (these don't work directly in ESEM mode).

---

## <a name="dsem"></a>4. DSEM / RDSEM — Dynamic SEM for intensive longitudinal data

Within-person time-series modeling with autoregressive and cross-lagged effects, random per person. `TYPE = TWOLEVEL DYNAMIC RANDOM` or `TYPE = CROSS RANDOM`.

### Basic DSEM (AR(1) within person)

```
TITLE:    DSEM: lag-1 autoregression on y, random across people

DATA:     FILE = ema_long.dat;                ! one row per occasion
VARIABLE: NAMES = id y x;
          USEVARIABLES = y x;
          CLUSTER = id;
          LAGGED = y(1) x(1);                  ! create y&1, x&1 (lag-1 versions)

ANALYSIS: TYPE = TWOLEVEL DYNAMIC RANDOM;
          ESTIMATOR = BAYES;
          PROCESSORS = 4;
          FBITERATIONS = 5000;
          BSEED = 42;

MODEL:    %WITHIN%
          phi | y ON y&1;                      ! random autoregression
          beta | y ON x;                        ! random concurrent effect

          %BETWEEN%
          y phi beta;                           ! free between-person variation
          [y phi beta];
          y WITH phi beta;
          phi WITH beta;

OUTPUT:   STDYX TECH8;
PLOT:     TYPE = PLOT3;
```

### Cross-lagged DSEM (two variables, lagged effects between them)

```
MODEL:    %WITHIN%
          y ON y&1 x&1;
          x ON x&1 y&1;
          y WITH x;                            ! concurrent within-time covariance
```

### RDSEM (residual DSEM — captures cross-classified random effects within time series)

```
ANALYSIS: TYPE = CROSS RANDOM;
          ESTIMATOR = BAYES;
```

DSEM is among the slowest models in Mplus. Expect long runtimes for many time points × many people.

---

## <a name="irt"></a>5. IRT — Item response theory parameterization

IRT models are CFA models with categorical indicators, identified by fixing factor variance to 1 (instead of fixing the first loading to 1). The latent factor is "ability θ"; loadings become discrimination parameters; thresholds become difficulty parameters.

### 2-Parameter Logistic (2PL)

```
TITLE:    2PL IRT model

DATA:     FILE = data.dat;
VARIABLE: NAMES = u1-u20;
          CATEGORICAL = u1-u20;

ANALYSIS: ESTIMATOR = MLR;
          LINK = LOGIT;

MODEL:    theta BY u1*-u20*;                  ! all loadings free (discrimination)
          theta@1;                            ! factor variance = 1 (IRT identification)
          [theta@0];                          ! factor mean = 0

OUTPUT:   STDYX TECH1;
```

In IRT terms:
- The loadings `theta BY u1*` = item discrimination a_i (factor-loading scale; divide by √(1 - a²) for IRT a-parameter scale).
- The thresholds `[u1$1]` = item difficulty b_i.

### Graded Response Model (GRM) — polytomous items

```
VARIABLE: CATEGORICAL = u1-u5;                ! polytomous; thresholds vary per item
ANALYSIS: ESTIMATOR = MLR; LINK = LOGIT;
MODEL:    theta BY u1*-u5*;
          theta@1;
          [theta@0];
```

GRM is the default for `CATEGORICAL` polytomous + ML estimator.

### Save IRT-style factor scores

```
SAVEDATA: FILE = irt_scores.dat;
          SAVE = FSCORES;
          IDVARIABLE = id;
```

For plausible values for secondary analysis, `SAVE = FSCORES(20);`.

---

## <a name="alignment"></a>6. Alignment — many-group measurement invariance

Used when many groups make traditional MGCFA infeasible. Alignment automatically identifies a partial-invariance solution that minimizes non-invariance across all groups.

```
TITLE:    Alignment with 30 groups

DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y6 g;
          USEVARIABLES = y1-y6 g;
          CLASSES = c(30);                    ! number of groups
          KNOWNCLASS = c (g = 1 g = 2 g = 3 ... g = 30);

ANALYSIS: ESTIMATOR = ML;
          TYPE = MIXTURE;
          ALIGNMENT = FREE;                   ! or FIXED (fix one group's mean and variance)
          PROCESSORS = 4;

MODEL:    %OVERALL%
          f1 BY y1-y3;
          f2 BY y4-y6;

OUTPUT:   ALIGN;                              ! prints alignment-based invariance summary
```

Output includes:
- Per-parameter non-invariance counts (which loadings/intercepts are non-invariant in which groups)
- Latent means / variances per group on a comparable metric
- R² for the alignment solution

`ALIGNMENT = FREE` lets all means and variances vary; `ALIGNMENT = FIXED` fixes the first group as reference. FREE is more common.

---

## <a name="ri-lta"></a>7. RI-LTA — Random-intercept latent transition

Adds a random intercept to LTA to absorb stable between-person heterogeneity, isolating *change* in latent class membership.

```
TITLE:    RI-LTA, two time points, 3 classes per wave

DATA:     FILE = data.dat;
VARIABLE: NAMES = u11-u15 u21-u25;
          CATEGORICAL = u11-u15 u21-u25;
          CLASSES = c1(3) c2(3);

ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
          ALGORITHM = INTEGRATION;
          INTEGRATION = MONTECARLO(500);

MODEL:    %OVERALL%
          f BY u11-u25*;                      ! random intercept factor across all waves' items
          f@1;
          c2 ON c1 f;                          ! transition depends on c1 AND random intercept

MODEL c1: %c1#1% [u11$1-u15$1] (1-5);
          %c1#2% [u11$1-u15$1] (6-10);
          %c1#3% [u11$1-u15$1] (11-15);

MODEL c2: %c2#1% [u21$1-u25$1] (1-5);          ! same labels as c1 → measurement invariance
          %c2#2% [u21$1-u25$1] (6-10);
          %c2#3% [u21$1-u25$1] (11-15);

OUTPUT:   TECH1 TECH8 TECH15;
```

The random intercept `f` absorbs cross-wave stability that would otherwise inflate apparent stayer rates in regular LTA. See Muthén & Asparouhov 2022 for more.

---

## Cross-cutting pitfalls

1. **BSEM convergence**: small-variance priors can prevent MCMC mixing. If PSRF stays > 1.10, loosen the priors (e.g., variance 0.05 instead of 0.01) or increase FBITERATIONS.
2. **DSEM data structure**: data must be in *long format* with one row per person-occasion. Each person has many rows; `CLUSTER = id` defines person.
3. **Alignment with very few groups**: alignment was designed for many groups (≥ 10–15). With 2–3 groups, classical MGCFA is preferable.
4. **RI-CLPM degrees of freedom**: full RI-CLPM with all free parameters can become saturated with 3 waves; constrain residual variances or autoregressives equal across waves.
5. **ESEM doesn't accept regressions outside the rotation block**. To add covariates to factors identified by ESEM, run ESEM first, then specify ESEM-within-CFA with the rotated loadings as starts.
6. **IRT 2PL with Mplus output**: loadings reported are on the factor-loading metric. Convert to IRT a-parameter via `a = loading / sqrt(residual_variance)` or use STDY for already-rescaled output.

## Canonical examples in `assets/examples/`

- `ex5.13_latent_interaction.inp` — XWITH (for reference; latent interaction is also "special")
- `bsem_smallvariance_priors.inp` — BSEM with cross-loading priors
- `dsem_arpath_random.inp` — DSEM AR(1) with random autoregression
- `ri_lta_two_waves.inp` — RI-LTA template
- `esem_target_rotation.inp` — ESEM with target rotation
