# Learning Guide: Nepal Climate Risk Assessment

This guide is your companion to `nepal_risk_assessment.ipynb`. Read it top to bottom once. After that you should be able to explain every part of the project in your own words and answer questions about it.

---

## 1. The project in 60 seconds

On 26 August 2026 a glacier collapse caused a deadly flash flood in Nepal's Bhote Koshi / Trishuli river corridor. A donor has a **hypothetical USD 100 million** for disaster resilience and asks:

> *Which of Nepal's 77 districts are most at risk, why, and where should the money go?*

We answered in three moves:
1. **Measure** risk in every district by combining **hazard** (rain, steep terrain, rivers), **exposure** (people and infrastructure), and **vulnerability** (roads, hospitals).
2. **Test** that measurement against 12,518 real disasters recorded from 2011 to 2026.
3. **Recommend** how to spend $100M, with every dollar linked to a specific finding.

The most important lesson is that **the test only partly passed**. We can predict *landslides* reasonably well, but not *floods*. And the disaster record itself is missing the August 2026 event. A good analyst reports this honestly and designs the investment around it.

---

## 2. Key concepts (plain-language glossary)

| Term | Plain meaning | Everyday analogy |
|---|---|---|
| **Risk = Hazard × Exposure × Vulnerability** | Disaster risk needs all three ingredients | A storm (hazard) only matters if there's a house (exposure), and it matters more if the house is weak (vulnerability) |
| **District** | Nepal's 77 administrative areas, our unit of analysis | Like counties |
| **DataFrame** | A table in Python (pandas) | An Excel sheet |
| **Join / merge** | Matching rows of two tables by a shared key (district name) | VLOOKUP |
| **Percentile (P95)** | The value 95% of observations fall below | Top 5% of exam scores |
| **Extreme rain day** | A rainy day above that district's P95 | One of the district's heaviest 5% of rainy days |
| **Linear trend / slope** | The best straight line through yearly values; slope = change per year | "Rainfall is going up 22 mm a year on average" |
| **p-value** | Probability of seeing a result this strong by pure chance if nothing real is going on. Below 0.05 = "statistically significant" | Is the coin rigged, or did it just land heads 6 times by luck? |
| **Anomaly (%)** | How much recent years differ from a baseline period | "This year's sales are 27% above our usual" |
| **Coefficient of variation (CV)** | Typical year-to-year wobble, as a % of the average | How much your monthly electricity bill normally varies |
| **Standard deviation** | How spread out values are | Elevation spread = flat plains (small) vs mountains (big) |
| **Min-max normalization** | Rescales any variable to 0–100 (lowest district = 0, highest = 100) | Converting different exams to percentages so you can average them |
| **Log transform** | Compresses very large values so a few giants don't squash everyone else | Richter scale for earthquakes |
| **Geometric mean** | Multiply values, then take the root. Low if *any* ingredient is low | A chain is only as strong as its weakest link |
| **Correlation (Spearman ρ)** | −1 to +1: do two things rank together? Based on ranks, so outliers matter less | Do taller students tend to weigh more? |
| **Regression** | Estimates each factor's effect *while holding the others constant*. **R²** = share of differences explained | Which matters more for house prices, size or location, once you account for both? |
| **Validation** | Checking a model's predictions against real outcomes | Checking a weather forecast against what actually happened |
| **Overfitting / p-hacking** | Tweaking a model until it matches the data, which makes it look good but useless | Drawing the target after shooting the arrow |
| **Structural break** | A sudden jump in data caused by a change in measurement, not reality | Switching from a bathroom scale to a gym scale |

---

## 3. How the project was built (step by step)

### Phase 0: Load and clean
- Loaded 4 CSV files: climate (1 million daily rows), exposure (77 districts × 32 columns), disaster events (12,518 rows), and climate clusters.
- **Read the data dictionary first**, as the brief requires. Several columns have known problems.
- Fixed a naming mismatch: "RUKUM EAST" vs "EASTERN RUKUM". Without this, two districts silently disappear when joining tables.

