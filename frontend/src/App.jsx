// App.jsx — ServicePilot Final Version
// White SaaS design + formatted RCA/CAB rendering + PDF export

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import axios from "axios";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import {
  AlertTriangle, Search, FileText, ClipboardList,
  ArrowRight, Zap, Brain, ChevronRight,
  Download, Loader2, CheckCircle, X, Shield,
  Activity, Database, Server, Lock
} from "lucide-react";

const SEV = {
  P1: { color:"text-red-500",    bg:"bg-red-50",    border:"border-red-200",    dot:"bg-red-500"    },
  P2: { color:"text-orange-500", bg:"bg-orange-50", border:"border-orange-200", dot:"bg-orange-500" },
  P3: { color:"text-yellow-600", bg:"bg-yellow-50", border:"border-yellow-200", dot:"bg-yellow-500" },
  P4: { color:"text-green-600",  bg:"bg-green-50",  border:"border-green-200",  dot:"bg-green-500"  },
};

// ─────────────────────────────────────────────────────────────────────────────
// DOCUMENT PARSER
// Converts the raw LLM text (which uses === SECTION === markers and
// Markdown pipe tables) into a structured array of typed blocks.
// This is what enables proper formatted rendering and PDF export.
// ─────────────────────────────────────────────────────────────────────────────
function parseDocument(text) {
  if (!text) return [];
  const blocks = [];
  const lines  = text.split("\n");
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();

    // Detect === SECTION HEADING ===
    if (line.startsWith("===") && line.endsWith("===")) {
      const title = line.replace(/===/g, "").trim();
      if (title) blocks.push({ type: "heading", content: title });
      i++;
      continue;
    }

    // Detect Markdown table block — a group of lines containing pipes
    if (line.includes("|") && line.startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      // Parse the table: first row is header, skip separator row (--- lines)
      const rows = tableLines
        .filter(l => !l.replace(/\|/g, "").replace(/-/g, "").trim() === false)
        .filter(l => !/^\|[-| ]+\|$/.test(l))
        .map(l =>
          l.split("|")
           .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1)
           .map(cell => cell.trim())
        );
      if (rows.length >= 2) {
        blocks.push({ type: "table", headers: rows[0], rows: rows.slice(1) });
      }
      continue;
    }

    // Detect bold headings like **HEADING** or * HEADING:
    if (
      (line.startsWith("**") && line.endsWith("**")) ||
      (line.startsWith("- **") && line.endsWith("**"))
    ) {
      const content = line.replace(/\*\*/g, "").replace(/^-\s*/, "").trim();
      if (content) blocks.push({ type: "subheading", content });
      i++;
      continue;
    }

    // Detect numbered or bulleted list items
    if (/^[\d]+\./.test(line) || line.startsWith("- ") || line.startsWith("* ") || line.startsWith("+ ")) {
      const listItems = [];
      while (
        i < lines.length &&
        (
          /^[\d]+\./.test(lines[i].trim()) ||
          lines[i].trim().startsWith("- ") ||
          lines[i].trim().startsWith("* ") ||
          lines[i].trim().startsWith("+ ")
        )
      ) {
        listItems.push(
          lines[i].trim()
            .replace(/^[\d]+\.\s*/, "")
            .replace(/^[-*+]\s*/, "")
            .replace(/\*\*/g, "")
        );
        i++;
      }
      if (listItems.length) blocks.push({ type: "list", items: listItems });
      continue;
    }

    // Non-empty paragraph text
    if (line.length > 0) {
      const cleanLine = line.replace(/\*\*/g, "").replace(/^\*\s*/, "").trim();
      if (cleanLine) {
        // Merge adjacent paragraph lines into one block
        let paragraph = cleanLine;
        i++;
        while (
          i < lines.length &&
          lines[i].trim().length > 0 &&
          !lines[i].trim().startsWith("===") &&
          !lines[i].trim().startsWith("|") &&
          !/^[\d]+\./.test(lines[i].trim()) &&
          !lines[i].trim().startsWith("- ") &&
          !lines[i].trim().startsWith("* ") &&
          !lines[i].trim().startsWith("**")
        ) {
          paragraph += " " + lines[i].trim().replace(/\*\*/g, "");
          i++;
        }
        blocks.push({ type: "paragraph", content: paragraph });
        continue;
      }
    }

    i++;
  }

  return blocks;
}

