# Data preparation for Mplus

Mplus reads only plain-text data files. Almost every "Mplus won't run my analysis" question turns out to be a data-formatting problem. This reference covers what the file should look like, how to declare it in `DATA:` and `VARIABLE:`, and how to handle the common conversions (CSV, SPSS, R, Stata).

## Acceptable file formats

| Format | Use | Declaration |
|---|---|---|
| Space- or tab-delimited, no header | Default | `DATA: FILE = mydata.dat;` |
| Comma-delimited | Common from R/Python | `DATA: FILE = mydata.csv; TYPE = INDIVIDUAL;` (Mplus auto-detects commas in modern versions; if not, pre-strip commas) |
| Free format (whitespace separates fields) | Default and most robust | `DATA: FILE = mydata.dat;` (no extra declaration needed) |
| Fixed format | Legacy | `DATA: FILE = mydata.dat; FORMAT = 6F8.2;` (rare) |
| Multiple files (multiple imputation) | Pooling | `DATA: FILE = implist.dat; TYPE = IMPUTATION;` |
| Multiple files (Monte Carlo external) | Simulation | `DATA: FILE = mclist.dat; TYPE = MONTECARLO;` |

**Rules that bite people:**
- No header row. The first row must be data. Use `VARIABLE: NAMES = ...` to assign names.
- No string variables. Recode categorical variables (e.g., gender "M"/"F") to numeric (1/2) before saving.
- Missing values: use a numeric code (`-99`, `999`, `9999`) or a single dot `.` for each cell. Empty cells / blanks are not valid in free format — they shift column alignment.
- Variable values must be space/comma-separated within a row. Tabs are usually fine but mixing tabs and spaces causes alignment errors.
- One row per observation (TYPE = INDIVIDUAL — the default). Summary-statistic input (TYPE = MEANS, TYPE = COVARIANCE) is rare; ignore unless the user explicitly has only summary stats.

## Recommended export workflow

**From R / tidyverse:**
```r
# Replace strings, recode factors as numeric integers
df_clean <- df %>%
  mutate(gender = as.integer(gender),
         across(everything(), ~ifelse(is.na(.), -99, .)))
write.table(df_clean, "mydata.dat",
            sep = " ", row.names = FALSE, col.names = FALSE,
            quote = FALSE, na = "-99")
```

Or use the `MplusAutomation` package: `prepareMplusData(df, "mydata.dat")` writes the data file *and* prints a ready-to-paste `NAMES =` line.

**From Python / pandas:**
```python
df_clean = df.fillna(-99)
df_clean.to_csv("mydata.dat", sep=" ", header=False, index=False)
```

**From SPSS / SAS / Stata:** Export to tab- or space-delimited text without a header.

## DATA block syntax

```
DATA:  FILE = mydata.dat;            ! relative paths resolved against the .inp directory
DATA:  FILE = "C:/Projects/Study1/mydata.dat";  ! absolute path; use forward slashes on Windows
DATA:  FILE IS mydata.dat;           ! IS is interchangeable with =
DATA:  FILE = mydata.dat;
       TYPE = INDIVIDUAL;            ! default; one row per observation
       NOBSERVATIONS = 500;          ! only required for some legacy formats
```

For multiple imputation analysis:
```
DATA:  FILE = imp_list.dat;          ! a text file whose contents are filenames of imputed datasets
       TYPE = IMPUTATION;
```

`imp_list.dat` is just:
```
imp1.dat
imp2.dat
imp3.dat
...
```

## VARIABLE block — declaring data structure

The single most error-prone block. Get it right and most other things fall into place.