### Phase 1: Climate
1. **Spotted a fake jump.** Rainfall doubles in 2004 because NASA changed its data source. So all trends use **2004–2025** only. 2026 is excluded from yearly totals because the data stops on 30 August.
2. **Avoided double counting.** Only 45 of the 77 rainfall series are independent; some districts share one satellite grid cell. National statistics count each series once.
3. **Defined "extreme"**: P95 of each district's rainy days (≥1 mm). We also used one national threshold (29.5 mm/day) so districts can be compared with each other.
4. Computed the trend, the anomaly (2004–19 baseline vs 2020–25 recent), and extreme-day counts.

### Phase 2: Terrain and rivers
- **Ruggedness** = standard deviation of elevation. The slope columns are broken (every district shows ~90°), and we showed this with a chart.
- **River hazard** = geometric mean of river size (log) and closeness to rivers. Both are needed for a high score.
- Found 8 districts that are both very rugged and on large rivers.

### Phase 3: Exposure
- Population, density, hydropower MW, hospitals, schools → log → 0–100 → weighted average (people 50%, infrastructure 50%).
- Checked sensitivity: equal weights give almost the same ranking (ρ = 0.99), so our weighting choice doesn't drive the results.

### Phase 4: Vulnerability
- Low road density means hard to reach. High population per hospital means overwhelmed health care.
- Zero-hospital rule written (worst value), though no district has zero hospitals.
- Listed what is *missing*: poverty, age, housing quality, early-warning coverage, footpaths.

### Phase 5: Risk score
- Risk = **geometric mean** of hazard, exposure and vulnerability. This is multiplicative, matching the risk definition.
- Built three versions: combined, flood-only, and landslide-only.
- The additive alternative ranks districts similarly (ρ = 0.90). We chose multiplicative on principle: no hazard should mean no risk.

### Phase 6: Validation (the most important part)
- Counted events and deaths per district, and compared them with our scores (correlation + regression).
- Tested combined vs separate indices.
- Investigated *why* some results were weak (reporting changes, access, missing events), rather than tweaking the model.

### Phase 7: Investment
- Every budget line has a **rule** for choosing districts and cites **finding numbers**.
- Money follows confidence: targeted spending where validation is strong, monitoring and data where it is weak.

---

## 4. The findings (memorise these: they are your story)

| # | Finding | Key number |
|---|---|---|
| **F1** | Rainfall is rising | +22 mm/year (p<0.001); recent years +27% vs baseline; 33 of 45 series meaningfully wetter |
| **F2** | Extreme-rain days more frequent | 6.0 → 8.9 days/year (+49%), borderline significant (p = 0.05) |
| **F3** | The 26 Aug event was **not** a rain extreme | ~20 mm that day, below the ~30 mm threshold; it was an ice collapse. Jan–Aug 2026 was still the 3rd wettest |
| **F4** | 8 districts combine steep terrain and big rivers | Gorkha, Sankhuwasabha, Ramechhap, Dhading, Mugu, Humla, Rukum West, Kalikot |
| **F5** | Exposure is concentrated in cities and hydropower hubs | Kathmandu, Kaski, Lalitpur…; Dolakha has 587 MW |
| **F6** | Vulnerability is highest in remote mountains | Taplejung, Darchula, Bajura: one or two hospitals for 100k+ people, very few roads |
| **F7** | The combined index moderately matches reality | ρ = 0.39 with events, 0.42 with deaths |
| **F8** | The **landslide index works** | ρ = 0.53; ruggedness is the strongest predictor; R² = 0.50 |
| **F9** | The **flood index fails**, for an explainable reason | ρ = 0.23. Floods are recorded on the flat Terai plains (Jhapa, Morang, Sunsari), which our mountain-river variables don't describe |
| **F10** | The disaster record has reporting problems | Events ×4 after 2023 while deaths per event fell 0.5 → 0.04; **the 26 Aug disaster is missing** |
| **F11** | The index can't see glacial risk | Event corridor ranks only #21 (Sindhupalchok) and #47 (Rasuwa) |

**Methodological decision:** use **separate flood and landslide indices**. Flood and landslide events happen in different places (ρ = −0.14), and each specific index beats the combined index on its own hazard.

