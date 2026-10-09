# Nepal Climate Risk Explorer

**Live app:** https://nepal-climate-risk.streamlit.app

An interactive Streamlit app and analysis notebook that assess climate-disaster risk across Nepal's 77 districts. The risk index is tested against 12,341 recorded disasters (2011–2026, after removing duplicate records), and the project ends with a traceable USD 100 million resilience recommendation.

**Core idea:** Risk = Hazard × Exposure × Vulnerability, scored per district, then validated against Nepal's own disaster history (BIPAD Portal).

## Key findings
- Rainfall has risen about **22 mm/year since 2004**; extreme-rain days are up **~49%**.
- The **landslide index validates well** (ρ = 0.52 with recorded landslides); terrain ruggedness is the strongest driver.
- The **flood index does not** (ρ = 0.24): recorded floods concentrate on the flat Terai plains, which the available variables don't describe.
- The **26 Aug 2026 glacier collapse is missing** from the disaster record, and glacial hazard is invisible to the data, so part of the budget goes to monitoring and data.

## Data cleaning
The notebook's **Phase 0b** applies ten documented cleaning steps: profiling, key standardisation, type fixes, missing values and placeholder codes, duplicates, range checks, consistency checks, a UTC → Nepal time-zone correction, and removal of known-bad columns. Each is logged in `outputs/clean/cleaning_log.csv`. Main changes: 177 duplicate disaster records removed (12,518 → 12,341), all event dates corrected to Nepal time, and 11 unusable columns dropped.

## Project structure
```
app/
  streamlit_app.py      # the app (8 pages)
  risk_model.py         # scoring engine; reproduces the notebook (self-test: python app/risk_model.py)
.streamlit/config.toml  # theme and settings
nepal_climate_capstone_student_data/   # input data (climate_hazard.csv excluded from Git; see below)
outputs/                # results produced by the notebook and read by the app
  clean/                # cleaned data tables + cleaning_log.csv (audit trail of every cleaning step)
cleaning_toolkit.py     # reusable data-cleaning functions (also shown in the notebook, Phase 0b)
nepal_risk_assessment.ipynb  # full documented analysis
build_notebook.py       # generates the notebook
deck/                   # optional slide-deck builder (Node.js)
LEARNING_GUIDE.md       # plain-language explanation and presentation guide
requirements.txt        # pinned Python packages (tested on Python 3.12)
```

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
The app opens at http://localhost:8501. Map backgrounds need an internet connection.

### Re-running the analysis
The app only needs the files already in `outputs/`. To regenerate them, place `climate_hazard.csv` (129 MB, from the course data pack; too large for GitHub) in `nepal_climate_capstone_student_data/`, then:
```bash
pip install notebook
python build_notebook.py
jupyter nbconvert --to notebook --execute --inplace nepal_risk_assessment.ipynb
```

## Deploy

### Step 1: Put the project on GitHub
1. Create a GitHub account at https://github.com if you don't have one.
2. Click **New repository**. Name it, for example, `nepal-climate-risk`, choose **Private** (see *Privacy* below), and do **not** add a README or .gitignore (this project already has them). Click **Create repository**.
3. In a terminal in the project folder, run:
   ```bash
   git init
   git add .
   git status
   ```
   Check the list: `.venv/`, `climate_hazard.csv` and `Nepal_Capstone_Brief.pdf` must **not** appear (`.gitignore` excludes them).
4. Commit and push (replace `YOUR-USERNAME`):
   ```bash
   git commit -m "Nepal climate risk explorer: analysis notebook and Streamlit app"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/nepal-climate-risk.git
   git push -u origin main
   ```
   The first push opens a browser window to sign in to GitHub. If `git commit` says it doesn't know who you are, run once:
   `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.

### Step 2: Deploy on Streamlit Community Cloud (free)
1. Go to https://share.streamlit.io and sign in **with GitHub**. Allow access to your repositories, including private ones if your repo is private.
2. Click **Create app** → **Deploy a public app from GitHub** (the wording covers private repos too).
3. Fill in:
   - **Repository:** `YOUR-USERNAME/nepal-climate-risk`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
   - **App URL:** choose a name, e.g. `nepal-climate-risk`
4. Open **Advanced settings** and set **Python version = 3.12** (the version this project is tested on).
5. Click **Deploy**. The first build takes 2–5 minutes while packages install.
6. If the repo is private, the app is private too. Share it under **Share** → invite viewers by email (for example your instructor).

### Updating the app later
Edit locally, then:
```bash
git add .
git commit -m "Describe your change"
git push
```
Streamlit Cloud redeploys automatically within a minute.

### Troubleshooting
| Problem | Fix |
|---|---|
| `ModuleNotFoundError` in the cloud logs | The package is missing from `requirements.txt`; add it and push |
| `FileNotFoundError` for a CSV | The file wasn't committed. Check `git status` and that it isn't excluded by `.gitignore` |
| `push` rejected: file over 100 MB | A large file slipped in. Remove it with `git rm --cached <file>`, add it to `.gitignore`, then commit and push |
| Maps show dots but no background | Normal when offline; the cloud version has internet |
| App "sleeps" after a few days unused | Free apps hibernate; anyone opening it can wake it in about 30 seconds |

## Privacy and course materials
The capstone brief states that course materials may not be shared publicly. This repository therefore:
- excludes the brief PDF and the original zip (`.gitignore`);
- should be created as a **private** GitHub repo, with the Streamlit app shared only with invited viewers.

Check your programme's policy before making the repo or app public.

## Data sources
- **NASA POWER** (power.larc.nasa.gov): daily rainfall (PRECTOTCORR), temperature, humidity, wind
- **HydroSHEDS**: elevation (15 arc-sec DEM) and flow accumulation
- **Nepal National Statistics Office**, 2021 Census: population and density
- **OpenStreetMap** (Overpass API): hospitals, schools, roads, bridges
- **Wikipedia**, List of power stations in Nepal (as of 9 Mar 2026): hydropower capacity
- **geoBoundaries ADM2**: district boundaries and representative points
- **BIPAD Portal**, Government of Nepal: disaster incidents 2011–2026
