# Mplus skill — developer notes (v1)

Companion document to `mplus_skill_v1.zip`. Records what's in the skill, why, what to test, what's missing.

## What's in the skill

```
mplus_skill/
├── SKILL.md                          (62 lines — pure routing + universals)
├── references/                       (15 files, 3,538 lines total)
│   ├── syntax-fundamentals.md        Block structure, operators, naming, defaults
│   ├── data-preparation.md           File format, MISSING codes, CATEGORICAL/COUNT/SURVIVAL, MI workflow
│   ├── regression-path.md            Linear/logistic/probit/Poisson/censored regression, path with bootstrap CI
│   ├── efa.md                        EFA 1-K factors, rotations (GEOMIN/PROMAX/BI-GEOMIN/TARGET), bifactor, multilevel EFA
│   ├── cfa-sem.md                    CFA (cont/cat), SEM, MGCFA, invariance ladder, MIMIC, XWITH, bifactor, 2nd-order
│   ├── mediation-moderation.md       Simple/parallel/serial mediation, latent mediator, moderated mediation, Bayesian alt
│   ├── growth-survival.md            Linear/quadratic/free-time LGM, multi-indicator LGM, parallel-process, Cox + discrete survival
│   ├── lca-lpa.md                    LCA, LPA, factor mixture, distal outcomes (BCH), class enumeration, KNOWNCLASS
│   ├── mixture-longitudinal.md       LCGA, GMM, LTA (with measurement invariance across waves), parallel-process GMM
│   ├── multilevel.md                 Two-/three-level, cross-classified, two-level CFA/SEM/growth, 1-1-1 mediation (latent centering)
│   ├── multilevel-mixture.md         Within / between classes, multilevel growth mixture, multilevel LCA
│   ├── missing-bayesian.md           FIML, AUXILIARY, MI generation + analysis (TYPE=IMPUTATION), Bayesian SEM, plausible values, NMAR
│   ├── monte-carlo.md                Power analysis, sample-size determination, mixture MC, multilevel MC, external-data MC
│   ├── special-features.md           RI-CLPM, BSEM (small-variance priors), ESEM, DSEM/RDSEM, IRT (2PL/GRM), alignment, RI-LTA
│   └── common-errors.md              Parsing / identification / convergence / mixture / multilevel / Bayesian / categorical failure modes
└── assets/examples/                  (32 .inp templates + README index)
    └── README.md                     Maps every .inp to source chapter and topic
```

Total: ~3,600 lines of reference content + 32 vetted templates from the official library.

### What lives in SKILL.md (not in references)

- The triggering description with ~40 keyword variants ("CFA", "verifying factor analysis", "RI-CLPM", "结构方程", "中介分析", etc.). This is the only thing always in Claude's context, so it has to do all the trigger work.
- The routing table (which reference to read for what request).
- The seven non-negotiables: lowercase var names, declare categorical, complete files, block order, etc. These apply to *every* `.inp` Claude generates regardless of analysis.
- Universal variable-naming and scoping rules (8-char limit, range expansion, USEVARIABLES/AUXILIARY interaction, WITHIN/BETWEEN exclusivity).

### What's in `references/` instead

Anything topic-specific: decision trees per analysis family, skeletons, complete examples, common variants, and per-family pitfalls. These are only read when the topic comes up — keeps the always-on context small while still giving Claude depth on demand.

## Design tradeoffs

### One reference per User's Guide chapter — mostly

The User's Guide already groups by analysis type, and the chapter structure maps cleanly to user mental models ("I want CFA" → ch. 5 → cfa-sem.md). I broke from this only where:

1. **Mediation/moderation** got its own file across chapter 3 (observed) and chapter 5 (latent XWITH) — users think of "mediation" as one task, not two.
2. **Special features** combines RI-CLPM, BSEM, ESEM, DSEM, IRT, alignment, RI-LTA — these are *concepts*, not chapters; each appears scattered across the User's Guide + special-topic releases. One file with TOC scales better than seven half-empty files.
3. **Chapter 13 (special features)** had no examples in the raw library (only an index page), so its content is folded into the `special-features.md` file instead.

### Why not split mediation/moderation by latent vs observed?