**Investment ($100M):**

| Line | $M | Findings |
|---|---|---|
| Terrain & glacial monitoring | 22 | F3, F4, F8, F11 |
| Infrastructure reinforcement | 20 | F3, F5 |
| Landslide early warning | 18 | F1, F2, F8 |
| Community preparedness | 15 | F6 |
| Data infrastructure | 15 | F9, F10, F11 |
| Flood early warning | 10 | F9 |

---

## 5. Presentation script (follow the brief's required order)

**The deck is `Nepal_Climate_Risk_Deck.pptx` (18 slides).** Every slide has **speaker notes** (in PowerPoint: *View → Notes*) with a full plain-language script. Read them aloud a few times, then put them in your own words.

| Slides | Brief's required item |
|---|---|
| 1–4 | The 26 Aug event, the question, our approach, the data and its fixes |
| 5–6 | Climate/rainfall findings 2004–2025 (F1–F3) |
| 7–8 | Terrain and rivers (F4); population and infrastructure exposure (F5–F6) |
| 9–10 | The risk index: construction and results |
| 11–14 | Validation and the combined-vs-separate decision (F7–F11) |
| 15–16 | Investment recommendation, traced to findings |
| 17 | Summary |
| 18 | Appendix: sources, assumptions, limitations (for questions) |

Aim for about 1.5 minutes per slide, around 25 minutes in total. The condensed version below covers the core story:

1. **The event.** "On 26 August 2026 a glacier collapse sent a flash flood down the Bhote Koshi and Trishuli rivers, killing people and damaging hydropower. The question: where else is Nepal at risk, and where should $100M go?"
2. **Climate (2004–2025).** "We first removed a fake jump in the satellite data. In the reliable record, rainfall is rising ~22 mm a year, and extreme-rain days are up about half. But the August disaster happened on an ordinary rain day. It was an ice collapse."
3. **Terrain & rivers.** "We measured terrain by how much elevation varies, because the supplied slope data is broken. Eight districts combine extreme terrain with big rivers."
4. **Exposure.** "People and critical assets concentrate in Kathmandu Valley, Pokhara, the southern plains, and hydropower districts like Dolakha."
5. **The risk index.** "Risk is the geometric mean of hazard, exposure and vulnerability. It's only high where all three meet. The top districts are Myagdi, Darchula, Taplejung, Sankhuwasabha…"
6. **Validation.** "We tested it against 12,500 recorded disasters. Landslides: it works, and steep terrain explains half the variation. Floods: it doesn't, because floods happen on the flat plains. And the record itself is incomplete: the August disaster is missing. So we use separate flood and landslide indices."
7. **Recommendation.** "Money follows evidence. We fund early warning where the model is validated, and monitoring and data where it revealed blind spots."

---

## 5b. The Streamlit app (your chosen presentation format)

The brief asks for **one** presentation. You chose **Option A, the interactive Streamlit app**. The slide deck stays in the folder as a backup, for example if the app can't run on presentation day. Don't submit both as your main presentation.

### How to start it
From the project folder:

```bash
python -m streamlit run app/streamlit_app.py
```

It opens at http://localhost:8501. The maps need an internet connection for their background tiles; everything else works offline.

### How the app is built (so you can explain it)
| File | What it does |
|---|---|
| `app/risk_model.py` | The scoring engine. It repeats the notebook's Phases 2–5 as functions with the weights as inputs, so sliders genuinely recompute scores. Run `python app/risk_model.py` to prove it reproduces the notebook (it checks itself). |
| `app/streamlit_app.py` | The 8 pages, charts and sliders |
| `.streamlit/config.toml` | Colours (same palette as the deck); keeps the app private to your computer |

**Key concept: re-scoring on the baseline scale.** Min-max always gives the best district 0 and the worst 100. If we re-normalised after an intervention, the treated district could look *unchanged*, because the scale would stretch to fit. So scenarios keep the **baseline** min and max as a fixed ruler. Improvements then show up as real drops.

