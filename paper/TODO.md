# Research Paper Open Action Items (TODO.md)

This checklist tracks author-specific fields and pre-submission tasks for the manuscript:
**"Beyond Centroid Tripwires: Robust Multi-Class Directional Vehicle Counting in Heterogeneous Traffic Using Modern YOLO and ByteTrack"**

---

### 1. Author Metadata and Affiliations (High Priority)
- [ ] **Author Names & Affiliations** in `paper/main.tex`:
  - Replace `\todo{Author One}` with the principal investigator / student name.
  - Replace `\todo{Author Two}` with co-authors / faculty advisor / research mentor.
  - Insert correct Department, University/Institution name, City, Country, and official academic email addresses.
- [ ] **GitHub Repository URL**:
  - In `paper/main.tex` under *Data and Software Availability*, verify or update `https://github.com/Dream-blue-wasTaken/Traffic_detection`.

---

### 2. Back Matter and Funding (Medium Priority)
- [ ] **Acknowledgments**:
  - In `paper/main.tex`, replace `\todo{Acknowledge departmental support...}` with specific research grants, university computing clusters, or lab sponsorships (or remove the section if submitting to a double-blind review track).

---

### 3. Target Venue and Formatting Adjustments (Medium Priority)
- [ ] **Venue Template**:
  - The default is set to two-column IEEE Conference (`\documentclass[conference]{IEEEtran}`).
  - If submitting to an IEEE Transactions/Journal: change to `\documentclass[journal]{IEEEtran}`.
  - If submitting for review with line numbers: add `\usepackage{lineno}` and `\linenumbers`.
- [ ] **Page Limit**:
  - Standard IEEE conference submissions typically require 6 to 8 pages. The current draft spans ~6-7 pages with figures and tables.

---

### 4. Overleaf Compilation Instructions
1. Compress the `paper/` directory into a zip archive (`paper.zip`).
2. Log into [Overleaf](https://www.overleaf.com) $\rightarrow$ Click **New Project** $\rightarrow$ **Upload Project** $\rightarrow$ Select `paper.zip`.
3. Verify that the compiler is set to **pdfLaTeX** and the main document is set to `main.tex`.
4. Click **Recompile** (compile twice to resolve citation cross-references and figure labels).

---

### 5. Ethical and AI-Assisted Writing Disclosure Reminder
- IEEE policy mandates that authors take full scientific responsibility for the accuracy and integrity of their manuscript. If required by your target venue, include an AI-assisted writing disclosure in the manuscript or submission form according to IEEE author guidelines.