// ─────────────────────────────────────────────────────────────────────────────
// DOCUMENT RENDERER
// Takes the parsed blocks array and renders them as styled React elements.
// Headings: bold, white. Body: light gray. Tables: proper HTML table.
// Used for both the RCA and CAB RFC tabs inside the modal.
// ─────────────────────────────────────────────────────────────────────────────
function DocumentRenderer({ blocks }) {
  if (!blocks || blocks.length === 0) {
    return (
      <p className="text-gray-400 text-sm italic">No content available.</p>
    );
  }

  return (
    <div className="space-y-5">
      {blocks.map((block, idx) => {
        // ── Major section heading ===
        if (block.type === "heading") {
          return (
            <div key={idx} className="pt-4 first:pt-0">
              <h3
                className="font-bold text-white text-base uppercase tracking-wide pb-2"
                style={{
                  fontFamily: "Inter, sans-serif",
                  borderBottom: "1px solid rgba(255,255,255,0.1)",
                  marginBottom: "12px",
                }}
              >
                {block.content}
              </h3>
            </div>
          );
        }

        // ── Sub-heading (bold line within a section) ──
        if (block.type === "subheading") {
          return (
            <p
              key={idx}
              className="font-semibold text-white text-sm"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              {block.content}
            </p>
          );
        }

        // ── Body paragraph ──
        if (block.type === "paragraph") {
          return (
            <p
              key={idx}
              className="text-gray-300 text-sm leading-relaxed"
              style={{ fontFamily: "'Times New Roman', Times, serif" }}
            >
              {block.content}
            </p>
          );
        }

        // ── Numbered / bulleted list ──
        if (block.type === "list") {
          return (
            <ol key={idx} className="space-y-1.5 pl-1">
              {block.items.map((item, j) => (
                <li key={j} className="flex gap-3 text-sm">
                  <span
                    className="text-green-400 font-bold flex-shrink-0 w-5 text-right"
                  >
                    {j + 1}.
                  </span>
                  <span
                    className="text-gray-300 leading-relaxed"
                    style={{ fontFamily: "'Times New Roman', Times, serif" }}
                  >
                    {item}
                  </span>
                </li>
              ))}
            </ol>
          );
        }

        // ── Table (Action Items, Approval Matrix, etc.) ──
        if (block.type === "table") {
          return (
            <div key={idx} className="overflow-x-auto rounded-xl">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr style={{ background: "#16a34a" }}>
                    {block.headers.map((h, j) => (
                      <th
                        key={j}
                        className="px-4 py-2.5 text-left text-white font-semibold text-xs uppercase tracking-wider"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, j) => (
                    <tr
                      key={j}
                      style={{
                        background: j % 2 === 0 ? "#1e293b" : "#162032",
                      }}
                    >
                      {row.map((cell, k) => (
                        <td
                          key={k}
                          className="px-4 py-2.5 text-gray-300 text-xs border-t border-gray-700/50"
                          style={{ fontFamily: "'Times New Roman', Times, serif" }}
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}

// generatePDF — Produces a clean, professional corporate-style PDF.
// Design principles:
//   - White background throughout, no colors anywhere
//   - Headings: Helvetica Bold, black, with a simple underline rule
//   - Body text: Times Roman, black, for the formal document feel
//   - Tables: minimal gray borders, black text, light gray header background
//   - Pagination: headings are never orphaned at the bottom of a page
//     (we require 35mm of remaining space before placing a heading)
//   - No footer text on any page
function generatePDF(blocks, documentTitle, incidentDescription) {
  const doc   = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const marginLeft  = 20;
  const marginRight = 20;
  const marginTop   = 20;
  const marginBottom= 20;
  const maxW        = pageW - marginLeft - marginRight;
  let   y           = marginTop;

  // ── Page overflow helper ──────────────────────────────────────────────────
  // Returns true if adding `needed` mm of content would overflow the page.
  const willOverflow = (needed) => y + needed > pageH - marginBottom;

  // Adds a new page and resets the y cursor to the top margin.
  const newPage = () => {
    doc.addPage();
    y = marginTop;
  };

  // ── Document title ────────────────────────────────────────────────────────
  // We always have room for the title on the first page because y = marginTop.
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.setTextColor(0, 0, 0);
  doc.text(documentTitle, marginLeft, y);
  y += 7;

  // Thin rule under the title
  doc.setDrawColor(0, 0, 0);
  doc.setLineWidth(0.4);
  doc.line(marginLeft, y, pageW - marginRight, y);
  y += 5;

  // ── Incident summary ──────────────────────────────────────────────────────
  if (incidentDescription && incidentDescription.trim().length > 0) {
    doc.setFont("times", "italic");
    doc.setFontSize(9);
    doc.setTextColor(60, 60, 60);
    const summary = `Incident: ${incidentDescription.slice(0, 350)}${incidentDescription.length > 350 ? "..." : ""}`;
    const summaryLines = doc.splitTextToSize(summary, maxW);
    summaryLines.forEach(line => {
      if (willOverflow(5)) newPage();
      doc.text(line, marginLeft, y);
      y += 5;
    });
    y += 5; // breathing room after the summary
  }

  // ── Render content blocks ─────────────────────────────────────────────────
  blocks.forEach(block => {

    // HEADING — major section (from === HEADING === markers)
    // Orphan protection: require 35mm so the heading + at least 3 body lines
    // always share the same page. If less than 35mm remains, start a new page.
    if (block.type === "heading") {
      if (willOverflow(35)) newPage();
      else y += 6; // extra spacing before headings mid-page

      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.setTextColor(0, 0, 0);
      doc.text(block.content.toUpperCase(), marginLeft, y);
      y += 2;

      // Underline beneath the heading
      doc.setDrawColor(0, 0, 0);
      doc.setLineWidth(0.25);
      doc.line(marginLeft, y, pageW - marginRight, y);
      y += 5;
    }

    // SUBHEADING — bold label within a section
    else if (block.type === "subheading") {
      // Require 20mm — heading + at least 2 body lines
      if (willOverflow(20)) newPage();
      else y += 3;

      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(0, 0, 0);
      doc.text(block.content, marginLeft, y);
      y += 5;
    }

    // PARAGRAPH — body text in Times Roman
    else if (block.type === "paragraph") {
      doc.setFont("times", "normal");
      doc.setFontSize(10);
      doc.setTextColor(0, 0, 0);

      const lines = doc.splitTextToSize(block.content, maxW);
      lines.forEach(line => {
        if (willOverflow(5)) newPage();
        doc.text(line, marginLeft, y);
        y += 5;
      });
      y += 2; // small gap after a paragraph
    }

    // LIST — numbered list items in Times Roman
    else if (block.type === "list") {
      doc.setFontSize(10);
      doc.setTextColor(0, 0, 0);

      block.items.forEach((item, i) => {
        const itemLines = doc.splitTextToSize(item, maxW - 8);

        // Treat each list item atomically — don't split a single item
        // across pages if we can avoid it. Check if the whole item fits.
        const itemHeight = itemLines.length * 5 + 2;
        if (willOverflow(itemHeight)) newPage();

        // Number in bold, content in normal weight
        doc.setFont("helvetica", "bold");
        doc.text(`${i + 1}.`, marginLeft, y);
        doc.setFont("times", "normal");

        itemLines.forEach((line, li) => {
          // If it is a very long item and we are mid-way through it,
          // still check for overflow on each sub-line.
          if (li > 0 && willOverflow(5)) newPage();
          doc.text(line, marginLeft + 7, y);
          y += 5;
        });
        y += 1;
      });
      y += 2;
    }

    // TABLE — minimal style with light gray header, no colored fills
    else if (block.type === "table") {
      // Give the table at least 25mm of space to start; if not, push to new page.
      if (willOverflow(25)) newPage();

      autoTable(doc, {
        startY: y,
        head:   [block.headers],
        body:   block.rows,
        margin: { left: marginLeft, right: marginRight },
        headStyles: {
          fillColor:   [230, 230, 230],  // light gray — professional, not colorful
          textColor:   [0, 0, 0],
          fontStyle:   "bold",
          font:        "helvetica",
          fontSize:    9,
          cellPadding: 3,
        },
        bodyStyles: {
          fontSize:    9,
          cellPadding: 2.5,
          textColor:   [0, 0, 0],
          font:        "times",
        },
        alternateRowStyles: {
          fillColor: [248, 248, 248],    // very subtle alternating row tint
        },
        tableLineColor: [180, 180, 180],
        tableLineWidth: 0.2,
        styles: {
          overflow:    "linebreak",
          lineColor:   [180, 180, 180],
          lineWidth:   0.1,
        },
        // After autoTable draws a page, update our y cursor.
        didDrawPage: (data) => {
          y = data.cursor.y + 6;
        },
      });

      // Sync y with where autoTable finished
      y = (doc.lastAutoTable?.finalY || y) + 8;
    }
  });

  // Save — no footer text is added anywhere in this function.
  doc.save(`${documentTitle.replace(/\s+/g, "_")}_${new Date().toISOString().slice(0, 10)}.pdf`);
}

// ─────────────────────────────────────────────────────────────────────────────
// LOGO COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
function ServicePilotLogo({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M32 4L8 14V32C8 45 18.5 56.5 32 60C45.5 56.5 56 45 56 32V14L32 4Z"
        fill="url(#sg)" stroke="rgba(0,0,0,0.08)" strokeWidth="1" />
      <path d="M36 14L26 34H34L28 50L44 28H36L42 14H36Z" fill="white" opacity="0.95" />
      <defs>
        <linearGradient id="sg" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#16a34a" />
          <stop offset="100%" stopColor="#15803d" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// NAVBAR
// ─────────────────────────────────────────────────────────────────────────────
function Navbar({ onGetStarted }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: scrolled ? "rgba(255,255,255,0.96)" : "rgba(255,255,255,0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
        transition: "background 0.3s ease",
      }}
    >
      <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <ServicePilotLogo size={32} />
          <span className="font-bold text-gray-900 text-lg" style={{ letterSpacing: "-0.02em" }}>
            ServicePilot
          </span>
        </div>
        <button onClick={onGetStarted}
          className="flex items-center gap-2 px-5 py-2 rounded-lg text-white text-sm font-semibold"
          style={{ background: "linear-gradient(135deg,#16a34a,#15803d)", boxShadow: "0 1px 3px rgba(22,163,74,0.3)" }}
        >
          Get Started <ArrowRight size={14} />
        </button>
      </div>
    </nav>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// HERO SECTION
// ─────────────────────────────────────────────────────────────────────────────
function HeroSection({ onGetStarted }) {
  return (
    <section className="pt-32 pb-24 px-6 text-center" style={{ background: "#ffffff" }}>
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-center mb-8">
          <div className="p-5 rounded-2xl"
            style={{ background: "linear-gradient(135deg,#f0fdf4,#dcfce7)", border: "1px solid #bbf7d0", boxShadow: "0 4px 24px rgba(22,163,74,0.12)" }}>
            <ServicePilotLogo size={72} />
          </div>
        </div>
        <div className="flex justify-center mb-6">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest"
            style={{ background: "#f0fdf4", border: "1px solid #86efac", color: "#15803d" }}>
            <Zap size={11} /> Multi-Agent ITIL Process Automation
          </span>
        </div>
        <h1 className="font-bold text-gray-900 mb-5 leading-none"
          style={{ fontSize: "clamp(2.2rem,5.5vw,4.5rem)", letterSpacing: "-0.03em", whiteSpace: "nowrap" }}>
          Automate to Accelerate IT.
        </h1>
        <p className="text-gray-500 mb-8 max-w-2xl mx-auto leading-relaxed" style={{ fontSize: "1.15rem" }}>
          Introducing Multi-Agent ITIL Automation.{" "}
          <span className="text-gray-700 font-medium">Ready for the Zero-Bottleneck Era.</span>
        </p>
        <div className="flex justify-center mb-12">
          <button onClick={onGetStarted}
            className="flex items-center gap-2.5 px-8 py-3.5 rounded-xl text-white font-semibold text-base"
            style={{ background: "linear-gradient(135deg,#16a34a,#15803d)", boxShadow: "0 4px 14px rgba(22,163,74,0.3)" }}>
            <Activity size={18} /> Analyze an Incident
          </button>
        </div>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span className="text-xs text-gray-400 mr-2">Integrates with</span>
          {["ServiceNow","Jira Service Management","Datadog"].map((n,i) => (
            <div key={i} className="px-4 py-2 rounded-lg text-gray-600 text-sm font-medium"
              style={{ background: "#f9fafb", border: "1px solid #e5e7eb" }}>{n}</div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Divider() {
  return <div className="max-w-7xl mx-auto px-6"><div style={{ height:"1px", background:"#f3f4f6" }} /></div>;
}

// ─────────────────────────────────────────────────────────────────────────────
// PIPELINE SECTION
// ─────────────────────────────────────────────────────────────────────────────
function PipelineSection() {
  const steps = [
    { icon:AlertTriangle, label:"Triage",     desc:"Raw incident data is ingested and classified by severity.", color:"#dc2626", bg:"#fef2f2", border:"#fecaca" },
    { icon:Search,        label:"Resolution", desc:"Semantic search across 100 historical incident resolutions.", color:"#2563eb", bg:"#eff6ff", border:"#bfdbfe" },
    { icon:FileText,      label:"RCA Report", desc:"Automated Root Cause Analysis document generation.", color:"#7c3aed", bg:"#f5f3ff", border:"#ddd6fe" },
    { icon:ClipboardList, label:"CAB RFC",    desc:"Change Advisory Board request document is finalized.", color:"#16a34a", bg:"#f0fdf4", border:"#bbf7d0" },
  ];
  return (
    <section className="py-24 px-6" style={{ background: "#ffffff" }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color:"#16a34a" }}>The Pipeline</p>
          <h2 className="font-bold text-gray-900" style={{ fontSize:"2.25rem", letterSpacing:"-0.02em" }}>End-to-End Automation Executes</h2>
          <p className="text-gray-500 mt-3 max-w-xl mx-auto">Four specialized AI agents running in sequence, each passing enriched context to the next.</p>
        </div>
        <div className="flex flex-col md:flex-row items-start justify-center gap-0">
          {steps.map((step,i) => (
            <div key={i} className="flex items-center">
              <div className="flex flex-col p-7 rounded-2xl" style={{ background:step.bg, border:`1px solid ${step.border}`, width:"200px", minHeight:"200px", flexShrink:0 }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 flex-shrink-0" style={{ background:"white", boxShadow:"0 1px 4px rgba(0,0,0,0.08)" }}>
                  <step.icon size={20} style={{ color:step.color }} />
                </div>
                <div className="text-xs font-bold uppercase tracking-widest mb-1.5" style={{ color:step.color }}>Step {i+1}</div>
                <div className="text-gray-900 font-semibold text-sm mb-2">{step.label}</div>
                <p className="text-gray-500 text-xs leading-relaxed">{step.desc}</p>
              </div>
              {i < steps.length-1 && (
                <div className="flex-shrink-0 mx-3 hidden md:flex items-center self-center" style={{ color:"#9ca3af" }}>
                  <ArrowRight size={20} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PROBLEM SECTION
// ─────────────────────────────────────────────────────────────────────────────
function ProblemSection() {
  const painPoints = [
    { label:"Manual Triage Delays",    icon:AlertTriangle },
    { label:"Inconsistent Severities", icon:Activity      },
    { label:"Lost Historical Context", icon:Database      },
    { label:"Slow RCA Drafting",       icon:FileText      },
    { label:"CAB Approval Friction",   icon:ClipboardList },
    { label:"SLA Breaches",            icon:Shield        },
  ];
  return (
    <section className="py-24 px-6" style={{ background:"#f9fafb" }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-5"
            style={{ background:"#fef2f2", border:"1px solid #fecaca", color:"#dc2626" }}>The Problem</span>
          <h2 className="font-bold text-gray-900 mb-4" style={{ fontSize:"2.25rem", letterSpacing:"-0.02em" }}>
            Legacy ITIL workflows equal{" "}<span style={{ color:"#16a34a" }}>Severe Bottlenecks</span>
          </h2>
          <p className="text-gray-600 max-w-xl mx-auto">
            Traditional incident management relies on manual effort at every stage — creating delays that compound into SLA breaches and revenue loss.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-10 items-start">
          <div className="rounded-2xl p-8" style={{ background:"#111827", border:"1px solid #1f2937" }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background:"#1f2937" }}>
                <Server size={18} className="text-gray-400" />
              </div>
              <div>
                <div className="text-white font-semibold text-sm">Incident Management System</div>
                <div className="text-gray-500 text-xs">Without ServicePilot</div>
              </div>
            </div>
            {[
              { label:"Triage",       width:"95%", color:"#dc2626", time:"45 min" },
              { label:"Root Cause",   width:"85%", color:"#f97316", time:"2.5 hrs" },
              { label:"RCA Drafting", width:"90%", color:"#eab308", time:"3 hrs"  },
              { label:"CAB Approval", width:"80%", color:"#6366f1", time:"1 day"  },
            ].map((item,i) => (
              <div key={i} className="mb-4">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-gray-400 text-xs font-medium">{item.label}</span>
                  <span className="text-xs font-semibold" style={{ color:item.color }}>{item.time}</span>
                </div>
                <div className="h-2 rounded-full" style={{ background:"#1f2937" }}>
                  <div className="h-2 rounded-full" style={{ width:item.width, background:item.color, opacity:0.8 }} />
                </div>
              </div>
            ))}
            <div className="mt-6 p-3 rounded-xl text-center text-sm font-medium" style={{ background:"#1f2937", color:"#6b7280" }}>
              Total resolution time: <span className="text-red-400 font-bold">6+ hours</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {painPoints.map((point,i) => (
              <div key={i} className="flex items-center gap-3 p-4 rounded-xl"
                style={{ background:"#ffffff", border:"1px solid #e5e7eb", boxShadow:"0 1px 3px rgba(0,0,0,0.05)" }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background:"#f3f4f6" }}>
                  <point.icon size={14} className="text-gray-600" />
                </div>
                <span className="text-gray-800 text-sm font-semibold">{point.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SOLUTIONS SECTION
// ─────────────────────────────────────────────────────────────────────────────
function SolutionsSection() {
  const agents = [
    { number:"01", title:"Agent 1: Triage",     sub:"Instant ITIL severity classification P1–P4.",       accent:"#16a34a", desc:"Analyzes raw incident descriptions and produces structured ITIL classifications — severity level, affected service, business impact, and resolver team assignment — in under 2 seconds." },
    { number:"02", title:"Agent 2: Resolution", sub:"BGE semantic search across 100+ incidents.",         accent:"#2563eb", desc:"Uses BAAI/BGE-Base dense retrieval embeddings to find the most semantically similar past incidents and synthesizes tailored resolution guidance grounded in historical data." },
    { number:"03", title:"Agent 3: RCA Report", sub:"Five Whys analysis and impact assessment.",          accent:"#7c3aed", desc:"Generates complete Root Cause Analysis documents with executive summary, incident timeline, Five Whys causal chain, preventive measures, and an action items table — 900+ words." },
    { number:"04", title:"Agent 4: CAB RFC",    sub:"Change Advisory Board request document.",            accent:"#16a34a", desc:"Produces formal ITIL Request for Change documents with risk assessment, implementation plan, rollback procedure, and stakeholder approval matrix — ready for CAB presentation." },
  ];
  return (
    <section className="py-24 px-6" style={{ background:"#ffffff" }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-5"
            style={{ background:"#f0fdf4", border:"1px solid #86efac", color:"#15803d" }}>Solutions</span>
          <h2 className="font-bold text-gray-900" style={{ fontSize:"2.25rem", letterSpacing:"-0.02em" }}>
            Evolving IT Service with{" "}<span style={{ color:"#16a34a" }}>4 Specialized AI Agents</span>
          </h2>
          <p className="text-gray-600 mt-3 max-w-xl mx-auto">
            Each agent owns a distinct phase of the ITIL incident lifecycle. State flows automatically — every agent builds on the previous one.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-12 items-start">
          <div className="md:sticky md:top-24">
            <div className="rounded-2xl p-9" style={{ background:"linear-gradient(160deg,#0f172a 0%,#1e3a5f 100%)", boxShadow:"0 20px 40px rgba(15,23,42,0.2)" }}>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background:"rgba(22,163,74,0.2)" }}>
                  <Brain size={20} style={{ color:"#86efac" }} />
                </div>
                <h3 className="text-white font-bold text-lg">LangGraph Pipeline</h3>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed mb-8">
                Four specialized LLM agents orchestrated by LangGraph, each owning a distinct phase of the ITIL incident lifecycle. The shared state object passes all accumulated context forward automatically at every step.
              </p>
              <div className="space-y-3">
                {[
                  { label:"LLaMA 3.3 70B via Groq",    icon:Zap,         color:"#fbbf24" },
                  { label:"BAAI/BGE-Base Embeddings",  icon:Brain,       color:"#60a5fa" },
                  { label:"ChromaDB Vector Store",     icon:Database,    color:"#a78bfa" },
                  { label:"100-Incident Knowledge Base",icon:Server,     color:"#86efac" },
                  { label:"FastAPI + React Frontend",  icon:Activity,    color:"#f87171" },
                ].map((tech,i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background:"rgba(255,255,255,0.06)" }}>
                      <tech.icon size={13} style={{ color:tech.color }} />
                    </div>
                    <span className="text-gray-300 text-sm">{tech.label}</span>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3 mt-8 pt-6" style={{ borderTop:"1px solid rgba(255,255,255,0.07)" }}>
                {[{val:"4",label:"Agents"},{val:"100+",label:"Incidents"},{val:"<20s",label:"Pipeline"}].map((s,i) => (
                  <div key={i} className="text-center">
                    <div className="text-2xl font-bold mb-0.5" style={{ color:"#86efac" }}>{s.val}</div>
                    <div className="text-gray-500 text-xs uppercase tracking-wider">{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="space-y-4">
            {agents.map((agent,i) => (
              <div key={i} className="p-6 rounded-2xl" style={{ background:"#ffffff", border:"1px solid #e5e7eb", boxShadow:"0 1px 4px rgba(0,0,0,0.05)" }}>
                <div className="flex items-start gap-4">
                  <div className="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded-lg flex-shrink-0"
                    style={{ background:"#f9fafb", border:"1px solid #e5e7eb", color:"#6b7280" }}>{agent.number}</div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-gray-900 text-base mb-0.5" style={{ letterSpacing:"-0.01em" }}>{agent.title}</h3>
                    <p className="text-sm font-semibold mb-2" style={{ color:agent.accent }}>{agent.sub}</p>
                    <p className="text-gray-600 text-sm leading-relaxed">{agent.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// FOOTER
// ─────────────────────────────────────────────────────────────────────────────
function Footer({ onGetStarted }) {
  return (
    <>
      <section className="py-24 px-6" style={{ background:"#0f172a" }}>
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-8"
            style={{ border:"1px solid rgba(22,163,74,0.3)", background:"rgba(22,163,74,0.08)", color:"#86efac" }}>
            <Brain size={12} /> Architectural Statement
          </div>
          <h2 className="text-white font-light leading-relaxed mb-6" style={{ fontSize:"1.6rem", maxWidth:"680px", margin:"0 auto 1.5rem" }}>
            Architected for scale. Leveraging{" "}
            <span className="font-semibold" style={{ color:"#86efac" }}>LangGraph</span>,{" "}
            <span className="font-semibold" style={{ color:"#93c5fd" }}>BGE semantic search</span>, and{" "}
            <span className="font-semibold" style={{ color:"#c4b5fd" }}>LLaMA 3.3</span>{" "}
            to synthesize complex ITIL resolutions in under 30 seconds.
          </h2>
          <button onClick={onGetStarted}
            className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-xl text-white font-semibold"
            style={{ background:"linear-gradient(135deg,#16a34a,#15803d)", boxShadow:"0 4px 14px rgba(22,163,74,0.3)" }}>
            <Activity size={18} /> Try ServicePilot Now
          </button>
        </div>
      </section>
      <footer className="py-6 text-center" style={{ background:"#020617", borderTop:"1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-gray-600 text-sm">
          © 2026 ServicePilot · Built by{" "}
          <span className="text-gray-400 font-medium">Thurubilli Sai Manoj</span>
          {" "}· Multi-Agent ITIL Process Automation · LangGraph · BGE-Base · LLaMA 3.3 70B
        </p>
      </footer>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ANALYZER MODAL — Complete with formatted document rendering + PDF export
// ─────────────────────────────────────────────────────────────────────────────
function AnalyzerModal({ onClose }) {
  const [description, setDescription] = useState("");
  const [examples,    setExamples]    = useState([]);
  const [isLoading,   setIsLoading]   = useState(false);
  const [result,      setResult]      = useState(null);
  const [error,       setError]       = useState(null);
  const [activeTab,   setActiveTab]   = useState(0);
  const [expandedInc, setExpandedInc] = useState(null);

  useEffect(() => {
    axios.get("/api/examples").then(r => setExamples(r.data.examples)).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!description.trim() || description.trim().length < 20) return;
    setIsLoading(true); setResult(null); setError(null);
    try {
      const r = await axios.post("/api/analyze", { incident_description: description.trim() });
      setResult(r.data); setActiveTab(0);
    } catch(e) {
      setError(e.response?.data?.detail || "Pipeline failed. Ensure the API server is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { icon:AlertTriangle, label:"Triage"    },
    { icon:Search,        label:"Incidents" },
    { icon:FileText,      label:"RCA"       },
    { icon:ClipboardList, label:"CAB RFC"   },
  ];

  return (
    <div className="fixed inset-0 z-[100] flex flex-col" style={{ background:"#0f172a" }}>

      {/* Header */}
      <div className="flex items-center justify-between px-8 py-4 flex-shrink-0"
        style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5">
          <ServicePilotLogo size={24} />
          <span className="text-white font-semibold">ServicePilot</span>
          <span className="text-gray-600 text-sm"> — ITIL Pipeline</span>
        </div>
        <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white"
          style={{ background:"#1e293b" }}>
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">

        {/* Input area — only shown before results */}
        {!result && (
          <div className="max-w-3xl mx-auto px-6 pt-12 pb-8">
            <h2 className="text-3xl font-bold text-white mb-2 text-center">Analyze an Incident</h2>
            <p className="text-gray-500 text-center mb-10">
              Describe any IT incident in plain English. All four agents run automatically.
            </p>
            {examples.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {examples.map(ex => {
                  const sev = SEV[ex.severity] || SEV.P1;
                  return (
                    <button key={ex.id} onClick={() => setDescription(ex.description)}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium ${sev.bg} ${sev.border} ${sev.color}`}>
                      {ex.title}
                    </button>
                  );
                })}
              </div>
            )}
            <textarea value={description} onChange={e => setDescription(e.target.value)} rows={7}
              placeholder="Example: Production Kubernetes cluster pods are in CrashLoopBackOff state. Payment service down. Missing Secret for gateway credentials..."
              className="w-full rounded-xl px-5 py-4 text-gray-200 placeholder-gray-600 text-sm leading-relaxed resize-none focus:outline-none mb-4"
              style={{ background:"#1e293b", border:"1px solid #334155" }}
            />
            {error && (
              <div className="p-3 rounded-lg text-red-400 text-sm mb-4"
                style={{ background:"#450a0a", border:"1px solid #7f1d1d" }}>{error}</div>
            )}
            <button onClick={handleAnalyze} disabled={isLoading || description.trim().length < 20}
              className="w-full py-4 rounded-xl font-semibold text-base text-white disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ background:"linear-gradient(135deg,#16a34a,#15803d)" }}>
              {isLoading
                ? <span className="flex items-center justify-center gap-3"><Loader2 size={18} className="animate-spin" />Running Pipeline — Agents 1 → 2 → 3 → 4...</span>
                : <span className="flex items-center justify-center gap-3"><Activity size={18} />Run ITIL Pipeline</span>
              }
            </button>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="max-w-2xl mx-auto px-6 pt-4 pb-12">
            <div className="rounded-2xl p-8 space-y-4" style={{ border:"1px solid #1e293b" }}>
              {[
                { icon:AlertTriangle, label:"Triage Agent",     desc:"Classifying severity and category..."    },
                { icon:Search,        label:"Resolution Agent", desc:"Searching knowledge base..."             },
                { icon:FileText,      label:"RCA Agent",        desc:"Generating root cause analysis..."       },
                { icon:ClipboardList, label:"CAB Agent",        desc:"Writing change request document..."      },
              ].map((s,i) => (
                <div key={i} className="flex items-center gap-4 p-3 rounded-xl" style={{ background:"#1e293b" }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background:"#0f172a" }}>
                    <s.icon size={14} className="text-green-400" />
                  </div>
                  <div className="flex-1">
                    <div className="text-white text-sm font-medium">{s.label}</div>
                    <div className="text-gray-500 text-xs">{s.desc}</div>
                  </div>
                  <Loader2 size={12} className="text-green-400 animate-spin" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {result && !isLoading && (() => {
          // Parse both documents once so the same parsed data is
          // used for both rendering and PDF generation
          const rcaBlocks = parseDocument(result.rca_report);
          const cabBlocks = parseDocument(result.cab_document);

          return (
            <div className="max-w-5xl mx-auto px-6 pb-16">

              {/* Success banner */}
              <div className="flex items-center gap-3 p-4 rounded-xl mb-6"
                style={{ background:"rgba(22,163,74,0.1)", border:"1px solid rgba(22,163,74,0.2)" }}>
                <CheckCircle size={16} className="text-green-400" />
                <span className="text-green-300 text-sm font-medium">
                  Pipeline completed in {result.execution_time_sec}s
                </span>
                <button onClick={() => { setResult(null); setDescription(""); }}
                  className="ml-auto text-xs text-gray-500 hover:text-gray-300">
                  New Incident
                </button>
              </div>

              {/* Metrics row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                {[
                  { label:"Severity",   value:result.triage.severity, color:SEV[result.triage.severity]?.color||"text-gray-300" },
                  { label:"Category",  value:result.triage.category, color:"text-blue-400" },
                  { label:"Resolution",value:result.triage.estimated_resolution_time.split(",")[0], color:"text-cyan-400" },
                  { label:"Confidence",value:result.synthesis.confidence_level, color:"text-green-400" },
                ].map((m,i) => (
                  <div key={i} className="rounded-xl p-4 text-center"
                    style={{ background:"#1e293b", border:"1px solid #334155" }}>
                    <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">{m.label}</div>
                    <div className={`font-bold text-lg ${m.color}`}>{m.value}</div>
                  </div>
                ))}
              </div>

              {/* Tab navigation */}
              <div className="flex gap-1 p-1 rounded-xl mb-6" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                {tabs.map((tab,i) => (
                  <button key={i} onClick={() => setActiveTab(i)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      activeTab===i ? "text-white" : "text-gray-400 hover:text-gray-200"
                    }`}
                    style={ activeTab===i ? { background:"#16a34a" } : {} }>
                    <tab.icon size={13} />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* ── TAB 0: Triage ── */}
              {activeTab===0 && (
                <div className="space-y-4">
                  <div className={`p-6 rounded-xl border ${SEV[result.triage.severity]?.bg} ${SEV[result.triage.severity]?.border}`}>
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-3 h-3 rounded-full ${SEV[result.triage.severity]?.dot}`} />
                      <span className={`text-2xl font-bold ${SEV[result.triage.severity]?.color}`}>{result.triage.severity}</span>
                      <span className="text-gray-700">— {result.triage.category}</span>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {[
                        ["Affected Service", result.triage.affected_service],
                        ["Recommended Team", result.triage.recommended_team],
                        ["Est. Resolution",  result.triage.estimated_resolution_time],
                        ["Category",         result.triage.category],
                      ].map(([k,v]) => (
                        <div key={k}>
                          <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">{k}</div>
                          <div className="text-gray-900 font-medium text-sm">{v}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-5 rounded-xl" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                      <div className="text-orange-400 text-xs font-semibold uppercase tracking-wider mb-3">Business Impact</div>
                      <p className="text-gray-300 text-sm leading-relaxed">{result.triage.business_impact}</p>
                    </div>
                    <div className="p-5 rounded-xl" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                      <div className="text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-3">Initial Diagnosis</div>
                      <p className="text-gray-300 text-sm leading-relaxed">{result.triage.initial_diagnosis}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 1: Similar Incidents ── */}
              {activeTab===1 && (
                <div className="space-y-4">
                  {result.similar_incidents.map((inc,i) => {
                    const isev = SEV[inc.severity]||SEV.P4;
                    const open = expandedInc===i;
                    return (
                      <div key={i} className="rounded-xl overflow-hidden" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                        <button onClick={() => setExpandedInc(open?null:i)}
                          className="w-full p-5 flex items-center gap-4 hover:bg-white/5 text-left">
                          <span className={`text-xl font-bold ${isev.color} w-8`}>#{i+1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="text-white text-sm font-medium truncate">[{inc.incident_id}] {inc.title}</div>
                            <div className="flex gap-3 mt-1 text-xs text-gray-500">
                              <span className={isev.color}>{inc.severity}</span>
                              <span>{inc.category}</span>
                              <span>{inc.resolved_in_minutes} min</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ background:"#334155" }}>
                              <div className="h-full rounded-full" style={{ width:`${inc.similarity_score}%`, background:"#16a34a" }} />
                            </div>
                            <span className="text-green-400 text-xs w-10">{inc.similarity_score}%</span>
                          </div>
                        </button>
                        {open && (
                          <div className="px-5 pb-5 pt-4" style={{ borderTop:"1px solid #334155" }}>
                            <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">Root Cause</div>
                            <p className="text-gray-300 text-sm mb-3">{inc.root_cause}</p>
                            <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Resolution Steps</div>
                            <div className="space-y-1">
                              {inc.resolution_steps.filter(s=>s.trim()).map((s,j) => (
                                <div key={j} className="flex gap-2 text-sm text-gray-300">
                                  <span className="text-green-500 flex-shrink-0">›</span>{s}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  <div className="p-5 rounded-xl" style={{ background:"rgba(22,163,74,0.05)", border:"1px solid rgba(22,163,74,0.2)" }}>
                    <div className="text-green-400 text-xs font-semibold uppercase tracking-wider mb-3">
                      LLM Synthesis — Ref: {result.synthesis.primary_reference}
                    </div>
                    <div className="space-y-2">
                      {result.synthesis.recommended_steps.filter(s=>s.trim()).map((s,i) => (
                        <div key={i} className="flex gap-3 text-sm">
                          <span className="text-green-500 font-bold w-5 flex-shrink-0">{i+1}.</span>
                          <span className="text-gray-300">{s}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 2: RCA Report — fully formatted ── */}
              {activeTab===2 && (
                <div>
                  {/* Toolbar */}
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <span className="text-white font-semibold text-sm">Root Cause Analysis Report</span>
                      <span className="text-gray-500 text-xs ml-3">{result.rca_report.split(" ").length} words</span>
                    </div>
                    {/* PDF download — generates a proper structured PDF */}
                    <button
                      onClick={() => generatePDF(rcaBlocks, "Root Cause Analysis Report", description)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium"
                      style={{ background:"linear-gradient(135deg,#16a34a,#15803d)", boxShadow:"0 2px 8px rgba(22,163,74,0.3)" }}
                    >
                      <Download size={13} /> Download PDF
                    </button>
                  </div>

                  {/* Formatted document body */}
                  <div className="rounded-xl p-8" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                    <DocumentRenderer blocks={rcaBlocks} />
                  </div>
                </div>
              )}

              {/* ── TAB 3: CAB RFC — fully formatted ── */}
              {activeTab===3 && (
                <div>
                  {/* Toolbar */}
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <span className="text-white font-semibold text-sm">Change Advisory Board — Request for Change</span>
                      <span className="text-gray-500 text-xs ml-3">{result.cab_document.split(" ").length} words</span>
                    </div>
                    {/* PDF download */}
                    <button
                      onClick={() => generatePDF(cabBlocks, "CAB Request for Change", description)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium"
                      style={{ background:"linear-gradient(135deg,#16a34a,#15803d)", boxShadow:"0 2px 8px rgba(22,163,74,0.3)" }}
                    >
                      <Download size={13} /> Download PDF
                    </button>
                  </div>

                  {/* Formatted document body */}
                  <div className="rounded-xl p-8" style={{ background:"#1e293b", border:"1px solid #334155" }}>
                    <DocumentRenderer blocks={cabBlocks} />
                  </div>
                </div>
              )}

            </div>
          );
        })()}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [showAnalyzer, setShowAnalyzer] = useState(false);

  useEffect(() => {
    document.body.style.overflow = showAnalyzer ? "hidden" : "auto";
    return () => { document.body.style.overflow = "auto"; };
  }, [showAnalyzer]);

  return (
    <div style={{ fontFamily:"'Inter',system-ui,sans-serif", background:"#ffffff" }}>
      <Navbar          onGetStarted={() => setShowAnalyzer(true)} />
      <HeroSection     onGetStarted={() => setShowAnalyzer(true)} />
      <Divider />
      <PipelineSection />
      <Divider />
      <ProblemSection />
      <Divider />
      <SolutionsSection />
      <Footer          onGetStarted={() => setShowAnalyzer(true)} />

      <AnimatePresence>
        {showAnalyzer && (
          <motion.div
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
            transition={{ duration:0.15 }}
          >
            <AnalyzerModal onClose={() => setShowAnalyzer(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}