**Key concept: why a 24% vulnerability cut only lowers risk ~9%.** Risk is the cube root of H × E × V. Cutting V by 24% multiplies risk by ∛0.76 ≈ 0.91. This is honest arithmetic, not a bug. Early warning saves lives, but it doesn't stop the landslide (hazard) or move the village (exposure).

### Demo script (follow the sidebar order, ~15 minutes)
| Page | What to show | What to say |
|---|---|---|
| **The question** | Map with the corridor as larger dots | "This is the 26 August event and the question: where else is Nepal at risk?" |
| **Climate** | Four headline numbers, then the two charts | "Rainfall is up 22 mm a year and extreme days are up about half. But 26 August was an ordinary rain day: the trigger was ice." |
| **Terrain and exposure** | Hover the red dots in the scatter; switch tabs | "Eight districts combine steep terrain with big rivers. People cluster in cities; fragility is in the mountains." |
| **Risk explorer** | Switch Landslide → Flood → Combined; pick **Sindhupalchok** in the profile | "Here's every district's risk. Notice the corridor sits mid-table. Our data can't see glacial hazard." |
| **Scenarios** | Preset "Landslide early-warning targets"; move the coverage slider | "If early warning reaches 80% of people, risk in these districts drops by about 8 points. Hazard and exposure don't change, which is why we also invest in monitoring." |
| **Validation** | The three ρ numbers, the heatmap, then the flood explanation | "Landslides: the index works. Floods: it doesn't, and here's why. And the August disaster isn't even in the record." |
| **Investment** | Bar chart and table; the early-warning simulation table | "$63M where evidence is strong, $37M to close the blind spots." |
| **Sidebar (bonus)** | Switch to "Weighted sum", then Reset | "Changing the method barely changes the ranking, so our conclusions are robust. Reported results always use the defaults." |

**Important if an examiner plays with the sliders:** the Validation page shows correlations under whatever settings are active, with a warning banner. Say clearly: *"The brief forbids tuning weights until the correlation looks good. These sliders are for testing robustness. Our reported results use the defaults, chosen before validation."*

---

## 5c. Putting the app online (concepts)

The step-by-step commands are in **README.md → Deploy**. Here is what each piece *is*, so the steps make sense:

| Thing | What it is | Analogy |
|---|---|---|
| **Git** | A program on your computer that records snapshots ("commits") of your project folder | Save points in a video game |
| **GitHub** | A website that stores a copy of your Git project online | Google Drive for code, with full history |
| **`git push`** | Uploads your latest commits to GitHub | Syncing to the cloud |
| **Streamlit Community Cloud** | A free service that reads your GitHub repo, installs the packages, and runs the app on a server with a public web address | A host who sets up your stall at a market using your instructions |
| **`requirements.txt`** | The list of Python packages (with exact versions) the server must install | A shopping list, so the server buys exactly what you tested with |
| **`.gitignore`** | A list of files Git must never upload | A "do not pack" list |
| **Private repo** | Only you (and people you invite) can see the code | A locked folder |

**Why some files are not uploaded:**
- `climate_hazard.csv` is 129 MB and GitHub refuses files over 100 MB. The app doesn't need it: it reads the pre-computed results in `outputs/`. Only re-running the notebook needs it.
- `Nepal_Capstone_Brief.pdf` is course material that may not be redistributed.
- `.venv/` is your local Python installation. The server builds its own from `requirements.txt`.

**Why "tested on Python 3.12":** the app was verified in your `.venv` (Python 3.12) using only the files Git will upload, which simulates a fresh download from GitHub. Choosing 3.12 in Streamlit's *Advanced settings* makes the server match.

---

## 6. Questions you may be asked, and how to answer

**"Why didn't you use the slope data?"**
It's corrupted: a unit error upstream makes almost every district show ~90°, which is physically impossible. We demonstrated this with a chart and used elevation standard deviation instead, which the data dictionary verifies as reliable.

**"Why start the climate analysis in 2004 and not 1990?"**
NASA changed its data source around 2004 and average rainfall doubled overnight. That's an instrument change, not climate. Comparing across it would invent a fake trend.

