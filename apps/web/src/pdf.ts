import type { CustodyDocument } from "@cryodispatch/shared";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

const MARGIN = 36;
const LABEL_X = 180;
const VALUE_W = 380;

function finalY(doc: jsPDF, fallback: number): number {
  return (doc as unknown as { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? fallback;
}

export function downloadCustodyPdf(c: CustodyDocument) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });

  doc.setFillColor(4, 21, 28);
  doc.rect(0, 0, 595, 72, "F");
  doc.setTextColor(46, 196, 182);
  doc.setFontSize(16);
  doc.text("CryoDispatch  ·  Chain of Cold Custody", MARGIN, 32);
  doc.setFontSize(10);
  doc.setTextColor(215, 243, 242);
  doc.text(`${c.doc_id}    payload hash ${c.payload_hash}`, MARGIN, 52);

  let y = 96;
  if (c.draft) {
    doc.setFillColor(226, 61, 40);
    doc.rect(0, 72, 595, 28, "F");
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.text("DRAFT — transfer not completed, no disposition asserted", MARGIN, 90);
    y = 118;
  }

  doc.setTextColor(20, 20, 20);
  doc.setFontSize(11);

  // Wrap long values instead of letting them collide with the next field.
  const line = (label: string, value: string) => {
    doc.setFont("helvetica", "bold");
    doc.text(label, MARGIN, y);
    doc.setFont("helvetica", "normal");
    const lines = doc.splitTextToSize(value, VALUE_W) as string[];
    doc.text(lines, LABEL_X, y);
    y += Math.max(18, lines.length * 14);
  };

  const num = (v: number | null, unit = "°C") => (v == null ? "not recorded" : `${v}${unit}`);

  line("1. Document ID", c.doc_id);

  const first = c.product[0];
  const qty = c.product.length;
  const volume = c.product.reduce((s, p) => s + p.volume_l, 0);
  line(
    "2. Product",
    first
      ? `${first.product_name}${first.blood_type ? ` (${first.blood_type})` : ""} · lot ${first.lot} · exp ${first.expiry} · ${qty} unit(s), ${volume.toFixed(2)} L · labelled ${first.temp_band}°C`
      : "not recorded",
  );
  line("3. From → to", `${c.from_site}\n→ ${c.to_site}`);

  y += 6;
  doc.setFont("helvetica", "bold");
  doc.text("4. Custody log", MARGIN, y);
  y += 8;
  autoTable(doc, {
    startY: y,
    head: [["Who", "When", "Location", "Action"]],
    body: c.custody.length
      ? c.custody.map((h) => [h.who, h.when, h.location, h.action])
      : [["—", "—", "—", "no handoffs recorded"]],
    theme: "grid",
    styles: { fontSize: 8, cellPadding: 3 },
    headStyles: { fillColor: [11, 36, 48] },
    margin: { left: MARGIN, right: MARGIN },
  });
  y = finalY(doc, y) + 24;

  line(
    "5. Band / min / max",
    `labelled ${c.band} · min ${num(c.min_c)} · max ${num(c.max_c)} · time out of range ${c.time_out_of_range_min} min · window ${c.observation_window_min} min · MKT ${
      c.mkt_c == null ? "n/a (not used to release blood or vaccines)" : `${c.mkt_c}°C`
    }`,
  );
  line("6. Sensor / calibration", `${c.sensor_id} · last calibrated ${c.calibration_date}`);
  line("7. Event class", c.event_class);
  line(
    "8. Disposition",
    c.mission_status ? `${c.disposition}  [${c.mission_status}]` : c.disposition,
  );

  y += 6;
  doc.setFont("helvetica", "bold");
  doc.text("9. Audit trail (computer-generated)", MARGIN, y);
  y += 8;
  autoTable(doc, {
    startY: y,
    head: [["Actor", "Action", "Old → new", "Reason", "When"]],
    body: c.audit.map((a) => [
      a.actor,
      a.action,
      `${a.old_value || "—"} → ${a.new_value || "—"}`,
      a.reason,
      a.created_at,
    ]),
    theme: "striped",
    styles: { fontSize: 7, cellPadding: 2 },
    headStyles: { fillColor: [11, 36, 48] },
    margin: { left: MARGIN, right: MARGIN },
  });
  y = finalY(doc, 700) + 20;

  if (y > 760) {
    doc.addPage();
    y = 80;
  }
  doc.setFontSize(8);
  doc.setTextColor(80, 80, 80);
  doc.text(doc.splitTextToSize(c.footer, 520) as string[], MARGIN, y);

  doc.save(c.draft ? `DRAFT-${c.doc_id}.pdf` : `${c.doc_id}.pdf`);
}
