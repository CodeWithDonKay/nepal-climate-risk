// Builds Nepal_Climate_Risk_Deck.pptx from ../outputs/deck_data.json (exported by the notebook).
// Run from this folder:  node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("./apply_theme.js");

const D = require(path.join(__dirname, "..", "outputs", "deck_data.json"));
const OUT = path.join(__dirname, "..", "Nepal_Climate_Risk_Deck.pptx");

const THEME = {
  name: "Himalaya Risk",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14202B", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F5F7F9",
    accent1: "1F3A5F", accent2: "3B5BA9", accent3: "B8243B",   // navy (labels) | indigo (data) | crimson (risk/highlight)
    accent4: "76838F", accent5: "2462A3", accent6: "C9D1D9",   // muted ink | flood blue | context grey
    hlink: "2F4FA0", folHlink: "76838F",
  },
};
const HEX = THEME.colors;
const MUTED = "76838F";
const GRID = "E3E7EB";
const STATUS = { good: "1F7A4D", warn: "8A5A00", bad: "B8243B" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.title = "Nepal Climate Risk and Resilience Assessment";
pres.author = "Capstone student";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

const L = 0.6;          // left margin
const CW = 12.133;      // content width
const TOP = 1.8;        // content top on content slides

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: L, y: 1.55, w: 8.4, h: 0.4, fontSize: 14, bold: true, color: C.accent6, charSpacing: 2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: L, y: 2.0, w: 8.4, h: 2.1, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: L, y: 4.3, w: 8.0, h: 1.4, fontSize: 18, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: L, y: 0.35, w: 9.0, h: 0.32, fontSize: 12, bold: true, color: C.accent4, charSpacing: 2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: L, y: 0.7, w: CW, h: 0.85, fontSize: 34, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Nepal Climate Risk and Resilience Assessment", options: { x: L, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 12.33, y: 7.05, w: 0.4, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: L, y: 0.6, w: 9.0, h: 0.35, fontSize: 12, bold: true, color: C.accent6, charSpacing: 2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: L, y: 0.95, w: CW, h: 0.9, fontSize: 38, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------- helpers ----------
async function iconData(name, hex = "FFFFFF") {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + hex, size: 256 }));
  const png = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
async function iconCircle(slide, name, x, y, d, fill, label) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: `${label} circle` });
  const pad = d * 0.27;
  slide.addImage({ data: await iconData(name), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, objectName: `${label} icon`, altText: label });
}
function text(slide, t, opts) {
  slide.addText(t, { isTextBox: true, margin: 0, valign: "top", fontSize: 14, color: C.text1, ...opts });
}
function card(slide, x, y, w, h, fill = C.background2, name = "card") {
  const line = fill === C.background2 ? { color: "DDE2E7", width: 0.75 } : { type: "none" };
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.05, fill: { color: fill }, line, objectName: name });
}
// Finding tags (F1..F11) - the deck's motif: every claim is traceable.
function tags(slide, list, xRight = L + CW, y = 0.33) {
  const w = 0.62, gap = 0.1;
  let x = xRight - list.length * w - (list.length - 1) * gap;
  for (const t of list) {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.32, rectRadius: 0.04, fill: { color: C.background1 }, line: { color: "C7D1DE", width: 0.75 }, objectName: `tag ${t}` });
    text(slide, t, { x, y, w, h: 0.32, fontSize: 11, bold: true, color: C.accent1, fontFace: "Consolas", align: "center", valign: "middle" });
    x += w + gap;
  }
}
function stat(slide, x, y, w, big, label, color = C.text1) {
  text(slide, big, { x, y, w, h: 0.75, fontSize: 40, bold: true, color, fontFace: THEME.headFontFace });
  text(slide, label, { x, y: y + 0.78, w, h: 0.6, fontSize: 14, color: C.text1 });
}
function chartStyle(extra = {}) {
  return {
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, dataLabelColor: "1B2A33",
    titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: "1B2A33", showTitle: true,
    valGridLine: { color: GRID, size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineColor: GRID, valAxisLineShow: false, showLegend: false, legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: MUTED,
    ...extra,
  };
}
function newSlide(master, section, kicker, title) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (kicker) s.addText(kicker, { placeholder: "kicker" });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}