I considered separate `mediation-observed.md` and `mediation-latent.md` but the user-facing distinction is fuzzy — most real-world questions mix observed and latent variables. One file with clearly-marked sections wins on findability.

### Why `common-errors.md` is huge (174 lines)

Error messages are reverse-lookup material — users don't read them top to bottom; they grep for a specific symptom. Bigger means more hit-rate. Organized by symptom category (parsing / identification / convergence / etc.) so the table-of-contents is the lookup index.

### Why I bundled 32 templates instead of 25

The User's Guide examples are short (typical < 1KB) and self-contained. Bundling extras is nearly free, and having a canonical file for every analysis family (rather than asking Claude to reconstruct) measurably reduces the chance of subtle syntax drift (e.g., forgetting `KNOWNCLASS` in LTA, or `BASEHAZARD = ON` for parametric survival). At 87KB total, the entire skill fits well under any reasonable bundle-size budget.

### Why imperative voice + "explain the why"

Following the skill-creator methodology: terse imperative for rules ("Always include TITLE, DATA, VARIABLE, and MODEL blocks") because Claude responds well to clear directives; but every non-obvious rule has a short *why* attached because LLMs can generalize past edge cases when they understand the reasoning, not just the rule. Example: "Mplus reads top-to-bottom and rejects out-of-order blocks" beats "ALWAYS put TITLE first."

## Suggested test scenarios

These 10 prompts cover the main analysis families and several edge cases. Each should result in Claude (a) recognizing the trigger keyword, (b) reading the right reference file, (c) producing a runnable `.inp` adapted to the user's specifics.

1. **Basic CFA** — "I have 12 items measuring two constructs (6 items each). All items are 5-point Likert. Help me write a CFA in Mplus." *(Expected: cfa-sem.md → categorical CFA with 6+6 indicators, WLSMV; note Likert-5 is borderline continuous-vs-ordinal; ask user or pick one with rationale.)*

2. **Mediation with bootstrap** — "我想做一个中介分析: x → m → y，用 bootstrap 算间接效应的置信区间。给我一个 Mplus 的 inp 文件。" *(Tests Chinese-language trigger + bootstrap CI pattern from regression-path.md / mediation-moderation.md.)*

3. **Measurement invariance across groups** — "I'm comparing a 4-factor anxiety model across three age groups. Walk me through configural, metric, and scalar invariance tests." *(Tests cfa-sem.md invariance ladder + MGCFA syntax.)*

4. **Latent growth + covariate** — "Four waves of depression scores per person, time-invariant covariates (sex, baseline SES), and a time-varying covariate (employment status at each wave). Linear growth model please." *(Tests growth-survival.md + correct TI vs TV covariate placement.)*

5. **LCA enumeration** — "I have eight binary symptom items. I think there are 3-5 latent classes. Show me how to run K=1 through K=5 and what to compare." *(Tests lca-lpa.md class enumeration workflow + BIC/LMR/BLRT explanation.)*

6. **Two-level random slope** — "Students nested in 60 schools. I want to know if the effect of homework time on test scores varies across schools, and whether school resources predict that variation." *(Tests multilevel.md random slope + cross-level interaction syntax.)*

7. **RI-CLPM** — "Three waves of self-esteem and academic achievement. I want to separate stable individual differences from within-person changes — I think this is called RI-CLPM?" *(Tests special-features.md RI-CLPM section, including the often-forgotten random intercept factor specification.)*

8. **Power analysis** — "Help me design a Monte Carlo power analysis for a CFA with one latent factor, six indicators, and one predictor. I want power ≥ .80 to detect a standardized regression of .25. How many participants?" *(Tests monte-carlo.md MONTECARLO + MODEL POPULATION + TECH9 workflow.)*

9. **LTA with covariate** — "Two waves of latent class measurement (3 classes per wave from 5 binary items), and I want a covariate (treatment group) to predict the transition probabilities." *(Tests mixture-longitudinal.md LTA + measurement-invariance labels + transition syntax.)*

10. **Debugging session** — "My Mplus model crashes with 'THE LATENT VARIABLE COVARIANCE MATRIX (PSI) IS NOT POSITIVE DEFINITE.' Here's my .inp [paste]. What's wrong?" *(Tests common-errors.md retrieval + diagnostic workflow.)*

