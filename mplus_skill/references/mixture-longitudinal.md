# Longitudinal mixture: GMM, LCGA, LTA (User's Guide Ch. 8)

Mixture models applied to repeated measures. Three core variants:

- **LCGA** (Latent Class Growth Analysis): classes differ in trajectory means; trajectory variances fixed at 0 within class (homogeneous trajectories per class).
- **GMM** (Growth Mixture Model): classes differ in trajectory means *and* trajectory variances (heterogeneous trajectories per class).
- **LTA** (Latent Transition Analysis): repeated cross-sectional latent class measurements connected by transition probabilities.

## Decision tree

```
User has repeated measures and wants to find...
├─ Distinct trajectory shapes, treat people within trajectory as identical
│   → LCGA  (growth factor variances fixed at 0 per class)
├─ Distinct trajectory shapes, allow within-class individual differences
│   → GMM  (growth factor variances free per class)
├─ Repeated latent-class measurements, want transition probabilities
│   → LTA  (CLASSES = c1(K) c2(K) ...)
├─ LTA + covariate predicting transitions
│   → LTA + c2 ON c1 + c2 ON x
├─ LTA + covariate predicting baseline class only
│   → c1 ON x
├─ Two parallel growth processes, each with classes
│   → Sequential / parallel GMM (CLASSES = c1(K) c2(K))
└─ Random-intercept LTA (control for stable between-person differences)
    → RI-LTA → see special-features.md
```

## Skeletons

### LCGA (latent class growth analysis)

```
TITLE:    LCGA, 3 trajectory classes
DATA:     FILE = data.dat;
VARIABLE: NAMES = y1-y4;
          CLASSES = c(3);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
MODEL:    %OVERALL%
          i s | y1@0 y2@1 y3@2 y4@3;
          i@0 s@0;                ! growth factor variances fixed at 0 (LCGA defining feature)
          %c#1%
          [i*0 s*0];
          %c#2%
          [i*1 s*0.5];
          %c#3%
          [i*2 s*1];
OUTPUT:   TECH11 TECH14;
PLOT:     TYPE = PLOT3;
          SERIES = y1-y4(s);
```

The `i@0 s@0` inside `%OVERALL%` is the LCGA signature — each class has a deterministic trajectory mean. Class-specific intercepts (`[i*…]`) and slopes (`[s*…]`) are typically given starting values to encourage stable convergence.

### GMM (growth mixture model)

```
VARIABLE: NAMES = y1-y4 x;
          CLASSES = c(2);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
MODEL:    %OVERALL%
          i s | y1@0 y2@1 y3@2 y4@3;
          i s ON x;
          c ON x;
          %c#1%
          [i*1 s*0.5];
          %c#2%
          [i*3 s*1];
OUTPUT:   TECH11 TECH14;
PLOT:     TYPE = PLOT3;
          SERIES = y1-y4(s);
```

The growth factor variances `i`, `s` are free by default (the GMM defining feature). To constrain variances equal across classes, omit class-specific variance statements (default is equal across classes).

To free variances per class:
```
          %c#1%
          [i*1 s*0.5];
          i s;
          %c#2%
          [i*3 s*1];
          i s;
```

### LTA (two time points, three classes per wave)

```
TITLE:    LTA, two time points, 3 classes
DATA:     FILE = data.dat;
VARIABLE: NAMES = u11-u15 u21-u25;
          CATEGORICAL = u11-u15 u21-u25;
          CLASSES = c1(3) c2(3);
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;
MODEL:    %OVERALL%
          c2 ON c1;                       ! transition probabilities
MODEL c1:                                 ! measurement model at time 1
          %c1#1%
          [u11$1-u15$1] (1-5);
          %c1#2%
          [u11$1-u15$1] (6-10);
          %c1#3%
          [u11$1-u15$1] (11-15);
MODEL c2:                                 ! measurement model at time 2; same labels enforce
          %c2#1%                          ! measurement invariance across waves
          [u21$1-u25$1] (1-5);
          %c2#2%
          [u21$1-u25$1] (6-10);
          %c2#3%
          [u21$1-u25$1] (11-15);
OUTPUT:   TECH1 TECH8 TECH15;
```

`TECH15` prints the latent-class transition probability matrix (and marginal class probs). Labeled equality constraints `(1-5)` across the two MODEL c1 / MODEL c2 blocks enforce **measurement invariance** of the latent classes across time — required for transition probabilities to be interpretable.