(async () => {
  // ============ 1. Title ============
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  s.addText("CAPSTONE PROJECT  |  OCTOBER 2026", { placeholder: "kicker" });
  s.addText("Where Nepal's Climate Risk Lives", { placeholder: "title" });
  s.addText("A risk assessment of all 77 districts, tested against 15 years of recorded disasters, and a USD 100 million resilience recommendation", { placeholder: "body" });
  s.addShape(pres.shapes.OVAL, { x: 9.55, y: 1.75, w: 3.2, h: 3.2, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "hero circle" });
  s.addImage({ data: await iconData("FaMountain"), x: 10.35, y: 2.55, w: 1.6, h: 1.6, objectName: "hero icon", altText: "Mountain" });
  s.addNotes(
    "Good morning. This assessment answers one practical question: if a donor has 100 million dollars to make Nepal more resilient to climate disasters, where should it go and why? " +
    "We look at all 77 districts, we test our answer against 15 years of real disaster records, and we end with a recommendation where every dollar is tied to evidence."
  );

  // ============ 2. The event ============
  s = newSlide("CONTENT", "Introduction", "THE EVENT", "26 August 2026: a glacier collapse");
  const rows = [
    ["FaMountain", "Trigger", "Glacier and rock-and-ice collapse at high altitude"],
    ["FaWater", "Path", "Flash flood down the Bhote Koshi and Trishuli river corridor"],
    ["FaUsers", "Human cost", "Significant loss of life and displacement"],
    ["FaBolt", "Assets", "Damage to hydropower generation facilities"],
  ];
  for (let i = 0; i < rows.length; i++) {
    const y = TOP + 0.15 + i * 1.2;
    await iconCircle(s, rows[i][0], L, y, 0.8, C.accent1, rows[i][1]);
    text(s, rows[i][1], { x: L + 1.05, y: y + 0.02, w: 5.0, h: 0.35, fontSize: 18, bold: true, color: C.text2 });
    text(s, rows[i][2], { x: L + 1.05, y: y + 0.4, w: 5.0, h: 0.5, fontSize: 14 });
  }
  card(s, 7.3, TOP + 0.1, 5.43, 4.75, C.text2, "question card");
  text(s, "THE CENTRAL QUESTION", { x: 7.7, y: TOP + 0.45, w: 4.6, h: 0.3, fontSize: 12, bold: true, color: C.accent6, charSpacing: 2 });
  text(s, "How do climate hazards, terrain, population, infrastructure and access interact to create risk across Nepal's 77 districts, and where has that risk actually materialized?",
    { x: 7.7, y: TOP + 0.95, w: 4.6, h: 3.2, fontSize: 20, color: C.background1 });
  s.addNotes(
    "On 26 August 2026 a glacier and rock-and-ice collapse sent a flash flood down the Bhote Koshi and Trishuli rivers, north of Kathmandu. People died, families were displaced, and hydropower plants were damaged. " +
    "This was not a one-off: Nepal has a long record of floods and landslides. So the question is bigger than this one event. Across all 77 districts, where is the risk, what drives it, and does Nepal's own disaster history agree with us?"
  );

  // ============ 3. Approach ============
  s = newSlide("CONTENT", "Introduction", "OUR APPROACH", "Risk exists only where three things meet");
  const trio = [
    ["FaCloudShowersHeavy", "Hazard", "Heavy rain, steep terrain, big rivers", C.accent3],
    ["FaUsers", "Exposure", "People, hospitals, schools, hydropower", C.accent2],
    ["FaRoad", "Vulnerability", "Few roads, overstretched hospitals", C.accent1],
  ];
  const cx = [1.55, 5.87, 10.19];
  for (let i = 0; i < 3; i++) {
    await iconCircle(s, trio[i][0], cx[i], TOP, 1.4, trio[i][3], trio[i][1]);
    text(s, trio[i][1], { x: cx[i] - 0.9, y: TOP + 1.55, w: 3.2, h: 0.4, fontSize: 20, bold: true, color: C.text2, align: "center" });
    text(s, trio[i][2], { x: cx[i] - 0.9, y: TOP + 1.97, w: 3.2, h: 0.4, fontSize: 14, align: "center" });
    if (i < 2) text(s, "×", { x: cx[i] + 2.0, y: TOP + 0.25, w: 1.1, h: 0.9, fontSize: 44, bold: true, color: C.accent4, align: "center", valign: "middle" });
  }
  const steps = [
    ["1  MEASURE", "Score all 77 districts on hazard, exposure and vulnerability"],
    ["2  TEST", "Compare scores with 12,341 recorded disasters (after cleaning), 2011-2026"],
    ["3  INVEST", "Allocate USD 100M, every dollar tied to a named finding"],
  ];
  for (let i = 0; i < 3; i++) {
    const x = L + i * 4.17;
    card(s, x, 4.95, 3.8, 1.65, C.background2, `step ${i + 1}`);
    text(s, steps[i][0], { x: x + 0.3, y: 5.15, w: 3.2, h: 0.35, fontSize: 14, bold: true, color: C.accent1, charSpacing: 1 });
    text(s, steps[i][1], { x: x + 0.3, y: 5.55, w: 3.2, h: 0.9, fontSize: 14 });
  }
  s.addNotes(
    "Disaster professionals define risk as hazard times exposure times vulnerability. A huge landslide on an empty mountainside is hazard without exposure: low risk. A city with no hazard is also low risk. Risk is high only where all three meet. " +
    "Our method has three steps: measure those three ingredients for every district, test the result against real disasters, and then invest."
  );

  // ============ 4. Data ============
  s = newSlide("CONTENT", "Introduction", "THE DATA", "Four datasets, four flaws fixed first");
  text(s, "What we used", { x: L, y: TOP, w: 5.9, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
  const data = [
    ["FaCloudRain", "Climate: NASA POWER", "Daily rainfall and temperature, 1990-2026"],
    ["FaMountain", "Terrain and rivers: HydroSHEDS", "Elevation, river size, distance to rivers"],
    ["FaUsers", "Exposure: Census 2021, OpenStreetMap", "Population, hospitals, schools, roads, hydropower"],
    ["FaClipboardList", "Disasters: BIPAD Portal", "12,341 floods, landslides and rain events after removing duplicates"],
  ];
  for (let i = 0; i < 4; i++) {
    const y = TOP + 0.6 + i * 1.12;
    await iconCircle(s, data[i][0], L, y, 0.7, C.accent1, data[i][1]);
    text(s, data[i][1], { x: L + 0.95, y, w: 5.0, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
    text(s, data[i][2], { x: L + 0.95, y: y + 0.37, w: 5.0, h: 0.35, fontSize: 13, color: MUTED });
  }
  text(s, "What we corrected", { x: 6.95, y: TOP, w: 5.8, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
  const fixes = [
    ["Rainfall doubles in 2004", "A satellite data-source change, not climate. Trends use 2004-2025 only."],
    ["Only 45 of 77 rain series unique", "Neighbouring districts share a satellite cell. Each counted once."],
    ["Slope data stuck near 90°", "A unit error upstream. Elevation spread used instead."],
    ["2026 ends on 30 August", "A partial year. Excluded from annual totals."],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 6.95 + (i % 2) * 2.94, y = TOP + 0.6 + Math.floor(i / 2) * 2.2;
    card(s, x, y, 2.78, 2.0, C.background2, `fix ${i + 1}`);
    text(s, fixes[i][0], { x: x + 0.2, y: y + 0.18, w: 2.38, h: 0.65, fontSize: 14, bold: true, color: C.accent1 });
    text(s, fixes[i][1], { x: x + 0.2, y: y + 0.88, w: 2.38, h: 1.0, fontSize: 13 });
  }
  s.addNotes(
    "We used four public datasets. Before any analysis we read the data dictionary and fixed four problems. " +
    "One: rainfall doubles overnight in 2004 because NASA changed its data source, so all trends start in 2004. " +
    "Two: the satellite grid is coarse, so only 45 of the 77 rainfall series are actually different; we count each once. " +
    "Three: the slope column has a unit error and shows almost 90 degrees everywhere, which is impossible, so we measure steepness with the spread of elevation instead. " +
    "Four: 2026 stops at the end of August, so we don't treat it as a full year. We also fixed a spelling mismatch for Rukum district so the tables join correctly."
  );

  // ============ 5. Rainfall trend ============
  pres.addSection({ title: "Climate" });
  s = newSlide("CONTENT", "Climate", "CLIMATE  |  2004-2025", `Rainfall is rising about ${D.rain_slope} mm a year`);
  tags(s, ["F1"]);
  const yrs = D.rain_years.map(String);
  s.addChart([
    { type: pres.charts.LINE, data: [{ name: "Annual rainfall", labels: yrs, values: D.rain_mm }], options: { chartColors: [HEX.accent2], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 7 } },
    { type: pres.charts.LINE, data: [{ name: "Trend", labels: yrs, values: D.rain_trend }], options: { chartColors: [HEX.accent3], lineSize: 2, lineDataSymbol: "none", lineDash: ["dash"] } },
  ], chartStyle({ x: L, y: TOP, w: 7.9, h: 4.95, title: "Average annual rainfall, 45 independent series (mm)", showLegend: true, legendPos: "b", catAxisLabelRotate: -45, valAxisMinVal: 1000, valAxisLabelFormatCode: "#,##0" }));
  stat(s, 8.95, TOP + 0.05, 3.78, `+${D.rain_slope} mm`, "per year since 2004 (statistically significant, p < 0.001)");
  stat(s, 8.95, TOP + 1.7, 3.78, `+${Math.round(D.anomaly_median)}%`, `2020-25 vs 2004-19, versus a normal year-to-year swing of about ${Math.round(D.cv_median)}%`);
  stat(s, 8.95, TOP + 3.35, 3.78, `${D.meaningful_n} of 45`, "independent rainfall series meaningfully wetter. None drier");
  s.addNotes(
    `Using only the reliable record from 2004, average rainfall across Nepal is rising about ${D.rain_slope} millimetres a year, and the trend is statistically significant. ` +
    `Recent years, 2020 to 2025, are about ${Math.round(D.anomaly_median)} percent wetter than 2004 to 2019. Rainfall naturally swings about ${Math.round(D.cv_median)} percent from year to year, so this change is bigger than normal noise. ` +
    `${D.meaningful_n} of the 45 independent rainfall series show a meaningful increase; none show a meaningful decrease. ` +
    "One caution: satellite products get reprocessed, so a small part of any trend could be instrumental."
  );

  // ============ 6. Extreme days + 26 Aug ============
  s = newSlide("CONTENT", "Climate", "CLIMATE  |  EXTREMES", "Extreme-rain days are up by half");
  tags(s, ["F2", "F3"]);
  const ey = D.ext_years.map(String);
  const base = D.ext_days.map((v, i) => (D.ext_years[i] <= 2019 ? v : 0));
  const rec = D.ext_days.map((v, i) => (D.ext_years[i] >= 2020 ? v : 0));
  s.addChart(pres.charts.BAR, [
    { name: "Baseline 2004-2019", labels: ey, values: base },
    { name: "Recent 2020-2025", labels: ey, values: rec },
  ], chartStyle({ x: L, y: TOP, w: 7.6, h: 4.95, barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, chartColors: [HEX.accent6, HEX.accent2], showLegend: true, legendPos: "b", catAxisLabelRotate: -45,
    title: "Extreme-rain days per district per year (heaviest 5% of rainy days)" }));
  const pct = D.ext_pct;
  stat(s, 8.6, TOP + 0.05, 4.13, `${D.ext_base.toFixed(1)} → ${D.ext_recent.toFixed(1)}`, `extreme days per district per year (+${pct}%). Borderline significant (p = 0.05)`);
  card(s, 8.6, TOP + 1.85, 4.13, 3.1, C.text2, "event card");
  text(s, "But 26 August was an ordinary rain day", { x: 8.9, y: TOP + 2.1, w: 3.55, h: 0.75, fontSize: 17, bold: true, color: C.background1 });
  text(s, `About 20 mm fell in the corridor that day, below the ${D.nat_p95} mm extreme threshold. The trigger was ice, not rain: rainfall monitoring alone would have missed it.`,
    { x: 8.9, y: TOP + 2.9, w: 3.55, h: 1.9, fontSize: 14, color: C.background1 });
  s.addNotes(
    "We defined an extreme rain day as one of the heaviest five percent of rainy days for each district, because what counts as extreme in a dry district is different from a wet one. " +
    `The average district went from ${D.ext_base} to ${D.ext_recent} extreme days a year, about ${pct} percent more. The trend is borderline significant, so we call it a strong indication rather than proof. ` +
    "Here is the twist. January to August 2026 was the third wettest on record, but on 26 August itself the corridor got about 20 millimetres, below the extreme threshold. The disaster was triggered by ice collapsing, not by rain. That matters for where we invest."
  );

  // ============ 7. Terrain ============
  pres.addSection({ title: "Terrain and exposure" });
  s = newSlide("CONTENT", "Terrain and exposure", "TERRAIN AND RIVERS", "Eight districts: extreme terrain on big rivers");
  tags(s, ["F4"]);
  const sx = D.scatter;
  const xs = sx.x_other.concat(sx.x_hot);
  s.addChart(pres.charts.SCATTER, [
    { name: "Ruggedness", values: xs },
    { name: "Other districts", values: sx.y_other.concat(sx.x_hot.map(() => null)) },
    { name: "Steep and on major rivers", values: sx.x_other.map(() => null).concat(sx.y_hot) },
  ], chartStyle({ x: L, y: TOP, w: 7.4, h: 4.95, chartColors: [HEX.accent6, HEX.accent3], lineSize: 0, lineDataSymbolSize: 9, showLegend: true, legendPos: "b",
    title: "Each dot is a district (scores 0-100)", showValAxisTitle: true, valAxisTitle: "River size x closeness", showCatAxisTitle: true, catAxisTitle: "Terrain ruggedness",
    valAxisTitleColor: MUTED, catAxisTitleColor: MUTED, valAxisTitleFontSize: 12, catAxisTitleFontSize: 12, valAxisTitleFontFace: "+mn-lt", catAxisTitleFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 100, catAxisMinVal: 0, catAxisMaxVal: 100 }));
  text(s, "Top third on both measures", { x: 8.4, y: TOP, w: 4.33, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  sx.hot_names.forEach((n, i) => {
    const x = 8.4 + (i % 2) * 2.2, y = TOP + 0.55 + Math.floor(i / 2) * 0.58;
    card(s, x, y, 2.05, 0.46, C.background2, `chip ${n}`);
    text(s, n, { x: x + 0.15, y, w: 1.8, h: 0.46, fontSize: 14, bold: true, color: C.accent1, valign: "middle" });
  });
  text(s, [
    { text: "Why together? ", options: { bold: true, color: C.text2 } },
    { text: "Landslides can dam rivers and burst downstream; ice collapses travel down steep valleys through river corridors. Steep plus river means cascading hazard." },
  ], { x: 8.4, y: TOP + 3.0, w: 4.33, h: 1.4, fontSize: 14 });
  text(s, "Ruggedness = spread of elevation within the district (supplied slope data is corrupted).", { x: 8.4, y: TOP + 4.45, w: 4.33, h: 0.5, fontSize: 11, italic: true, color: MUTED });
  s.addNotes(
    "Next, physical geography. Terrain ruggedness is how much the elevation varies inside a district: valleys and peaks together mean steep, unstable ground. River hazard combines how big the river is with how close the land is to it. " +
    "These two measures are almost unrelated, so each adds new information. Eight districts are in the top third on both, including Gorkha, Sankhuwasabha and Ramechhap. " +
    "Why does the combination matter? A landslide can block a river and then burst, and an ice collapse travels down steep valleys through river corridors. That cascade is exactly what happened on 26 August."
  );

  // ============ 8. Exposure & vulnerability ============
  s = newSlide("CONTENT", "Terrain and exposure", "EXPOSURE AND VULNERABILITY", "Assets cluster in cities; fragility in mountains");
  tags(s, ["F5", "F6"]);
  const barOpts = (x, w, title, color) => chartStyle({ x, y: TOP, w, h: 4.3, barDir: "bar", chartColors: [color], title, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0", catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 115, barGapWidthPct: 45, catAxisLabelFontSize: 12 });
  s.addChart(pres.charts.BAR, [{ name: "Exposure", labels: D.top_exposure.labels, values: D.top_exposure.values }], barOpts(L, 5.85, "Exposure score: people and critical assets (top 8)", HEX.accent2));
  s.addChart(pres.charts.BAR, [{ name: "Vulnerability", labels: D.top_vuln.labels, values: D.top_vuln.values }], barOpts(6.88, 5.85, "Vulnerability score: weak road and hospital access (top 8)", HEX.accent2));
  text(s, "Kathmandu Valley, Pokhara (Kaski) and the southern plains hold most people. Dolakha holds the most hydropower (587 MW).", { x: L, y: 6.2, w: 5.85, h: 0.75, fontSize: 13 });
  text(s, "One or two mapped hospitals for 100,000+ people and very sparse roads. Not captured: poverty, age, housing quality.", { x: 6.88, y: 6.2, w: 5.85, h: 0.75, fontSize: 13 });
  s.addNotes(
    "Exposure is what's in harm's way: people, density, hospitals, schools and hydropower. It concentrates in Kathmandu, Pokhara and the southern plains, plus hydropower hubs like Dolakha. We tested different weights and the ranking barely changed. " +
    "Vulnerability is how hard it is to cope and to help: we use road density and people per hospital. The most vulnerable districts are remote mountain districts like Taplejung and Darchula. " +
    "We are honest about what's missing: poverty, age structure and housing quality aren't in the data, so vulnerability is only partly measured."
  );

  // ============ 9. Index construction ============
  pres.addSection({ title: "Risk index" });
  s = newSlide("CONTENT", "Risk index", "THE RISK INDEX", "High only where all three are high");
  const blocks = [
    ["HAZARD", "Flood: rain + rivers\nLandslide: rain + terrain", C.accent3],
    ["EXPOSURE", "People, density, hydropower, hospitals, schools", C.accent2],
    ["VULNERABILITY", "Road access and people per hospital", C.accent4],
  ];
  for (let i = 0; i < 3; i++) {
    const x = L + i * 3.17;
    card(s, x, TOP, 2.7, 2.1, blocks[i][2], blocks[i][0]);
    text(s, blocks[i][0], { x: x + 0.2, y: TOP + 0.2, w: 2.3, h: 0.4, fontSize: 16, bold: true, color: C.background1, charSpacing: 1 });
    text(s, blocks[i][1], { x: x + 0.2, y: TOP + 0.7, w: 2.3, h: 1.3, fontSize: 14, color: C.background1 });
    text(s, i < 2 ? "×" : "=", { x: x + 2.7, y: TOP + 0.6, w: 0.47, h: 0.8, fontSize: 32, bold: true, color: C.accent4, align: "center", valign: "middle" });
  }
  card(s, L + 3 * 3.17, TOP, 2.62, 2.1, C.text2, "risk block");
  text(s, "RISK", { x: L + 3 * 3.17 + 0.2, y: TOP + 0.2, w: 2.2, h: 0.4, fontSize: 16, bold: true, color: C.accent6, charSpacing: 1 });
  text(s, "Geometric mean of the three, scored 0-100", { x: L + 3 * 3.17 + 0.2, y: TOP + 0.7, w: 2.2, h: 1.3, fontSize: 14, color: C.background1 });
  const choices = [
    ["FaCompressArrowsAlt", "Log scaling", "Stops giants like Kathmandu flattening every other district onto the same score"],
    ["FaBalanceScale", "Weights tested", "Equal weights give almost the same ranking (ρ = 0.99), so our judgment calls don't drive results"],
    ["FaTimes", "Multiply, don't add", "No hazard must mean no risk. An additive version ranks similarly anyway (ρ = 0.90)"],
  ];
  for (let i = 0; i < 3; i++) {
    const x = L + i * 4.17;
    card(s, x, 4.35, 3.8, 2.35, C.background2, `choice ${i + 1}`);
    await iconCircle(s, choices[i][0], x + 0.25, 4.6, 0.6, C.accent4, choices[i][1]);
    text(s, choices[i][1], { x: x + 1.0, y: 4.68, w: 2.6, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
    text(s, choices[i][2], { x: x + 0.25, y: 5.35, w: 3.3, h: 1.25, fontSize: 13 });
  }
  s.addNotes(
    "Here is how the index is built. Hazard comes in two versions: flood hazard combines heavy rain with river size and closeness; landslide hazard combines heavy rain with terrain ruggedness. " +
    "We multiply hazard, exposure and vulnerability using a geometric mean, so a district scores high only if all three are high. If any one is near zero, risk is low. " +
    "Three choices to know: we log-scaled skewed numbers so Kathmandu doesn't squash everyone else; we checked that our weights don't change the answer; and we chose multiplication because it matches what risk means."
  );

  // ============ 10. Top 10 ============
  s = newSlide("CONTENT", "Risk index", "THE RISK INDEX", "The ten highest-risk districts");
  s.addChart(pres.charts.BAR, [{ name: "Risk", labels: D.top_risk.labels, values: D.top_risk.values }], chartStyle({
    x: L, y: TOP, w: 7.4, h: 4.95, barDir: "bar", chartColors: [HEX.accent3], title: "Combined risk score (0-100)", showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0", catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 112, barGapWidthPct: 40, catAxisLabelFontSize: 12 }));
  text(s, "What the top ten share", { x: 8.4, y: TOP, w: 4.33, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
  text(s, [
    { text: "Steep mountain terrain and heavy rain", options: { bullet: true, breakLine: true } },
    { text: "Weak road and hospital access", options: { bullet: true, breakLine: true } },
    { text: "Mostly hill and mountain districts, not the big cities", options: { bullet: true } },
  ], { x: 8.4, y: TOP + 0.5, w: 4.33, h: 1.7, fontSize: 14, paraSpaceAfter: 8 });
  card(s, 8.4, TOP + 2.45, 4.33, 2.5, C.background2, "corridor card");
  const cr = D.corridor_rank;
  text(s, "Where is the 26 Aug corridor?", { x: 8.65, y: TOP + 2.65, w: 3.85, h: 0.4, fontSize: 15, bold: true, color: C.accent1 });
  text(s, `Sindhupalchok #${cr.Sindhupalchok}, Nuwakot #${cr.Nuwakot}, Rasuwa #${cr.Rasuwa} of 77. Our index does not flag it. The validation explains why.`,
    { x: 8.65, y: TOP + 3.1, w: 3.85, h: 1.7, fontSize: 14 });
  s.addNotes(
    "These are the ten highest-risk districts on the combined index: Myagdi, Darchula, Taplejung, Sankhuwasabha and so on. They combine steep terrain and heavy rain with weak road and hospital access. " +
    `Notice what's not here: the corridor hit on 26 August. Sindhupalchok ranks ${cr.Sindhupalchok} and Rasuwa ${cr.Rasuwa}. That is an important signal, and the validation section explains it.`
  );

  // ============ 11. Validation scorecard ============
  pres.addSection({ title: "Validation" });
  s = newSlide("CONTENT", "Validation", "VALIDATION", "Tested against 12,341 real disasters");
  tags(s, ["F7", "F8", "F9"]);
  const dec = D.decision;
  const score = [
    ["FaCheck", "Landslide index", `ρ = ${dec["landslide index"].landslide_events.toFixed(2)}`, "vs recorded landslides", "VALIDATED", "Terrain ruggedness is the strongest driver; explains about half the variation (R² = 0.49)", STATUS.good, "F8"],
    ["FaExclamation", "Combined index", "ρ = 0.39", "vs all events (0.43 vs deaths)", "MODERATE", "Significant and useful, but driven almost entirely by its landslide part", STATUS.warn, "F7"],
    ["FaTimes", "Flood index", `ρ = ${dec["flood index"].flood_events.toFixed(2)}`, "vs recorded floods", "NOT VALIDATED", "Floods happen where our variables don't look. Explained on the next slide", STATUS.bad, "F9"],
  ];
  for (let i = 0; i < 3; i++) {
    const x = L + i * 4.17, [ic, name, big, vs, verdict, why, col] = score[i];
    card(s, x, TOP, 3.8, 4.15, C.background2, `${name} card`);
    await iconCircle(s, ic, x + 0.3, TOP + 0.3, 0.7, col, name);
    text(s, name, { x: x + 1.2, y: TOP + 0.45, w: 2.4, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
    text(s, big, { x: x + 0.3, y: TOP + 1.2, w: 3.2, h: 0.8, fontSize: 40, bold: true, color: C.text1 });
    text(s, vs, { x: x + 0.3, y: TOP + 2.0, w: 3.2, h: 0.35, fontSize: 13, color: MUTED });
    text(s, verdict, { x: x + 0.3, y: TOP + 2.5, w: 3.2, h: 0.35, fontSize: 14, bold: true, color: col, charSpacing: 2 });
    text(s, why, { x: x + 0.3, y: TOP + 2.9, w: 3.2, h: 1.15, fontSize: 13 });
  }
  text(s, [
    { text: "Reading ρ (rank correlation across 77 districts): ", options: { bold: true, color: C.text2 } },
    { text: "0 = no link  |  0.3 = weak  |  0.5 = moderate  |  0.7+ = strong" },
  ], { x: L, y: 6.2, w: CW, h: 0.4, fontSize: 14 });
  s.addNotes(
    "This is the most important part. Until now, our index is just a hypothesis. We tested it against 12,341 disasters recorded by Nepal's BIPAD system since 2011, after removing duplicate records. " +
    "The landslide index works: a correlation of 0.52 with recorded landslides, and terrain ruggedness alone explains about half the difference between districts. " +
    "The combined index is moderate, around 0.4, but that comes almost entirely from its landslide part. " +
    "The flood index fails, at only 0.24. We did not re-tune the model to make this number look better; that would be cheating. Instead we found the reason."
  );

  // ============ 12. Why floods fail ============
  s = newSlide("CONTENT", "Validation", "VALIDATION  |  FLOODS", "Why the flood index fails: floods are on the plains");
  tags(s, ["F9"]);
  const fc = D.flood_corr;
  s.addChart(pres.charts.BAR, [{ name: "rho", labels: Object.keys(fc), values: Object.values(fc) }], chartStyle({
    x: L, y: TOP, w: 6.6, h: 4.6, barDir: "bar", chartColors: [HEX.accent2], title: "Correlation with recorded flood events (ρ)", showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "+0.00;-0.00", catAxisOrientation: "maxMin", valAxisMinVal: -0.5, valAxisMaxVal: 0.5, valAxisLabelFormatCode: "0.0", barGapWidthPct: 50, catAxisLabelFontSize: 12, catAxisLabelPos: "low" }));
  text(s, "Most recorded floods", { x: 7.6, y: TOP, w: 5.13, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
  text(s, D.top_flood_events.labels.join(", "), { x: 7.6, y: TOP + 0.45, w: 5.13, h: 0.45, fontSize: 16, bold: true, color: C.accent1 });
  text(s, "Mostly flat southern lowlands (Terai), plus Kathmandu Valley: dense, well-connected, low-lying.", { x: 7.6, y: TOP + 0.95, w: 5.13, h: 0.8, fontSize: 14 });
  text(s, [
    { text: "The cause: ", options: { bold: true, color: C.text2 } },
    { text: "our flood variables describe mountain rivers and rain. Lowland floods happen where rivers leave the mountains and spread over flat, crowded plains. No variable in the data captures floodplain flatness." },
  ], { x: 7.6, y: TOP + 1.9, w: 5.13, h: 1.6, fontSize: 14 });
  card(s, 7.6, TOP + 3.6, 5.13, 1.0, C.background2, "honesty card");
  text(s, "We report this rather than re-tuning the model until the number looks good.", { x: 7.85, y: TOP + 3.6, w: 4.7, h: 1.0, fontSize: 14, italic: true, color: C.text2, valign: "middle" });
  s.addNotes(
    "Why do floods fail? Look at where floods are actually recorded: Jhapa, Morang, Sunsari, Kailali, and Kathmandu. Flat southern lowlands, plus Kathmandu. " +
    "Flood counts go down with rugged terrain and up with population and roads. Our flood hazard score has essentially no link at all. " +
    "The explanation is a missing variable: we measure mountain rivers and rainfall, but lowland floods happen where rivers spread across flat, crowded plains, and the dataset has nothing on floodplains. Part of it is also reporting: floods get recorded where people and roads are. " +
    "The brief tells us to explain weak results, not hide them, and that's what we've done."
  );

  // ============ 13. Decision ============
  s = newSlide("CONTENT", "Validation", "METHODOLOGICAL DECISION", "Decision: separate flood and landslide indices");
  const hl = { bold: true, color: C.background1, fill: { color: C.accent2 } };
  const cell = (v, best) => ({ text: v.toFixed(2), options: best ? hl : {} });
  const head = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
  s.addTable([
    [head("Index"), head("vs recorded floods"), head("vs recorded landslides")],
    [{ text: "Combined index" }, cell(dec["combined index"].flood_events), cell(dec["combined index"].landslide_events)],
    [{ text: "Flood index" }, cell(dec["flood index"].flood_events, true), cell(dec["flood index"].landslide_events)],
    [{ text: "Landslide index" }, cell(dec["landslide index"].flood_events), cell(dec["landslide index"].landslide_events, true)],
  ], { x: L, y: TOP + 0.1, w: 6.8, colW: [2.4, 2.2, 2.2], rowH: 0.62, fontSize: 15, fontFace: THEME.bodyFontFace, color: C.text1, align: "center", valign: "middle",
    border: { type: "solid", pt: 1, color: C.background2 }, fill: { color: C.background1 } });
  text(s, "Highlighted: the best index for each hazard. Spearman ρ across 77 districts.", { x: L, y: TOP + 2.75, w: 6.8, h: 0.4, fontSize: 12, italic: true, color: MUTED });
  const ev = [
    ["Floods and landslides strike different places", "Their district counts are unrelated (ρ = −0.13). One number can't rank both."],
    ["Each specific index wins on its own hazard", "Landslide 0.52 vs combined 0.47; flood 0.24 vs combined 0.12."],
    ["A single index would hide a weakness", "Its apparent success is its landslide part. Separating shows floods need better data."],
  ];
  for (let i = 0; i < 3; i++) {
    const y = TOP + 0.1 + i * 1.6;
    text(s, String(i + 1), { x: 7.9, y, w: 0.5, h: 0.6, fontSize: 30, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
    text(s, ev[i][0], { x: 8.5, y: y + 0.05, w: 4.23, h: 0.45, fontSize: 15, bold: true, color: C.text2 });
    text(s, ev[i][1], { x: 8.5, y: y + 0.55, w: 4.23, h: 0.9, fontSize: 13 });
  }
  s.addNotes(
    "The brief asked us to decide, with evidence, whether one combined index or separate flood and landslide indices is more defensible. The evidence points to separate indices. " +
    "First, floods and landslides happen in different districts. Second, each specific index beats the combined one on its own hazard. Third, a single number would hide the fact that we predict landslides well and floods poorly. " +
    "So we use two indices, and we treat the flood index as low confidence."
  );

  // ============ 14. Blind spots ============
  s = newSlide("CONTENT", "Validation", "VALIDATION  |  DATA QUALITY", "The record has blind spots, including this event");
  tags(s, ["F10", "F11"]);
  const yy = D.events_years.map(String);
  s.addChart(pres.charts.BAR, [
    { name: "2011-2023", labels: yy, values: D.events_n.map((v, i) => (D.events_years[i] <= 2023 ? v : 0)) },
    { name: "2024-2026", labels: yy, values: D.events_n.map((v, i) => (D.events_years[i] >= 2024 ? v : 0)) },
  ], chartStyle({ x: L, y: TOP, w: 7.2, h: 4.95, barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, chartColors: [HEX.accent6, HEX.accent2], title: "Recorded disaster events per year (BIPAD)",
    catAxisLabelRotate: -45, valAxisLabelFormatCode: "#,##0" }));
  const dpe0 = D.deaths_per_event[0], dpe1 = D.deaths_per_event[D.deaths_per_event.length - 1];
  const spots = [
    ["FaChartBar", "Reporting changed, not disasters", `Events quadrupled after 2023 while deaths per event fell from ${dpe0} to ${dpe1}: many more minor incidents logged`],
    ["FaSearch", "The 26 Aug collapse is missing", "Only six minor events and zero deaths are recorded in the corridor afterwards"],
    ["FaEyeSlash", "Glacial risk is invisible to our data", `No glacial-outburst records at all. Corridor ranks #${cr.Sindhupalchok} and #${cr.Rasuwa}`],
  ];
  for (let i = 0; i < 3; i++) {
    const y = TOP + i * 1.68;
    await iconCircle(s, spots[i][0], 8.2, y, 0.65, C.accent1, spots[i][1]);
    text(s, spots[i][1], { x: 9.05, y, w: 3.68, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
    text(s, spots[i][2], { x: 9.05, y: y + 0.42, w: 3.68, h: 1.1, fontSize: 13 });
  }
  s.addNotes(
    "The test also revealed problems with the record itself. Recorded events jump about four-fold after 2023, but deaths per event drop sharply. That means far more small incidents are being logged; it's a reporting change, not four times more disasters. " +
    "More strikingly, the 26 August collapse that prompted this assessment is not in the record: only six minor events with no deaths in the corridor afterwards. There are no glacial lake outburst records at all. " +
    "And our index ranks the corridor in the middle of the pack, because glacial hazard simply isn't in the data. These blind spots shape the investment."
  );

  // ============ 15. Allocation ============
  pres.addSection({ title: "Recommendation" });
  s = newSlide("CONTENT", "Recommendation", "RECOMMENDATION", "USD 100M: money follows evidence");
  const al = [...D.alloc].sort((a, b) => b.usd - a.usd);
  const nice = (l) => l.replace(/^\S+\s/, "");
  s.addChart(pres.charts.BAR, [{ name: "USD M", labels: al.map((a) => nice(a.line)), values: al.map((a) => a.usd) }], chartStyle({
    x: L, y: TOP, w: 7.4, h: 4.95, barDir: "bar", chartColors: [HEX.accent2], title: "Allocation (USD million)", showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: '"$"0"M"', catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 27, barGapWidthPct: 40, catAxisLabelFontSize: 12 }));
  const act = ["1a", "1b", "3", "4"], blind = ["2", "5"];
  const sum = (ids) => D.alloc.filter((a) => ids.includes(a.line.split(" ")[0])).reduce((t, a) => t + a.usd, 0);
  card(s, 8.4, TOP, 4.33, 2.3, C.background2, "act card");
  text(s, `$${sum(act)}M`, { x: 8.65, y: TOP + 0.2, w: 3.9, h: 0.7, fontSize: 36, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  text(s, "Act where evidence is strong: landslide and flood early warning, infrastructure, community preparedness", { x: 8.65, y: TOP + 0.95, w: 3.9, h: 1.2, fontSize: 14 });
  card(s, 8.4, TOP + 2.6, 4.33, 2.35, C.text2, "blind card");
  text(s, `$${sum(blind)}M`, { x: 8.65, y: TOP + 2.8, w: 3.9, h: 0.7, fontSize: 36, bold: true, color: C.background1 });
  text(s, "Close the blind spots that hid this disaster: glacial and terrain monitoring, better disaster and flood data", { x: 8.65, y: TOP + 3.55, w: 3.9, h: 1.25, fontSize: 14, color: C.background1 });
  s.addNotes(
    `Here's the recommendation. The principle is simple: money follows evidence. ${sum(act)} million goes to direct protection where our analysis is solid: landslide early warning in the validated high-risk districts, flood warning where floods are actually recorded, reinforcing exposed infrastructure, and preparing the most isolated communities. ` +
    `${sum(blind)} million goes to the blind spots: monitoring glaciers and unstable terrain, including the August corridor, and fixing the disaster and flood data so the next assessment can see what this one could not.`
  );

  // ============ 16. Traceability table ============
  s = newSlide("CONTENT", "Recommendation", "RECOMMENDATION", "Every dollar traces to a finding");
  const th = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
  const trows = [[th("Line"), th("USD"), th("Target districts (selected by rule)"), th("Findings")]];
  for (const a of D.alloc) {
    trows.push([{ text: nice(a.line), options: { bold: true, color: C.text2 } }, { text: `$${a.usd}M`, options: { bold: true, color: C.accent1 } },
      { text: a.line.startsWith("5") ? `National, piloted in: ${a.targets}` : a.targets }, { text: a.findings, options: { color: C.accent1, bold: true, fontFace: "Consolas", fontSize: 11 } }]);
  }
  s.addTable(trows, { x: L, y: TOP - 0.1, w: CW, colW: [2.75, 0.85, 7.13, 1.4], fontSize: 12, fontFace: THEME.bodyFontFace, color: C.text1, valign: "middle",
    border: { type: "solid", pt: 1, color: C.background2 }, rowH: [0.4, 0.66, 0.66, 0.66, 0.82, 0.66, 0.66], margin: [0.04, 0.08, 0.04, 0.08] });
  s.addNotes(
    "Every line is traceable. Landslide early warning goes to the top eight on the validated landslide index. Flood warning goes to the five districts with the most recorded floods, because our flood index failed. " +
    "Glacial monitoring goes to the high-mountain districts that are steep and on major rivers, plus Sindhupalchok and Rasuwa. Infrastructure reinforcement targets high exposure plus every district with 150 megawatts or more of hydropower. " +
    "Community preparedness targets the most vulnerable districts, and data infrastructure is national, piloted where hazard is high but few events are recorded. F-numbers refer to the findings in the notebook."
  );

  // ============ 17. Closing ============
  s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Recommendation" });
  s.addText("IN SUMMARY", { placeholder: "kicker" });
  s.addText("Three things to remember", { placeholder: "title" });
  const take = [
    ["Rain extremes are rising", `+${D.rain_slope} mm a year since 2004 and about half again as many extreme-rain days.`, "F1, F2"],
    ["We can rank landslide risk, not floods or glacial collapse", "Terrain explains half of landslide variation. Floods and the August collapse sit in data blind spots.", "F8 to F11"],
    ["Money follows evidence", `$${sum(act)}M protects where evidence is strong; $${sum(blind)}M closes the blind spots that hid this disaster.`, "All findings"],
  ];
  for (let i = 0; i < 3; i++) {
    const x = L + i * 4.17;
    text(s, String(i + 1), { x, y: 2.35, w: 1, h: 0.9, fontSize: 54, bold: true, color: C.accent6 });
    text(s, take[i][0], { x, y: 3.35, w: 3.75, h: 1.0, fontSize: 20, bold: true, color: C.background1 });
    text(s, take[i][1], { x, y: 4.45, w: 3.75, h: 1.3, fontSize: 15, color: C.background2 });
    text(s, take[i][2], { x, y: 5.85, w: 3.75, h: 0.35, fontSize: 12, bold: true, color: C.accent6, fontFace: "Consolas" });
  }
  text(s, "Full method, code and assumptions: nepal_risk_assessment.ipynb", { x: L, y: 6.8, w: CW, h: 0.3, fontSize: 11, color: C.accent6 });
  s.addNotes(
    "Three things to remember. One: rain extremes in Nepal are rising. Two: with this data we can rank landslide risk with reasonable confidence, but floods and glacial collapses like 26 August sit in blind spots. " +
    "Three: our 100 million follows the evidence, protecting where we're confident and closing the gaps where we're not. Thank you, I'm happy to take questions."
  );

  // ============ 18. Appendix ============
  pres.addSection({ title: "Appendix" });
  s = newSlide("CONTENT", "Appendix", "APPENDIX", "Sources, assumptions and limitations");
  const colTxt = (x, head, items) => {
    text(s, head, { x, y: TOP - 0.1, w: 3.8, h: 0.4, fontSize: 15, bold: true, color: C.accent1 });
    text(s, items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })), { x, y: TOP + 0.4, w: 3.8, h: 4.75, fontSize: 13, paraSpaceAfter: 4 });
  };
  colTxt(L, "Data sources", [
    "NASA POWER (power.larc.nasa.gov): daily rainfall (PRECTOTCORR), temperature, humidity, wind",
    "HydroSHEDS: elevation (15 arc-sec DEM) and flow accumulation",
    "Nepal National Statistics Office, 2021 Census: population and density",
    "OpenStreetMap (Overpass API): hospitals, schools, roads, bridges",
    "Wikipedia, List of power stations in Nepal (9 Mar 2026): hydropower",
    "geoBoundaries ADM2: district boundaries and area",
    "BIPAD Portal, Government of Nepal: disaster incidents 2011-2026",
  ]);
  colTxt(L + 4.17, "Key assumptions", [
    "Climate trends 2004-2025 only; 45 independent series counted once",
    "Extreme day = above district P95 of rainy days (≥ 1 mm)",
    "Baseline 2004-19 vs recent 2020-25; meaningful if larger than baseline year-to-year variation",
    "Ruggedness = elevation standard deviation (slope data unusable)",
    "Skewed variables log-scaled, then min-max to 0-100",
    "Exposure weights 30/20/20/15/15 (population, density, hydropower, hospitals, schools)",
    "Risk = geometric mean of hazard, exposure, vulnerability",
  ]);
  colTxt(L + 8.34, "Limitations", [
    "No poverty, age, housing or early-warning coverage data",
    "OpenStreetMap undercounts rural facilities and roads",
    "One rainfall point per district; coarse satellite grid",
    "No floodplain or glacial-lake variables",
    "Disaster record: reporting surge after 2023; 26 Aug 2026 event missing",
    "Correlation shows association, not cause",
  ]);
  s.addNotes("Reference slide for questions: data sources as cited in the data dictionary, every major assumption, and the limitations we identified. The notebook documents each one in detail.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
