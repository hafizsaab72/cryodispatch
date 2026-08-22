const PptxGenJS = require("pptxgenjs");
const path = require("path");

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.author = "CryoDispatch";
pres.title = "CryoDispatch — Predict. Dispatch. Prove.";

const INK = "04151C";
const PANEL = "0B2430";
const CYAN = "2EC4B6";
const ICE = "E8F1F2";
const MUTE = "7FA3AD";
const AMBER = "E07A3D";
const HOT = "E23D28";

function iceCircle(slide, x, y, letter) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w: 0.42, h: 0.42,
    fill: { color: CYAN },
  });
  slide.addText(letter, {
    x, y, w: 0.42, h: 0.42,
    align: "center", valign: "middle",
    fontSize: 12, fontFace: "Calibri", color: INK, bold: true, margin: 0,
  });
}

function darkBg(slide) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: INK },
  });
}

function lightBg(slide) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: "F4FAFA" },
  });
}

// 1 Title
{
  const s = pres.addSlide();
  darkBg(s);
  iceCircle(s, 0.7, 1.3, "C");
  s.addText("CRYODISPATCH", {
    x: 1.3, y: 1.28, w: 10, h: 0.45,
    fontFace: "Calibri", fontSize: 14, color: CYAN, charSpacing: 4, margin: 0,
  });
  s.addText("Predict. Dispatch. Prove.", {
    x: 0.7, y: 2.0, w: 12, h: 1.1,
    fontFace: "Cambria", fontSize: 40, color: ICE, bold: true, margin: 0,
  });
  s.addText("A hospital cold-chain plant — not a temperature dashboard.\nELCIA Tech Summit 2026  ·  Electronics City", {
    x: 0.7, y: 3.3, w: 11, h: 0.9,
    fontFace: "Calibri", fontSize: 18, color: MUTE, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: 4.6, w: 3.6, h: 1.6, fill: { color: PANEL }, rectRadius: 0.12,
  });
  s.addText("Sense  →  classify  →  move  →  verify  →  ticket", {
    x: 0.9, y: 5.05, w: 3.2, h: 0.8,
    fontFace: "Calibri", fontSize: 14, color: ICE, margin: 0,
  });
  s.addNotes("Open with the floor map live. This is a plant that acts.");
}

// 2 Problem
{
  const s = pres.addSlide();
  lightBg(s);
  s.addText("The gap is not monitoring", {
    x: 0.6, y: 0.45, w: 12, h: 0.7,
    fontFace: "Cambria", fontSize: 32, color: INK, bold: true, margin: 0,
  });
  const cards = [
    ["eVIN already watches ILRs", "National immunization stock + temperature. We do not replace it."],
    ["e-BloodBank already counts bags", "Inventory is solved. Floor-level evacuate-and-prove is not."],
    ["if (temp > 8) is not intelligence", "Judges have seen that dashboard. The plant has to act first."],
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.5, w: 3.9, h: 4.4, fill: { color: PANEL }, rectRadius: 0.12,
    });
    iceCircle(s, x + 0.25, 1.75, String(i + 1));
    s.addText(c[0], {
      x: x + 0.25, y: 2.4, w: 3.4, h: 1.2,
      fontFace: "Cambria", fontSize: 20, color: ICE, margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.25, y: 3.7, w: 3.4, h: 1.6,
      fontFace: "Calibri", fontSize: 15, color: MUTE, margin: 0,
    });
  });
}