**"Your flood validation is weak. Isn't your model wrong?"**
Partly, and we say so. The weakness has a clear explanation: Nepal's recorded floods happen on the flat southern plains, while our flood variables describe mountain rivers and rainfall. We didn't tweak the model to force a better number, because that would be overfitting. Instead, we funded flood early warning in the historically flooded districts and funded floodplain data collection.

**"Why multiply instead of add?"**
Risk requires all three ingredients. With addition, a city with no hazard still gets a medium score. With multiplication (geometric mean), no hazard means low risk. The two methods rank districts similarly anyway (ρ = 0.90).

**"How did you choose the weights?"**
People 50%, infrastructure 50%, a stated judgment. We tested equal weights and the ranking barely changed (ρ = 0.99), so the conclusions don't depend on our weights.

**"Why does Sindhupalchok, where the disaster happened, rank only 21st?"**
Our index measures rainfall-driven hazard. The August event was a glacier collapse, which isn't in the data. That's why $22M goes to terrain and glacial monitoring, specifically including the event corridor.

**"Is a correlation of 0.5 good?"**
For district-level structural data (no information on exactly *where* in a district people live), explaining about half the variation in landslides is a solid result. It's not good enough to predict individual disasters, and the brief doesn't ask us to.

**"What does the data NOT capture?"**
Poverty, age structure, housing quality, early-warning coverage, footpath access, and accurate rural facility counts (OpenStreetMap undercounts). These are named limitations and are part of the data-infrastructure investment.

**"How do you know the app shows the same numbers as your notebook?"**
`app/risk_model.py` contains a self-test. Running it compares every score with the notebook's output and stops with an error if any differs by more than 0.01.

**"Where does the 30% early-warning effect come from?"**
It's an assumption, labelled in the app, based on the Global Commission on Adaptation (2019) estimate that 24 hours' warning can cut damage by about 30%. The slider lets anyone test other values.

**"Why did disaster counts jump after 2023?"**
Deaths per event fell from ~0.5 to 0.04 at the same time. That means many more small incidents are being logged. It's a reporting change, not four times more disasters.

---

## 7. Files in the project

| File | What it is |
|---|---|
| `app/streamlit_app.py`, `app/risk_model.py` | **Deliverable (a):** the interactive Streamlit app (see section 5b) |
| `requirements.txt` | Python packages needed to run the notebook and app (`pip install -r requirements.txt`) |
| `README.md` | Project front page on GitHub, with run and deployment steps |
| `.gitignore` | Files Git must never upload (large data, course PDF, `.venv`) |
| `Nepal_Climate_Risk_Deck.pptx` | Backup: the 18-slide deck with speaker notes |
| `deck/build_deck.js` | Script that generates the deck from `outputs/deck_data.json`. Re-run with `node build_deck.js` inside `deck/` after re-running the notebook |
| `nepal_risk_assessment.ipynb` | **Deliverable (b):** the documented notebook with all explanations and results |
| `build_notebook.py` | Script that generates the notebook (edit here if you change text or logic, then re-run) |
| `outputs/district_risk_scores.csv` | Final table: all 77 districts with every score. Feeds the presentation |
| `outputs/validation_*.csv`, `investment_allocation.csv`, `phase1_climate_summary.csv` | Supporting tables |
| `outputs/figures/*.png` | 9 charts ready for slides |

### How to run it yourself
Open the notebook in Jupyter:

```bash
python -m jupyter notebook nepal_risk_assessment.ipynb
```

Then choose *Run → Run All Cells*. To regenerate it from the script after editing:

```bash
python build_notebook.py
```

```bash
python -m jupyter nbconvert --to notebook --execute --inplace nepal_risk_assessment.ipynb
```

---

## 8. Practice exercise (to check your understanding)
Try changing one decision and see what happens. This is the best way to really understand the project:
1. In the notebook, change the exposure weights (e.g. population 0.6), re-run, and check whether the top 10 changes.
2. Change the baseline to 2004–2014 vs 2015–2025. Does the anomaly still look meaningful?
3. Change `WET = 1.0` to `WET = 5.0`. How do the extreme thresholds move?

If the big conclusions survive these changes, they are *robust*. That is a strong thing to be able to say in your presentation.
