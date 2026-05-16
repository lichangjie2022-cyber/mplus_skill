# Common Mplus errors and how to diagnose them

A catalog of frequent error messages, warnings, and "model ran but the estimates look weird" failures. Skim this when the user reports a problem; the symptom usually maps cleanly to one of these.

## Table of contents

1. [Parsing errors (won't even start)](#parsing)
2. [Identification errors](#identification)
3. [Convergence errors](#convergence)
4. [Output-quality warnings](#warnings)
5. [Missing-data surprises](#missing)
6. [Multilevel-specific problems](#multilevel)
7. [Mixture-specific problems](#mixture)
8. [Bayesian-specific problems](#bayesian)
9. [Categorical-data problems](#categorical)
10. [Output that looks wrong but isn't](#look-wrong)

---

## <a name="parsing"></a>1. Parsing errors

These appear at the top of the output and prevent the model from running.

| Error | Likely cause | Fix |
|---|---|---|
| `*** ERROR in <BLOCK> command: Unknown variable: XYZ` | Variable in MODEL/USEVARIABLES not in NAMES | Check spelling; remember case-insensitivity but exact-character match |
| `Unrecognized option` | Misspelled keyword (`USEVARIBLES`, `CATEGORIAL`) | Spell check |
| `Statement expected: ;` | Missing semicolon | Add `;` at end of every statement |
| `*** ERROR: Variable name XYZABCDEFG is longer than 8 characters` | Mplus truncates to 8 chars | Use shorter names |
| `*** ERROR: The following MODEL statements are ignored` | MODEL refers to undefined latent variable | Define the latent (`f BY ...`) before regressing on it |
| `The keyword USEOBSERVATIONS is not allowed with TYPE=MIXTURE` | Some keywords incompatible with model type | Use SUBPOPULATION or move filtering to DATA prep |
| `*** ERROR: NAMES = list does not match column count of data` | NAMES count ≠ columns in .dat | Count columns with `awk '{print NF; exit}' data.dat`; align NAMES |

---

## <a name="identification"></a>2. Identification errors

| Error | Likely cause | Fix |
|---|---|---|
| `THE MODEL ESTIMATION TERMINATED NORMALLY. WARNING: A NEGATIVE VARIANCE ESTIMATE FOR LATENT VARIABLE F1` | "Heywood case" — negative latent variance | Constrain `f1@0.0001` minimum, or rethink model; sometimes indicates measurement-level issue |
| `THE LATENT VARIABLE COVARIANCE MATRIX (PSI) IS NOT POSITIVE DEFINITE` | Latent correlations imply r > 1 or two factors are identical | Reduce factors / merge factors; check if scale of latent indicators is appropriate |
| `THE RESIDUAL COVARIANCE MATRIX (THETA) IS NOT POSITIVE DEFINITE` | Constraint forces negative residual variance | Free a residual or reconsider equality constraint |
| `Standard error could not be computed` | Model is empirically under-identified | Check df, reduce free parameters; try different starting values |
| `*** WARNING: PARAMETER IS FIXED AT 0 INSTEAD OF FREE` | Mplus auto-fixed a parameter at the boundary | Constrain manually if intentional; otherwise investigate why |
| Model has 0 degrees of freedom but "fits perfectly" | Saturated model | Not really an error; means the model can fit any data exactly. Try a constrained model. |

---

## <a name="convergence"></a>3. Convergence errors

| Error | Likely cause | Fix |
|---|---|---|
| `THE MODEL ESTIMATION DID NOT TERMINATE NORMALLY` | Algorithm couldn't find a maximum | Check starting values; try `STARTS = 500 50;` for mixture; rescale variables to similar magnitude |
| `THE OPTIMIZATION ALGORITHM DID NOT CONVERGE WITHIN N ITERATIONS` | Iterations too few | `ANALYSIS: ITERATIONS = 10000;` |
| `INSUFFICIENT INFORMATION TO ESTIMATE PARAMETERS` | Too many free parameters for sample size | Simplify model |
| Model converges but estimates near `*****` | Numerical overflow | Rescale variables (divide by 100, etc.) |
| `LL DIFFERENT ACROSS RANDOM STARTS` (mixture) | Local maxima | Increase STARTS to 1000 200; check best LL replicates ≥ 2× |
| `NO BEST FIT FOUND` (mixture) | Best LL appears only once | Increase STARTS; consider that the best LL may be a degenerate solution (one class with near-zero variance) |

---

## <a name="warnings"></a>4. Output-quality warnings

| Warning | Meaning | Action |
|---|---|---|
| `WARNING: THE BIVARIATE DISTRIBUTION OF VARIABLES X1 AND X2 IS SINGULAR.` | x1 and x2 are linearly dependent or nearly so | Drop one |
| `WARNING: STANDARD ERRORS COULD NOT BE COMPUTED. THE MODEL MAY NOT BE IDENTIFIED.` | Estimates returned but SEs not computed | Check identification, simplify model |
| `WARNING: ONE OR MORE PARAMETERS IS ON THE BOUNDARY OF THE PARAMETER SPACE` | Variance fixed at 0 by estimator | Inspect parameter; consider freeing |
| `WARNING: THERE MAY BE PROBLEMS WITH THE DATA FILE` | Mplus failed sanity check on data | Re-export data file; check for non-numeric values |
| `IT IS POSSIBLE THAT THE MODEL IS NOT IDENTIFIED` | df = 0 or numerical near-singularity | Confirm df with TECH1; reduce free parameters |
| `ICC = 0.000` for a clearly clustered variable | CLUSTER pointing wrong | Verify CLUSTER variable |

---

## <a name="missing"></a>5. Missing-data surprises

| Symptom | Cause | Fix |
|---|---|---|
| `Number of observations: 200` when file has 1000 rows | Listwise deletion (no FIML active) | Declare `MISSING = ALL (-99);` |
| Estimates wildly different from listwise version with FIML | x has missing observations but isn't an endogenous variable | Add `[x]; x;` in MODEL or use AUXILIARY |
| FIML "no missing data" message but you have missing data | MISSING code didn't match data | Verify code in file matches declaration |
| Bizarre means / variances | Missing code being read as real data | Same as above |
| `TYPE = IMPUTATION` reports half the expected N per dataset | Imputation files have different formats / column counts | Verify each imputed dataset has the same NAMES and column count |

---

## <a name="multilevel"></a>6. Multilevel-specific problems

| Symptom | Cause | Fix |
|---|---|---|
| `WITHIN variable does not vary within clusters` | Variable in WITHIN list has only between variation | Move to BETWEEN or to neither |
| `BETWEEN variable varies within clusters` | Variable in BETWEEN list has within-cluster variation | Move to WITHIN or to neither |
| ICC = 0 for all variables | CLUSTER variable wrong | Verify CLUSTER variable values |
| Random slope variance = 0 | Slope doesn't actually vary across clusters | Constrain `s@0;` for a fixed slope, simpler model |
| L2 sample size too small (N_clusters < 30) | Insufficient L2 information | Use BAYES; reduce L2 parameters |
| `THE NUMBER OF CLUSTERS IS LESS THAN OR EQUAL TO 1` | Cluster IDs all same or all different | Check data file |
| TWOLEVEL RANDOM model runs for hours | Categorical outcomes + integration | Switch to BAYES; or simplify |

---

## <a name="mixture"></a>7. Mixture-specific problems

| Symptom | Cause | Fix |
|---|---|---|
| Best LL appears only once (in TECH8 listing) | Local maximum, not a true global | Increase STARTS = 1000 200 |
| Different classes across runs with different seeds | Local maxima OR label switching | Inspect item profiles, not labels |
| One class has <5% of cases | Possibly a degenerate or outlier class | Try one fewer class; check if substantively meaningful |
| Entropy = 0.4 (very low) | Classes overlap heavily | Possibly too many classes; reduce K |
| LMR-LRT not printed | Some model configurations don't support it | Use BLRT (TECH14) |
| `INSUFFICIENT INFORMATION TO ESTIMATE THE CLASS-SPECIFIC PARAMETERS` | Class too small or model too complex | Reduce free parameters per class |
| GMM converges with one class having intercept variance = 0 | Effectively LCGA for that class | Constrain explicitly or accept |
| Standard errors enormous (>100 for log-odds) | Class is near-empty | Reduce K |

---

## <a name="bayesian"></a>8. Bayesian-specific problems

| Symptom | Cause | Fix |
|---|---|---|
| PSRF > 1.05 even after FBITERATIONS = 50000 | Slow mixing, possibly under-identified | Simplify model; check for identifying constraints |
| Posterior CI extremely wide | Diffuse prior + small N | Use weakly informative priors |
| `POTENTIAL SCALE REDUCTION COULD NOT BE COMPUTED` | Need ≥ 2 chains | Set `PROCESSORS = 2;` or higher |
| Convergence achieved but estimates "look weird" | Posterior is bimodal (mixture in disguise) | Plot histograms (`TYPE = PLOT2;`); consider model is multimodal |
| PPP exactly 0 or 1 | Model fits very badly or very well (suspicious) | Inspect; possibly model is misspecified or saturated |

---

## <a name="categorical"></a>9. Categorical-data problems

| Symptom | Cause | Fix |
|---|---|---|
| `*** ERROR: There are not enough categories with non-zero frequencies` | A category has 0 observations | Collapse categories; recode |
| Polychoric correlation could not be computed | Cells with 0 in cross-tab | Collapse low-frequency categories |
| WLSMV chi-square is much smaller than expected | Mean-adjusted chi-square always smaller | Report DIFFTEST for nested-model comparison |
| Difftest "deriv file" missing | First (larger) model didn't save derivatives | Add `SAVEDATA: DIFFTEST = deriv.dat;` to the larger model |
| WLSMV + missing data: only some rows used | WLSMV does pairwise-present, not FIML | Switch to BAYES or ML+INTEGRATION (slow) for full likelihood |
| Standardized loadings exceed 1.0 | Mplus reports standardized in the latent-response metric, not observed binary | Interpret cautiously; sometimes legitimate |
| Item probability profile looks identical across classes | Model is degenerate; classes don't differ on observables | Add covariates or reduce K |

---

## <a name="look-wrong"></a>10. Output that looks wrong but isn't

| Apparent issue | Actually | Diagnosis |
|---|---|---|
| Standardized loadings > 1 | Mplus standardizes in latent-response metric for categorical | Not an error; interpret with context |
| Coefficient for `c#k ON x` is huge negative | Multinomial logit; large coefficient = strong predictor of class membership | Convert to odds: exp(coef) |
| Mediation indirect = 0 but bootstrap CI excludes 0 | Bootstrap CI is on the point distribution, not the asymptotic test | Trust the CI |
| Different N reported for FIML vs listwise | FIML uses all rows with at least one observed variable | Expected behavior |
| Negative chi-square in DIFFTEST | Numerical issue near-equivalent models | Confirm models are properly nested; small negative often → no real difference |
| TECH3 covariance matrix has off-diagonals near 1 | Two parameters are nearly redundant | Possibly under-identified; check TECH1 for parameter redundancy |
| Two-level model: `y` variance is much smaller at BETWEEN than within | Normal — between-cluster variance is usually smaller | Check ICC ≈ var_between / (var_between + var_within) |

---

## Diagnostic workflow when something is off

1. **Read TECH1 first.** It shows the parameter spec matrix Mplus parsed. If your model in your head ≠ TECH1's matrix, the parser disagreed with you.
2. **Check sample size and missing data.** SAMPSTAT output reports the actual N used. If less than expected, find out why (listwise deletion, BETWEEN cluster size requirement, etc.).
3. **Check fit indices in light of model complexity.** RMSEA close to 0 with high df is good. RMSEA = 0.000 with df = 0 is meaningless — saturated.
4. **For mixture/multilevel, check the warnings in the log.** Mplus prints "WARNING:" liberally; these often pinpoint the issue.
5. **Compare to a simpler model.** If a complex model fails, fit a stripped-down version (drop covariates, reduce classes, etc.) and confirm it runs. Build up to find what breaks.
6. **Compare to a known-good example.** Pick a similar `.inp` from `assets/examples/` and confirm it runs on the user's data; then modify gradually.

## Reading the log for warnings

Mplus output has a "**INPUT READING TERMINATED NORMALLY**" line — past that, look for:
- `*** WARNING` lines (multiple are common; many are non-fatal but indicate model issues)
- "MODEL ESTIMATION TERMINATED NORMALLY" — needed for valid output
- The "MODEL FIT INFORMATION" section — chi-square, RMSEA, CFI, etc.
- "MODEL RESULTS" — parameter estimates
- "STANDARDIZED MODEL RESULTS" (if requested)

If "MODEL ESTIMATION TERMINATED NORMALLY" doesn't appear, treat all output as suspect.