// 3 Architecture
{
  const s = pres.addSlide();
  lightBg(s);
  s.addText("Three apps. One brain. MQTT as a contract.", {
    x: 0.6, y: 0.4, w: 12, h: 0.6,
    fontFace: "Cambria", fontSize: 28, color: INK, bold: true, margin: 0,
  });
  const boxes = [
    [0.6, "Simulator", "Python  ·  24 assets\nMQTT-shaped JSON"],
    [3.7, "Ingest", "Newton plant +\ngreedy dispatch"],
    [6.8, "Command", "Floor map, T_eq,\ncustody PDF"],
    [9.9, "Staff", "Accept · QR · reject\nwrong vault"],
  ];
  boxes.forEach(([x, t, b]) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.4, w: 2.85, h: 2.6, fill: { color: PANEL }, rectRadius: 0.1,
    });
    s.addText(t, { x, y: 1.6, w: 2.85, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 16, color: CYAN, bold: true, margin: 0 });
    s.addText(b, { x: x + 0.15, y: 2.2, w: 2.55, h: 1.4, align: "center", fontFace: "Calibri", fontSize: 14, color: ICE, margin: 0 });
  });
  s.addText("Live path is HTTP → plant. Dashboard never subscribes to a broker. An ESP32 can replace the sim on the same payload.", {
    x: 0.6, y: 4.4, w: 12, h: 0.8,
    fontFace: "Calibri", fontSize: 16, color: INK, margin: 0,
  });
  s.addText("cryo/{site}/assets/{id}/telemetry   ·   /status (retained)   ·   /lwt → PROBE_DEAD", {
    x: 0.6, y: 5.4, w: 12, h: 0.5,
    fontFace: "Calibri", fontSize: 14, color: MUTE, margin: 0,
  });
}

// 4 Fault taxonomy
{
  const s = pres.addSlide();
  darkBg(s);
  s.addText("Sensor death is not a hot vault", {
    x: 0.6, y: 0.4, w: 12, h: 0.6,
    fontFace: "Cambria", fontSize: 30, color: ICE, bold: true, margin: 0,
  });
  const rows = [
    ["PROBE_DEAD", "Last-will / logger silent", "Ticket only. Do not move stock."],
    ["THERMAL_EXCURSION", "T_eq headed through the band", "Spoilage clock + MOVE + compressor ticket"],
    ["BOTH", "Blind and hot", "Worst case — evacuate and re-instrument"],
  ];
  rows.forEach((r, i) => {
    const y = 1.35 + i * 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.6, y, w: 12.1, h: 1.4, fill: { color: PANEL }, rectRadius: 0.1,
    });
    iceCircle(s, 0.85, y + 0.48, String(i + 1));
    s.addText(r[0], { x: 1.5, y: y + 0.2, w: 4.2, h: 0.4, fontFace: "Calibri", fontSize: 16, color: CYAN, bold: true, margin: 0 });
    s.addText(r[1], { x: 1.5, y: y + 0.65, w: 5, h: 0.45, fontFace: "Calibri", fontSize: 14, color: MUTE, margin: 0 });
    s.addText(r[2], { x: 7.0, y: y + 0.4, w: 5.3, h: 0.6, fontFace: "Calibri", fontSize: 16, color: ICE, margin: 0 });
  });
}

// 5 Physics
{
  const s = pres.addSlide();
  lightBg(s);
  s.addText("Newton for the box. Not ARIMA.", {
    x: 0.6, y: 0.4, w: 12, h: 0.6,
    fontFace: "Cambria", fontSize: 30, color: INK, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.25, w: 7.4, h: 5.4, fill: { color: PANEL }, rectRadius: 0.12,
  });
  s.addText("τ  dT/dt  +  T  =  T_eq\n\nT_eq = T_set + α_door·door + α_h·(1 − health)\n\nt* = −τ ln((T_th − T_eq)/(T − T_eq))", {
    x: 0.9, y: 1.55, w: 6.9, h: 3.2,
    fontFace: "Calibri", fontSize: 20, color: ICE, margin: 0,
  });
  s.addText("Judges see T_eq jump while air is still legal. Demo τ is compressed (~2 min). Physics is the same.", {
    x: 0.9, y: 5.0, w: 6.9, h: 1.2,
    fontFace: "Calibri", fontSize: 15, color: MUTE, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 8.25, y: 1.25, w: 4.4, h: 5.4, fill: { color: INK }, rectRadius: 0.12,
  });
  s.addText("Skip", { x: 8.5, y: 1.5, w: 4, h: 0.4, fontFace: "Calibri", fontSize: 14, color: AMBER, margin: 0 });
  s.addText("ARIMA\nif (temp > 8)\nMKT as a release decision\nFCM / APNs\nMQTT as the only bus", {
    x: 8.5, y: 2.1, w: 3.9, h: 4.0,
    fontFace: "Calibri", fontSize: 16, color: ICE, margin: 0,
  });
}