Two stretch tests:
- "我的两层数据有学生嵌套在班级里，因变量是学业成绩，自变量是学习动机（个人水平）和班级氛围（班级水平），想用贝叶斯估计。" *(Multilevel + Bayesian — tests reading two references.)*
- "Translate this lavaan model to Mplus: `model <- 'f1 =~ y1 + y2 + y3; f2 =~ y4 + y5 + y6; f3 ~ f1 + f2'`" *(Tests SEM + lavaan → Mplus translation; Claude needs to know lavaan's `=~` ↔ `BY`, `~` ↔ `ON`.)*

### How to evaluate

For each test prompt, look for:
- ✅ Recognized the analysis family (no asking "what kind of analysis?")
- ✅ Read the right reference file (visible in tool calls if logged)
- ✅ Generated a complete `.inp` (all required blocks)
- ✅ Used lowercase variable names + ranges where natural
- ✅ Declared CATEGORICAL / GROUPING / CLUSTER appropriately
- ✅ Picked the right ESTIMATOR (WLSMV for cat, BAYES for complex, etc.) and *stated it*
- ✅ Asked for appropriate OUTPUT (STDYX, MODINDICES, CINTERVAL, TECH8 as relevant)
- ✅ For mixture: STARTS specified, TECH11/TECH14 in OUTPUT
- ✅ For multilevel: WITHIN/BETWEEN allocated correctly, CLUSTER set
- ❌ Watch for: hallucinated keywords, syntax that won't parse, wrong default-value assumptions, conflating mediation with latent moderation, missing `;` at end of statements

## Known limitations

1. **No support for Mplus version differences.** Mplus 8.0 introduced `MODEL = CONFIGURAL METRIC SCALAR;` shortcut; older versions need long-form. The skill defaults to current syntax; users on Mplus 7.x may need adjustment.

2. **Chapter 13 (Special Features) content is sparse.** The original library had only the chapter index page (no example folders). Coverage of advanced topics in `special-features.md` is drawn from the special-topics releases instead — fine in practice but the User's Guide ch. 13 examples weren't available to mine.

3. **No coverage of MIRT (multidimensional IRT) beyond standard 2PL/GRM.** The IRT section is short; bifactor IRT and other advanced parameterizations route through `cfa-sem.md` bifactor + IRT.

4. **No coverage of `MONTECARLO` for survival with frailty.** Survival MC is mentioned but not deeply templated. Same for Bayesian survival.

5. **Genetics-specific syntax (twin models, ACE decomposition) is not covered.** Chapter 5 ex5.18 hints at twin model `WITH` constraints, but a full ACE/ADE template isn't provided. The original library's `04_special_topics/Genetics/` had no `.inp` files — only papers.

6. **The skill assumes English UI / English User's Guide concepts.** The trigger keywords include Chinese terms ("结构方程", "中介分析", etc.) but the references themselves are in English. If users want bilingual references, that's a v2 expansion.

7. **No coverage of MplusAutomation R workflow.** The skill writes `.inp` files; running them via R's `MplusAutomation` package and parsing output is out of scope.

8. **DSEM coverage is shallow.** DSEM is a large topic (continuous-time, multilevel time-varying coefficients, hybrid models). One DSEM template + one section in `special-features.md` is a starting point but Asparouhov & Muthén's full DSEM materials would warrant a dedicated reference.

9. **Multi-group LCA / measurement invariance of latent classes** is mentioned in `lca-lpa.md` but the canonical template (`KNOWNCLASS` plus measurement labels) is illustrated only as a snippet, not a bundled `.inp` file (mainly because the User's Guide examples don't have one perfectly suited).

10. **No automated linter / validator.** The skill helps generate syntax but doesn't verify that the syntax parses. A v2 enhancement: include a script that does a lightweight syntactic check (matching `;`, valid block names, etc.).

## Sources I read

### Primary (User's Guide examples, read in full)
- `01_users_guide/chap3_regression_path/`: ex3.1, ex3.2, ex3.3, ex3.4, ex3.5, ex3.6, ex3.7, ex3.8part1, ex3.9, ex3.10, ex3.11, ex3.14, ex3.15, ex3.16, ex3.17, ex3.18
- `01_users_guide/chap4_efa/`: all 8 examples (ex4.1part1 through ex4.7)
- `01_users_guide/chap5_cfa_sem/`: ex5.1, ex5.2, ex5.3, ex5.4, ex5.5, ex5.6, ex5.8, ex5.11, ex5.13, ex5.14, ex5.18, ex5.20, ex5.21, ex5.23, ex5.24, ex5.25, ex5.27, ex5.29
- `01_users_guide/chap6_growth_survival/`: ex6.1, ex6.2, ex6.3, ex6.4, ex6.6, ex6.7, ex6.8, ex6.10, ex6.11, ex6.12, ex6.13, ex6.14, ex6.15, ex6.17, ex6.19, ex6.20, ex6.22, ex6.23, ex6.24, ex6.25
- `01_users_guide/chap7_mixture_crosssectional/`: ex7.1, ex7.2, ex7.3, ex7.4, ex7.7, ex7.9, ex7.10, ex7.12, ex7.13, ex7.14, ex7.16, ex7.18, ex7.22, ex7.27
- `01_users_guide/chap8_mixture_longitudinal/`: ex8.1, ex8.2, ex8.3, ex8.4, ex8.5, ex8.6, ex8.7, ex8.8, ex8.10, ex8.13part1, ex8.14, ex8.15
- `01_users_guide/chap9_multilevel/`: ex9.1a, ex9.2, ex9.3, ex9.5, ex9.6, ex9.7, ex9.9, ex9.10, ex9.11, ex9.12, ex9.14, ex9.16, ex9.18, ex9.20, ex9.22, ex9.27
- `01_users_guide/chap10_multilevel_mixture/`: ex10.1, ex10.2, ex10.3, ex10.4, ex10.6, ex10.7, ex10.8, ex10.10, ex10.13
- `01_users_guide/chap11_missing_bayesian/`: all 10 examples (ex11.1 through ex11.8part3)
- `01_users_guide/chap12_montecarlo/`: ex12.1, ex12.2, ex12.3, ex12.4, ex12.5, ex12.6, ex12.7, ex12.8, ex12.10, ex12.12

### Secondary (special-topics releases, surveyed)
- `04_special_topics/BSEM/baysemversion1/` — Asparouhov & Muthén BSEM materials (run8, run19, run20)
- `04_special_topics/DSEM_TimeSeries/DSEM/` — sections 5.1, 5.5, 5.7 (centering, DFA, TVEM)
- `04_special_topics/ESEM/Supplementary materials_ESEM1/` — ESEM-within-CFA illustrations
- `04_special_topics/IRT/all_tables/Table 1/`
- `04_special_topics/MeasurementInvariance/baysemversion1/` (run19, alignment example)
- `04_special_topics/Mediation/LatentCentering/` (McNeish multilevel mediation tables)
- `04_special_topics/RI-LTA/` — Muthén & Asparouhov RI-LTA scripts
- `04_special_topics/SurvivalAnalysis/Survival/`
- `02_web_notes/Note19/`, `webnote1/`, `web10/`, `webnote4/`, `webnote5/`, `webnote6/`

Total examples surveyed: roughly 150-180 `.inp` files across the library's 1,506 files. The 32 bundled templates are the most pedagogically clear of those.

## Next steps for v2

If iterating later:

1. **Run the 10 test prompts above** and inspect outputs. Likely revisions: (a) tighten any references where Claude over-quotes the reference, (b) add a missing variant if a test reveals one, (c) clarify pitfalls based on actual errors observed.
2. **Add a dedicated `lavaan-translation.md` reference** if users frequently arrive with R/lavaan code to translate.
3. **Expand DSEM templates** if intensive longitudinal users emerge as a frequent audience.
4. **Add a `genetics.md` reference** with ACE/ADE twin model templates (extract from User's Guide ex5.18 + add).
5. **Build an evals harness** following the skill-creator methodology (evals/evals.json with 15-20 test prompts, ground-truth assertions, baseline-vs-with-skill comparison).
6. **Consider per-version notes** for users on older Mplus (the shortcut invariance syntax, certain output options, were added in 8.0).
