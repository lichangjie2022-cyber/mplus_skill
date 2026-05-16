# Latent class and latent profile analysis (User's Guide Ch. 7)

Cross-sectional mixture models for discovering unobserved subgroups. LCA uses categorical indicators (binary, ordinal); LPA uses continuous indicators. Factor mixture combines a latent factor with class structure. This reference also covers covariates and distal outcomes via the 3-step and BCH approaches.

## Decision tree

```
User wants to identify subgroups based on...
├─ Binary or ordinal items → LCA  (CATEGORICAL = u1-uK)
├─ Continuous items → LPA  (no CATEGORICAL)
├─ Mixed item types → use CATEGORICAL for the ordinal/binary; LPA-style for continuous
├─ Items + a continuous latent dimension underlying them → factor mixture
├─ Subgroups + want to predict class from covariates → c ON x (LCA-with-covariate, ex7.4)
├─ Subgroups + want to predict outcomes from class → distal outcomes (BCH or manual 3-step)
└─ Already know class composition (observed grouping) → KNOWNCLASS, then test invariance
```

## Skeletons

### LCA, binary indicators (foundational pattern)

```
TITLE:    LCA, six binary items, two classes
DATA:     FILE = data.dat;
VARIABLE: NAMES = u1-u6;
          CATEGORICAL = u1-u6;
          CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;          ! 500 random starts, refine best 50
          STITERATIONS = 20;
MODEL:    %OVERALL%                  ! invariant parameters (priors on c)
OUTPUT:   TECH1 TECH8 TECH11 TECH14;
```

By default, item thresholds vary freely across classes (the class-defining parameters). `%OVERALL%` holds the class probabilities (priors).

### LPA, continuous indicators

```
TITLE:    LPA, four continuous items, three profiles
VARIABLE: NAMES = y1-y4;
          CLASSES = c(3);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
MODEL:    %OVERALL%
OUTPUT:   TECH11;
```

By default, item means vary across classes; item variances are equal across classes (a strong assumption). To free variances per class (LPA "Class-varying variances" model):

```
MODEL:    %OVERALL%
          %c#1%
          y1-y4;            ! free variances in class 1
          %c#2%
          y1-y4;
          %c#3%
          y1-y4;
```

Class-varying variances often fit better but at risk of degenerate solutions (variance near 0).

### LCA with covariate predicting class membership

```
VARIABLE: NAMES = u1-u6 x;
          CATEGORICAL = u1-u6;
          CLASSES = c(3);
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          c ON x;           ! multinomial logit of class on covariate
OUTPUT:   TECH1;
```

`c ON x;` is a multinomial logistic regression with the last class as reference. Reported as `C#1 ON X`, `C#2 ON X` (last class is reference).

### LCA with direct effect of covariate on item (DIF check)

```
MODEL:    %OVERALL%
          c ON x;
          u1 ON x;          ! direct effect → tests DIF on u1 by x
```

If `u1 ON x` is significant and large, x affects item u1 directly (above class) — measurement non-invariance.

### Mixture regression (one continuous outcome, class-varying regression)

```
VARIABLE: NAMES = y x1 x2;
          CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          y ON x1 x2;
          c ON x1;          ! class also predicted by x1
          %c#2%
          y ON x2;          ! in class 2, y's regression on x2 differs
          y;                ! residual variance can also vary
```

This is `ex7.1` — a foundational mixture pattern.

### Factor mixture (CFA + LCA)

```
VARIABLE: NAMES = u1-u8;
          CATEGORICAL = u1-u8;
          CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE;
          ALGORITHM = INTEGRATION;
          STARTS = 100 10;
MODEL:    %OVERALL%
          f BY u1-u8;
          [f@0]; f@1;       ! standard factor identification within mixture
          %c#1%
          [f];              ! free class-specific factor mean
          %c#2%
          [f];
```

Factor loadings are typically held equal across classes (default `%OVERALL%`); factor means and thresholds may differ.

### Distal outcomes — BCH method (recommended)

```
VARIABLE: NAMES = u1-u4 y x;
          CATEGORICAL = u1-u4;
          CLASSES = c(3);
          AUXILIARY = y(BCH) x;
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          c ON x;
```

BCH adjusts for classification uncertainty when estimating means of `y` per class. Alternative methods:
- `DCAT` — for categorical distal outcomes
- `DCON` / `DU3STEP` — older 3-step approaches
- Manual 3-step (estimate model, save cprobs, run logistic regression on cprobs) — see Asparouhov & Muthén 2014

### LCA with known group (multi-group LCA / measurement invariance of classes)

```
VARIABLE: NAMES = u1-u6 g;
          CATEGORICAL = u1-u6;
          CLASSES = cg(2) c(3);              ! known group cg, latent class c
          KNOWNCLASS = cg (g=0 g=1);
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          c ON cg;                            ! does class membership differ by group?
MODEL cg:                                     ! item thresholds per known group
          %cg#1%
          [u1$1-u6$1];
          %cg#2%
          [u1$1-u6$1];
```