### LTA with covariate

`ex8.13` pattern (covariate influences transition):
```
VARIABLE: NAMES = u11-u15 u21-u25 g;
          CATEGORICAL = u11-u15 u21-u25;
          CLASSES = cg(2) c1(3) c2(3);
          KNOWNCLASS = cg (g=0 g=1);
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          c1 c2 ON cg;                      ! baseline and post both depend on cg
MODEL cg: %cg#1%
          c2 ON c1;
          %cg#2%
          c2 ON c1;                         ! allow transitions to differ by cg
MODEL c1: ...                                ! same measurement model labels as before
MODEL c2: ...
```

### Parallel-process GMM (two outcomes, each with trajectory classes)

```
VARIABLE: NAMES = y1-y4 z1-z4;
          CLASSES = c1(2) c2(2);
ANALYSIS: TYPE = MIXTURE;
MODEL:    %OVERALL%
          i1 s1 | y1@0 y2@1 y3@2 y4@3;
          i2 s2 | z1@0 z2@1 z3@2 z4@3;
          c2 ON c1;
MODEL c1:
          %c1#1% [i1 s1];
          %c1#2% [i1*1 s1*0.5];
MODEL c2:
          %c2#1% [i2 s2];
          %c2#2% [i2*1 s2*0.5];
```

### Class enumeration with growth mixture

Same workflow as cross-sectional LCA: fit K = 1, 2, 3, ... record BIC, ABIC, entropy, LMR-LRT, BLRT. Especially with GMM, beware:
- Solutions where classes differ only in variances (rather than trajectory shape) — often spurious.
- "Single trajectory" classes that capture <5% of sample with extreme means — outliers, not classes.

## ANALYSIS settings

```
ANALYSIS: TYPE = MIXTURE;
          STARTS = 500 50;            ! GMM/LTA often need this many; up to 1000 200
          STITERATIONS = 20;
          STSEED = 12345;             ! reproducibility for class enumeration
          PROCESSORS = 4;
          STARTS = 0;                 ! disable random starts when manually setting all start values
                                      ! (common in published LTA replication scripts)
```

## Pitfalls

1. **LCGA vs GMM confusion.** Forgetting `i@0 s@0` in LCGA makes it a GMM — fits better but is a different model. Conversely, freeing variances within `%c#k%` blocks turns LCGA into class-specific GMM.
2. **Class enumeration with growth.** Adding classes always improves fit indices. Substantive interpretation matters more than information criteria alone. Plot trajectories — if two "classes" have parallel trajectories, they likely shouldn't be separate.
3. **LTA measurement invariance is a precondition.** Without invariance constraints across waves, latent classes at different times measure different constructs — transition probabilities meaningless. Always constrain thresholds (`(1-5)`, etc.) across waves first; relax for partial invariance only with justification.
4. **`MODEL c1: %c1#k%` vs `MODEL c2: %c2#k%`.** The class label must match the latent class variable. Mixing them (`MODEL c2: %c1#1%`) is a common error → Mplus rejects the syntax.
5. **Random starts and replication.** GMM and LTA often have many local maxima. If the best LL doesn't replicate (`STARTS = 500 50` and Mplus reports the top LL only once), increase to `STARTS = 1000 200`.
6. **Posterior probabilities (CPROBABILITIES) save.** Use `SAVEDATA: SAVE = CPROBABILITIES;` to save modal class assignments plus posteriors. For LTA, modal class assignments at each wave are saved separately.
7. **`c2 ON c1` is multinomial logistic.** Reported as `C2#1 ON C1#1`, `C2#1 ON C1#2`, etc. with the last class as reference at each level. The transition matrix in TECH15 is more directly interpretable.
8. **LTA with covariate on transitions** requires `MODEL c1:` and `MODEL c2:` constraints to keep measurement invariance. The covariate's effect appears in `c2 ON c1 covariate` patterns — see ex8.13 for the canonical setup.
9. **GMM with linear time scores and small T.** With T=3, only LCGA (no within-class variation) is sometimes identifiable; GMM may need fixed slope variances. Check with `ANALYSIS: OUTPUT = TECH1;` to confirm.

## Canonical examples in `assets/examples/`

- `ex8.1_gmm.inp` — basic GMM with covariates
- `ex8.13_lta.inp` — LTA with covariate, KNOWNCLASS, measurement-invariance labels
