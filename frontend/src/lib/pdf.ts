import { jsPDF } from "jspdf";

export interface IncidentData {
  date: string;
  amount: string;
  account: string;
  description: string;
  phone: string;
  evidence: string[];
}

/**
 * Generates a plain-text incident report PDF.
 * Devanagari is NOT embedded — the PDF uses plain Latin only as a summary
 * and instructs user to print the full form from the portal.
 * Falls back to window.print() if jsPDF fails.
 */
export function downloadIncidentPdf(data: IncidentData): void {
  try {
    const doc = new jsPDF({ unit: "mm", format: "a4" });
    const LINE_H = 8;
    const MARGIN = 20;
    const WIDTH = 170;
    let y = MARGIN;

    const line = (text: string, bold = false) => {
      doc.setFont("helvetica", bold ? "bold" : "normal");
      const lines = doc.splitTextToSize(text, WIDTH) as string[];
      lines.forEach((l: string) => {
        if (y > 270) { doc.addPage(); y = MARGIN; }
        doc.text(l, MARGIN, y);
        y += LINE_H;
      });
    };

    doc.setFontSize(16);
    line("SAJAG — Cyber Fraud Incident Report", true);
    doc.setFontSize(11);
    y += 4;
    line("Submit this reference to the National Cyber Crime Portal: cybercrime.gov.in", false);
    line("Or call 1930 for immediate assistance.", false);
    y += 4;
    doc.setDrawColor(180, 180, 180);
    doc.line(MARGIN, y, MARGIN + WIDTH, y);
    y += 6;

    doc.setFontSize(12);
    line("Date of Incident:", true);
    line(data.date || "—");
    y += 2;
    line("Amount Lost (INR):", true);
    line(data.amount || "—");
    y += 2;
    line("Account / UPI / Wallet:", true);
    line(data.account || "—");
    y += 2;
    line("Your Phone Number:", true);
    line(data.phone || "—");
    y += 2;
    line("What Happened:", true);
    line(data.description || "—");
    y += 2;
    line("Evidence Collected:", true);
    if (data.evidence.length) {
      data.evidence.forEach((e) => line(`  - ${e}`));
    } else {
      line("  None listed");
    }
    y += 6;
    doc.setFontSize(10);
    line("DISCLAIMER: This PDF is a personal reference only. It has no official status.", false);
    line("File your complaint at cybercrime.gov.in or at your nearest police station.", false);

    doc.save("sajag-incident-report.pdf");
  } catch {
    window.print();
  }
}