```
VARIABLE:
  NAMES = id age gender y1-y6 x1-x4 clus;     ! every column in mydata.dat, in order
  USEVARIABLES = age y1-y6 x1-x4;             ! what enters the analysis
  IDVARIABLE = id;                            ! used when saving fscores / cprobs
  MISSING = ALL (-99);                        ! single code for all variables
  MISSING = y1-y6 (-99) x1-x4 (-1);           ! variable-specific codes
  CATEGORICAL = u1-u6;                        ! ordered-categorical outcomes
  NOMINAL = race;                             ! unordered multi-category outcomes
  COUNT = visits;                             ! Poisson count outcomes
  COUNT = visits (i);                         ! zero-inflated Poisson
  CENSORED = income (a);                      ! censored from above (top-coded)
  GROUPING = gender (1=male 2=female);        ! multiple-group analysis
  CLUSTER = clus;                             ! multilevel nesting
  WITHIN = y1-y6;                             ! level-1-only variables
  BETWEEN = w1 w2;                            ! level-2-only variables
  WEIGHT = wt;                                ! sampling weight
  STRATIFICATION = strat;                     ! survey design strata
  SUBPOPULATION = (subgroup EQ 1);            ! analyze a subset, keep design info
  AUXILIARY = (m) z1 z2;                      ! keep z1, z2 as MAR correlates only
  AUXILIARY = (e) g1 g2;                      ! same-equation aux for FIML (Graham 2003)
  CLASSES = c(2);                             ! latent class variable, 2 classes
  KNOWNCLASS = cg (gender=1 gender=2);        ! observed grouping as a class variable
```

### Missing data codes

- Default missing code: `.` (single dot per cell). If your file uses dots, no `MISSING` declaration needed.
- For numeric codes, declare:
  - `MISSING = ALL (-99);` — same code for all variables
  - `MISSING = y1-y6 (-99) x (-1);` — per-variable codes
  - `MISSING = ALL (-99 -88);` — multiple codes (treated identically)
- Important: blank / empty cells in free format are **shifts**, not missing. Always replace with a code before saving.

### Categorical, ordinal, and count outcomes

| Outcome type | Declaration | Estimator default | Notes |
|---|---|---|---|
| Continuous (Likert 5–7+ pt often) | none | ML | If skewed: MLR for robust SE |
| Binary | `CATEGORICAL = u;` | WLSMV | Or ML with LINK=LOGIT/PROBIT |
| Ordinal (3–5 categories) | `CATEGORICAL = u1-u4;` | WLSMV | Threshold model |
| Nominal (≥3 unordered) | `NOMINAL = u;` | ML (multinomial logit) | Cannot use WLSMV |
| Count (Poisson) | `COUNT = u;` | ML | Need ALGORITHM=INTEGRATION |
| Zero-inflated count | `COUNT = u (i);` | ML | (i) flags inflation |
| Censored (top-coded income) | `CENSORED = y (a);` | ML | (b) = bottom, (a) = top, (bi)/(ai) = inflated |
| Time-to-event (survival) | `SURVIVAL = t;` + `TIMECENSORED = tc(0=NOT 1=RIGHT);` | ML or specialized | See growth-survival.md |

If you declare a variable on multiple of these lists, Mplus errors. Each variable gets one classification.

### Variables you analyze vs. variables you keep

`USEVARIABLES` is the subset that enters MODEL. Any NAMES not in USEVARIABLES are **invisible** to the model — they cannot appear in MODEL statements. This matters for FIML:

- If `z` is a strong correlate of missingness on `y` but isn't in your model, FIML cannot use it.
- To keep `z` for MAR purposes only: `AUXILIARY = (m) z;` — Mplus adds saturated covariances with all USEVARIABLES, improving missing-data plausibility without changing the model.
- `AUXILIARY = (e) z;` adds `z` to the model's mean and variance estimation (Graham 2003 "extra dependent" approach).

### CLUSTER and WITHIN / BETWEEN allocation

For multilevel analysis (TYPE = TWOLEVEL):
- `CLUSTER = clus;` names the level-2 ID.
- `WITHIN = ...;` lists variables that vary **only** within clusters (level-1 covariates, time-varying predictors).
- `BETWEEN = ...;` lists variables that are constant within a cluster (level-2 attributes, group means).
- Variables that belong on both levels (a continuous L1 variable you also want to model as a L2 mean) are listed in **neither**, and Mplus automatically decomposes into within and between parts.

Common error: putting `clus` in WITHIN or BETWEEN. The cluster variable goes only in `CLUSTER = ...;` and never in WITHIN/BETWEEN.

### Complex survey design

```
VARIABLE:
  WEIGHT = wt;
  STRATIFICATION = strat;
  CLUSTER = psu;                ! Or use TYPE=COMPLEX (single level), TYPE=COMPLEX TWOLEVEL
ANALYSIS:
  TYPE = COMPLEX;               ! standard errors adjusted for design
```

`TYPE = COMPLEX` adjusts standard errors only (Taylor linearization). `TYPE = COMPLEX TWOLEVEL` does both design adjustment and explicit multilevel.