For measurement invariance of an LCA across groups, additionally constrain `MODEL c:` thresholds across `cg` strata to equality.

## Class enumeration workflow

Mplus does not select K for you. Fit K = 1, 2, 3, ... and compare:

| Metric | Lower / higher = better? | Notes |
|---|---|---|
| Log-likelihood | higher | not penalized for parameters |
| AIC | lower | weak penalty |
| BIC | lower | preferred information criterion |
| ABIC (sample-size adjusted BIC) | lower | helpful when N small |
| Entropy | higher (closer to 1) | classification certainty (not a fit index) |
| LMR-LRT (`TECH11`) | p < .05 favors K vs K-1 | quick but approximate |
| BLRT (`TECH14`) | p < .05 favors K vs K-1 | gold standard, slow |

Workflow per K:
```
VARIABLE: CLASSES = c(K);
ANALYSIS: TYPE = MIXTURE; STARTS = 500 50;
OUTPUT:   TECH11 TECH14;
```

Record BIC, ABIC, entropy, smallest class size, LMR-LRT p, BLRT p. Pick K based on:
1. Substantive interpretability (most important).
2. Information criteria — look for elbow in BIC.
3. LMR/BLRT — last K where p < .05.
4. Class size — no class < 5% is a common heuristic.
5. Replication — do classes look similar across random seeds? Try different STARTS.

## ANALYSIS settings

```
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;            ! defaults: 20 8. 500 50 is safer for K > 2.
          STITERATIONS = 20;          ! EM iters per start; increase if local maxima
          STSEED = 12345;             ! reproducibility
          ALGORITHM = INTEGRATION;    ! required if factor mixture / latent on observed in classes
          INTEGRATION = MONTECARLO(500);   ! reduces cost vs. GAUSSHERMITE
          PROCESSORS = 4;             ! parallelize starts
```

If LCA replication fails (different LL across runs), increase STARTS to 1000 200 or higher.

## OUTPUT to interpret

```
OUTPUT:   TECH1 TECH8 TECH11 TECH14 STDYX;
```

- `TECH11` — LMR-LRT (rapid K vs K-1 test)
- `TECH14` — BLRT (definitive K vs K-1 test; slow because bootstraps the LL)
- `TECH8` — iteration log
- `TECH1` — parameter spec matrix (verify your model is what Mplus parses)
- `STDYX` — standardized regressions (for `c ON x`)

For class profiles, the output reports:
- Item-probability profile (probability of each response category per class) — interpretable for LCA
- Item-mean profile (per class) — for LPA
- Posterior probabilities (per case, per class) — saved with `SAVEDATA: SAVE = CPROBABILITIES;`

## Saving class assignments

```
SAVEDATA: FILE = lca_out.dat;
          SAVE = CPROBABILITIES;     ! adds posterior probs and modal class to file
          IDVARIABLE = id;
```

## Pitfalls

1. **Local maxima.** Mixture likelihood is non-convex. Always check:
   - Best LL replicated across random starts (Mplus prints "Final stage loglikelihood values at local maxima, seeds, and initial stage start numbers" — top values should repeat).
   - If not, increase `STARTS = 1000 200;`.
2. **Class label switching.** Across runs with different seeds, "class 1" may correspond to different substantive groups. Inspect item profiles, not class numbers.
3. **Forgetting CATEGORICAL.** LCA on binary items without `CATEGORICAL = u1-uK;` becomes LPA on 0/1 data — wrong model, but Mplus runs it silently.
4. **Adding too many classes.** Common to stop adding when LMR/BLRT p > .05 OR a class is < 5%. Substantive replication across samples is the gold standard.
5. **BCH vs older methods.** Use BCH for distal outcomes. The earlier "Vermunt 3-step" (DU3STEP) can bias estimates if entropy is low. BCH is more robust.
6. **Factor mixture identification.** Both class means *and* factor means free per class is under-identified; constrain factor variance equal across classes or fix one class's factor mean to 0.
7. **Covariate in `%c#k%`.** Covariates can vary across classes (`y ON x` inside `%c#1%`), but multinomial logit `c ON x` lives in `%OVERALL%` only.
8. **STARTS = 0 disables random starts** — only use when supplying explicit starting values manually (common in published replication code).

## Canonical examples in `assets/examples/`

- `ex7.1_mixture_regression.inp` — mixture regression with `c ON x` and class-specific slope
- `ex7.4_lca_covariate.inp` — LCA with covariate predicting class
- `ex7.9_lpa_continuous.inp` — LPA, continuous indicators
- `ex7.27_factor_mixture.inp` — factor mixture (CFA + LCA with INTEGRATION)
