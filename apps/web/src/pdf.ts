import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

type Custody = {
  doc_id: string;
  product: { unit_id: string; product_name: string; lot: string; expiry: string; blood_type?: string | null; volume_l: number }[];
  from_site: string;
  to_site: string;
  custody: { who: string; when: string; location: string; action: string }[];
  band: string;
  min_c: number | null;
  max_c: number | null;
  time_out_of_range_min: number;
  mkt_c: number | null;
  sensor_id: string;
  calibration_date: string;
  event_class: string;
  disposition: string;
  audit: { actor: string; action: string; created_at: string; old_value: string; new_value: string; reason: string }[];
  footer: string;
  payload_hash: string;
};

export function downloadCustodyPdf(c: Custody) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  doc.setFillColor(4, 21, 28);
  doc.rect(0, 0, 595, 72, "F");
  doc.setTextColor(46, 196, 182);
  doc.setFontSize(16);
  doc.text("CryoDispatch  ·  Chain of Cold Custody", 36, 32);
  doc.setFontSize(10);
  doc.setTextColor(215, 243, 242);
  doc.text(`${c.doc_id}    hash ${c.payload_hash}`, 36, 52);

  doc.setTextColor(20, 20, 20);
  doc.setFontSize(11);
  let y = 96;
  const line = (label: string, value: string) => {
    doc.setFont("helvetica", "bold");
    doc.text(label, 36, y);
    doc.setFont("helvetica", "normal");
    doc.text(value, 180, y, { maxWidth: 380 });
    y += 18;
  };
  line("1. Document ID", c.doc_id);
  const prod = c.product[0];
  line(
    "2. Product",
    prod
      ? `${prod.product_name}  lot ${prod.lot}  exp ${prod.expiry}  qty ${c.product.length}  ${prod.blood_type ?? ""}`
      : "—",
  );
  line("3. From / to", `${c.from_site}  →  ${c.to_site}`);
  y += 6;
  doc.setFont("helvetica", "bold");
  doc.text("4. Custody log", 36, y);
  y += 8;
  autoTable(doc, {
    startY: y,
    head: [["Who", "When (IST)", "Location", "Action"]],
    body: c.custody.map((h) => [h.who, h.when, h.location, h.action]),
    theme: "grid",
    styles: { fontSize: 8 },
    margin: { left: 36, right: 36 },
  });
  y = ((doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable?.finalY ?? y) + 22;
  line("5. Band / min / max / out", `${c.band}   min ${c.min_c}   max ${c.max_c}   TOR ${c.time_out_of_range_min} min   MKT ${c.mkt_c ?? "n/a (not used for blood/vaccine release)"}`);
  line("6. Sensor / calibration", `${c.sensor_id}   last cal ${c.calibration_date}`);
  line("7. Event class", c.event_class);
  line("8. Disposition", c.disposition);
  y += 8;
  doc.setFont("helvetica", "bold");
  doc.text("9. Audit trail (computer-generated)", 36, y);
  y += 8;
  autoTable(doc, {
    startY: y,
    head: [["Actor", "Action", "Old → new", "Reason", "When"]],
    body: c.audit.map((a) => [a.actor, a.action, `${a.old_value} → ${a.new_value}`, a.reason, a.created_at]),
    theme: "striped",
    styles: { fontSize: 7 },
    margin: { left: 36, right: 36 },
  });
  const endY = ((doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable?.finalY ?? 720) + 24;
  doc.setFontSize(8);
  doc.setTextColor(80, 80, 80);
  doc.text(c.footer, 36, Math.min(endY, 810), { maxWidth: 520 });
  doc.save(`${c.doc_id}.pdf`);
}