## Format / dimension checks before submitting

Before running Mplus on a new dataset, verify:

1. **Row × column count.** `wc -l mydata.dat` should equal N. `awk '{print NF}' mydata.dat | sort -u` should print a single number = number of variables. Different row lengths = misaligned data = silent corruption.
2. **NAMES count = column count.** Easy mistake: NAMES list 12 vars but the data file has 11. Mplus reads in row-order; misalignment shifts everything.
3. **Missing codes match.** Open the file; confirm `-99` (or whatever you declared) is what you actually see for missing cells. A common bug: R wrote `NA` literal strings → Mplus reads them as 0 (silently).
4. **No string variables.** `head mydata.dat`. Any quoted strings or letters = will fail.
5. **Path is reachable.** Mplus runs from the .inp's directory. Use a relative path if data and inp are in the same folder; absolute path with forward slashes otherwise (`C:/Studies/...`).

## Quick sanity check — TYPE = BASIC

To inspect data before fitting any model:

```
TITLE:    sanity check
DATA:     FILE = mydata.dat;
VARIABLE: NAMES = y1-y6 x1-x3 clus;
          MISSING = ALL (-99);
          USEVARIABLES = y1-y6 x1-x3;
          CLUSTER = clus;
ANALYSIS: TYPE = BASIC;
OUTPUT:   SAMPSTAT;
```

`TYPE = BASIC` reports sample means, SDs, correlations, missing-data patterns, ICCs (for TYPE = BASIC TWOLEVEL). Run this first when you encounter a new dataset.

## Multiple imputation: producing the inputs Mplus expects

To use TYPE = IMPUTATION analysis later, the imputation step must save in the right format. Two paths:

**Path A — generate imputations in Mplus itself (`DATA IMPUTATION` block):**
```
DATA:     FILE = raw.dat;
VARIABLE: NAMES = y1-y4 x1-x3;
          USEVARIABLES = y1-y4 x1-x3;
          MISSING = ALL (-99);
DATA IMPUTATION:
  IMPUTE = y1-y4 x1 (c);          ! (c) flags categorical
  NDATASETS = 20;
  SAVE = myimp*.dat;              ! saves myimp1.dat ... myimp20.dat + myimplist.dat
ANALYSIS: TYPE = BASIC;
```

Then analyze:
```
DATA:     FILE = myimplist.dat;
          TYPE = IMPUTATION;
VARIABLE: NAMES = y1-y4 x1-x3;
ANALYSIS: ESTIMATOR = ML;
MODEL:    y1 ON x1-x3;
          ...
```

**Path B — import datasets imputed elsewhere (R mice, SAS MI, Stata mi).** Save each imputed dataset to `imp1.dat`, `imp2.dat`, ... and create a text file `mylist.dat` listing them one per line. Then `DATA: FILE = mylist.dat; TYPE = IMPUTATION;`.

See `references/missing-bayesian.md` for the analysis-side details.

## Common data-prep mistakes

| Symptom | Cause | Fix |
|---|---|---|
| "Number of variables does not match the number of NAMES" | NAMES list miscount | `awk '{print NF; exit}' mydata.dat` to count columns; align with NAMES |
| Estimates wildly off, all variables look like means of 0–9 | File has commas but you didn't say so | Either convert to space-delimited or check version supports CSV |
| "Number of observations: 0" | Wrong path, file unreadable | Use absolute path; check working directory matches .inp location |
| All variances huge | Missing-data code being treated as real data | Add `MISSING = ALL (-99);` (or whatever your code is) |
| FIML "no missing data" but you have missing data | Code was wrong, all "missing" entries read as numeric | Verify MISSING code matches what's in the file |
| Multilevel ICC = 0 for everything | CLUSTER points to wrong variable, or cluster IDs are not contiguous (Mplus is fine with non-contiguous but typo on column name kills it) | Check CLUSTER = matches a variable in NAMES |
| Multiple-group model has only one group's results | GROUPING values don't match the file (e.g., file has 0/1 but you wrote `g (1=male 2=female)`) | Match the actual codes |

## Reference example to copy

`assets/examples/ex3.1_regression.inp` — simplest possible Mplus file: TITLE, DATA, VARIABLE, MODEL. Use this as the starting frame for any new analysis.
