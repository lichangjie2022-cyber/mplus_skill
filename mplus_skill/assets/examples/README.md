# Bundled `.inp` templates — index

Canonical Mplus syntax samples drawn from the official User's Guide examples (Muthén & Muthén) and select special-topic releases. Each is a complete, runnable `.inp` (paired with its `.dat` file in the original library — here only the syntax is bundled).

Use these as starting frames, not as drop-in solutions. The variable names (`y1-y6`, `x`, `clus`, `u11-u15`, etc.) are placeholders that need to be replaced with the user's actual variable names.

## Where each template comes from

| File | User's Guide source | Topic |
|---|---|---|
| `ex3.1_regression.inp` | Ch. 3 ex 3.1 | Minimal linear regression |
| `ex3.11_path.inp` | Ch. 3 ex 3.11 | Path analysis with multiple equations |
| `ex3.16_path_bootstrap.inp` | Ch. 3 ex 3.16 | Path analysis with bootstrap indirect effects |
| `ex4.1_efa_continuous.inp` | Ch. 4 ex 4.1 part 1 | EFA, continuous indicators, GEOMIN rotation |
| `ex4.7_efa_bifactor.inp` | Ch. 4 ex 4.7 | Bifactor EFA with BI-GEOMIN rotation |
| `ex5.1_cfa_basic.inp` | Ch. 5 ex 5.1 | Two-factor CFA, continuous indicators |
| `ex5.2_cfa_categorical.inp` | Ch. 5 ex 5.2 | CFA with categorical indicators (WLSMV) |
| `ex5.11_sem.inp` | Ch. 5 ex 5.11 | SEM with latent-on-latent regressions |
| `ex5.13_latent_interaction.inp` | Ch. 5 ex 5.13 | Latent moderation via XWITH |
| `ex5.14_mgcfa_mimic.inp` | Ch. 5 ex 5.14 | Multiple-group CFA with covariates (MIMIC) |
| `ex6.1_lgm_linear.inp` | Ch. 6 ex 6.1 | Linear latent growth, 4 waves |
| `ex6.10_lgm_covariates.inp` | Ch. 6 ex 6.10 | LGM with time-invariant and time-varying covariates |
| `ex6.14_multi_indicator_lgm.inp` | Ch. 6 ex 6.14 | Multiple-indicator LGM with measurement invariance |
| `ex6.20_survival_cox.inp` | Ch. 6 ex 6.20 | Continuous-time survival (Cox-style) |
| `ex7.1_mixture_regression.inp` | Ch. 7 ex 7.1 | Mixture regression with class-varying slope |
| `ex7.4_lca_covariate.inp` | Ch. 7 ex 7.4 | LCA with covariate predicting class |
| `ex7.9_lpa_continuous.inp` | Ch. 7 ex 7.9 | Latent profile analysis (continuous indicators) |
| `ex7.27_factor_mixture.inp` | Ch. 7 ex 7.27 | Factor mixture (CFA + LCA, INTEGRATION) |
| `ex8.1_gmm.inp` | Ch. 8 ex 8.1 | Growth mixture model |
| `ex8.13_lta.inp` | Ch. 8 ex 8.13 part 1 | LTA with covariate, KNOWNCLASS |
| `ex9.1a_twolevel_regression.inp` | Ch. 9 ex 9.1a | Two-level random-intercept regression |
| `ex9.6_twolevel_cfa.inp` | Ch. 9 ex 9.6 | Two-level CFA |
| `ex10.1_two_level_mixture.inp` | Ch. 10 ex 10.1 | Two-level mixture |
| `ex10.8_multilevel_mixture_growth.inp` | Ch. 10 ex 10.8 | Multilevel growth mixture with random slopes |
| `ex11.6_multiple_imputation_growth.inp` | Ch. 11 ex 11.6 | Multiple imputation + growth |
| `ex11.7_bayesian_multi_indicator_growth.inp` | Ch. 11 ex 11.7 | Bayesian estimation + MI + invariant multi-indicator growth |
| `ex12.1_mc_cfa_mimic.inp` | Ch. 12 ex 12.1 | Monte Carlo: MIMIC power analysis with missing patterns |
| `ex12.4_mc_multilevel_growth.inp` | Ch. 12 ex 12.4 | Monte Carlo: multilevel growth with NCSIZES |
| `bsem_smallvariance_priors.inp` | Asparouhov & Muthén BSEM materials | BSEM with small-variance cross-loading priors (Holzinger-Swineford) |
| `dsem_arpath_random.inp` | DSEM (DFA section) | Dynamic SEM with random AR path |
| `esem_target_rotation.inp` | Marsh & Morin ESEM-within-CFA materials | ESEM with target rotation, longitudinal application |
| `ri_lta_two_waves.inp` | Muthén & Asparouhov RI-LTA materials | Random-intercept latent transition analysis |

## How to pick a template

Run the `references/<topic>.md` decision tree first to find the analysis family; that reference file names which specific example to consult. Don't shotgun-read all 32 — the references curate the right one per request.