// 6 Demo
{
  const s = pres.addSlide();
  lightBg(s);
  s.addText("Ninety seconds. A judge holds the phone.", {
    x: 0.6, y: 0.4, w: 12, h: 0.55,
    fontFace: "Cambria", fontSize: 28, color: INK, bold: true, margin: 0,
  });
  const steps = [
    ["0–10s", "Plant, not a chart"],
    ["10–25s", "Kill probe → ticket, no MOVE"],
    ["25–40s", "Compressor: T_eq up, air still legal"],
    ["40–65s", "Accept. Wrong-vault QR fails."],
    ["65–80s", "Second vault cascades to V8"],
    ["80–90s", "Custody PDF + kWh hold vs move"],
  ];
  steps.forEach((st, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.6 + col * 4.15;
    const y = 1.25 + row * 2.7;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 3.95, h: 2.45, fill: { color: PANEL }, rectRadius: 0.1,
    });
    iceCircle(s, x + 0.25, y + 0.3, String(i + 1));
    s.addText(st[0], { x: x + 0.8, y: y + 0.32, w: 2.8, h: 0.4, fontFace: "Calibri", fontSize: 14, color: CYAN, margin: 0 });
    s.addText(st[1], { x: x + 0.25, y: y + 1.0, w: 3.45, h: 1.1, fontFace: "Calibri", fontSize: 16, color: ICE, margin: 0 });
  });
}

// 7 Compliance
{
  const s = pres.addSlide();
  darkBg(s);
  s.addText("Bands we hardcode. Claims we refuse.", {
    x: 0.6, y: 0.4, w: 12, h: 0.6,
    fontFace: "Cambria", fontSize: 28, color: ICE, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.2, w: 6.1, h: 5.5, fill: { color: PANEL }, rectRadius: 0.12,
  });
  s.addText("RBC 2–6°C   ·   vaccines 2–8°C\nPlatelets 22±2°C   ·   FFP ≤ −30°C\nFreeze ≤0°C is critical on alum vaccines\nDoor-open ≠ discard\nQuarantine. Never auto-scrap.", {
    x: 0.9, y: 1.5, w: 5.6, h: 4.8,
    fontFace: "Calibri", fontSize: 18, color: ICE, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.95, y: 1.2, w: 5.7, h: 5.5, fill: { color: "1A0E0C" }, rectRadius: 0.12,
  });
  s.addText("Not FDA-certified\nNot NABH / WHO PQS\nNot an eVIN replacement\nMKT does not prove potency", {
    x: 7.25, y: 1.7, w: 5.2, h: 4.4,
    fontFace: "Calibri", fontSize: 20, color: AMBER, margin: 0,
  });
}

// 8 Close
{
  const s = pres.addSlide();
  darkBg(s);
  iceCircle(s, 0.7, 1.5, "C");
  s.addText("Closed loop. Hardware-ready.", {
    x: 1.3, y: 1.45, w: 11, h: 0.55,
    fontFace: "Cambria", fontSize: 32, color: ICE, bold: true, margin: 0,
  });
  s.addText("When a vault fails we classify the fault, move the right units to the right door with the right nurse, prove custody with QR, and open a compressor ticket — while refusing to evacuate on a dead sensor.", {
    x: 0.7, y: 2.4, w: 11.8, h: 1.6,
    fontFace: "Calibri", fontSize: 18, color: MUTE, margin: 0,
  });
  s.addText("ESP32 sketch in docs/firmware  ·  MQTT schema in docs/mqtt-schema.md  ·  Demo: docs/demo-script.md", {
    x: 0.7, y: 4.3, w: 12, h: 0.5,
    fontFace: "Calibri", fontSize: 14, color: CYAN, margin: 0,
  });
  s.addText("CryoDispatch  ·  ELCIA Tech Summit 2026", {
    x: 0.7, y: 6.4, w: 12, h: 0.4,
    fontFace: "Calibri", fontSize: 14, color: MUTE, margin: 0,
  });
}

const out = path.join(__dirname, "CryoDispatch.pptx");
pres.writeFile({ fileName: out }).then(() => {
  console.log("wrote", out);
});
