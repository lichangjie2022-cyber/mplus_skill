# Multilevel mixture (User's Guide Ch. 10)

Combines multilevel and mixture modeling: latent classes at level 1 (within), at level 2 (between), or both. The MODEL block nests `%WITHIN%`/`%BETWEEN%` with `%OVERALL%`/`%c#k%`. ANALYSIS uses `TYPE = TWOLEVEL MIXTURE` (or `... RANDOM` for random slopes).

## Decision tree

```
User wants classes at...
├─ Within level only (subgroups within each cluster)
│   → CLASSES = c(K); ANALYSIS: TYPE = TWOLEVEL MIXTURE;
│     %WITHIN% %OVERALL% / %WITHIN% %c#k%
│     %BETWEEN% %OVERALL% (no class blocks at L2)
├─ Between level only (classes of clusters; cluster is the unit)
│   → CLASSES = cb(K);  list cb in BETWEEN
│     %BETWEEN% %OVERALL% / %BETWEEN% %cb#k%
├─ Both levels (within-class and between-class)
│   → CLASSES = cw(Kw) cb(Kb);
└─ Multilevel growth mixture (cluster-level trajectory classes)
    → growth specification + CLASSES at the appropriate level + TYPE = TWOLEVEL MIXTURE [RANDOM]
```

## Skeletons

### Within-level classes (subgroups within cluster)

```
TITLE:    within-level latent class regression
DATA:     FILE = data.dat;
VARIABLE: NAMES = y x w clus;
          CLASSES = c(2);
          WITHIN = x;
          BETWEEN = w;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL MIXTURE;
          STARTS = 200 20;
MODEL:    %WITHIN%
          %OVERALL%
          y ON x;
          c ON x;
          %c#1%
          y ON x;          ! class-specific slope (or other class-specific parameters)
          y;
          %BETWEEN%
          %OVERALL%
          y ON w;
          c#1 ON w;        ! L2 prediction of within-class log-odds
OUTPUT:   TECH1 TECH8;
```

Key syntax features:
- `%WITHIN%` then `%OVERALL%` (in that order) — overall parameters at within level
- `%WITHIN%` then `%c#k%` — class-specific parameters at within level
- `%BETWEEN%` then `%OVERALL%` — overall parameters at between level
- The class variable `c` appears in `c ON x` at WITHIN (multinomial logit on L1 covariate) and `c#1 ON w` at BETWEEN (effect of L2 covariate on the log-odds of being in class 1)

### Between-level classes (cluster types)

```
VARIABLE: NAMES = y x w clus;
          CLASSES = cb(3);
          WITHIN = x;
          BETWEEN = cb w;       ! cb listed in BETWEEN
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL MIXTURE;
MODEL:    %WITHIN%
          %OVERALL%
          y ON x;
          %BETWEEN%
          %OVERALL%
          cb ON w;              ! L2 covariate predicts cluster class
          y ON w;
          %cb#1%
          [y];                  ! class-specific cluster-mean intercept
          %cb#2%
          [y];
          %cb#3%
          [y];
```

In a between-level mixture, classes are *clusters* — the latent class membership is at the cluster level, all members of a cluster share the class.

### Multilevel growth mixture (cluster trajectories)

```
VARIABLE: NAMES = y1-y4 x w clus;
          CLASSES = cb(2);
          WITHIN = x;
          BETWEEN = cb w;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL MIXTURE RANDOM;
          STARTS = 200 20;
          PROCESSORS = 4;
MODEL:    %WITHIN%
          %OVERALL%
          iw sw | y1@0 y2@1 y3@2 y4@3;
          y1-y4 (1);            ! equal residual variances
          iw sw ON x;
          %BETWEEN%
          %OVERALL%
          ib sb | y1@0 y2@1 y3@2 y4@3;
          y1-y4@0;
          ib sb ON w;
          cb ON w;
          %cb#1%
          [ib sb];              ! class-specific trajectory means
          %cb#2%
          [ib*2 sb*0.5];
```

### Multilevel LCA (latent class at level 1, factor structure at level 2)

```
VARIABLE: NAMES = u1-u6 x clus;
          CATEGORICAL = u1-u6;
          CLASSES = c(3);
          WITHIN = x;
          CLUSTER = clus;
ANALYSIS: TYPE = TWOLEVEL MIXTURE;
MODEL:    %WITHIN%
          %OVERALL%
          c ON x;
          %BETWEEN%
          %OVERALL%
          f BY c#1 c#2;          ! latent factor from L1 class log-odds
```

## ANALYSIS settings

```
ANALYSIS: TYPE = TWOLEVEL MIXTURE;
          TYPE = TWOLEVEL MIXTURE RANDOM;
          STARTS = 200 20;             ! reduce because multilevel mixture is slow
          STARTS = 0;                  ! disable starts when supplying explicit start values
          PROCESSORS = 4;
          ALGORITHM = INTEGRATION;     ! often required
          INTEGRATION = MONTECARLO(500);
```

Multilevel mixture is slow. Typical models take minutes to hours. To reduce runtime:
- Lower STARTS (200 20 instead of 500 50)
- Use INTEGRATION = MONTECARLO with a smaller number (e.g., 200)
- Reduce model complexity for initial enumeration; refine final K with full STARTS

## Pitfalls

1. **CLASSES variable scope.** A class variable at within level appears in `%WITHIN%`. A class variable for clusters (`cb`) must be listed in `BETWEEN = cb ...` for Mplus to know it's a between-level variable.
2. **Class enumeration at both levels simultaneously.** Don't try to choose Kw and Kb at once. Enumerate within-classes first holding clusters as random intercepts, then move to between classes.
3. **Estimation stability.** Multilevel mixture has even more local maxima than single-level mixture. Replication of the best LL across starts is critical; check the "Final stage loglikelihood values at local maxima" table.
4. **Cluster-class assignments.** Use `SAVEDATA: SAVE = CPROBABILITIES;` to inspect; for between-level classes, each cluster gets posterior probabilities.
5. **`c#1 ON w` is L2 → log-odds**, not a regression on `c#1` as a count. Effects are multinomial-logistic and reported on the logit scale.
6. **Mixing categorical L1 outcomes + INTEGRATION + multilevel.** This is the slowest combination in Mplus. Consider Bayesian estimation (`ESTIMATOR = BAYES`) — often faster than ML+INTEGRATION for these models.

## Canonical examples in `assets/examples/`

- `ex10.1_two_level_mixture.inp` — basic two-level mixture
- `ex10.8_multilevel_mixture_growth.inp` — multilevel growth mixture with random slopes
