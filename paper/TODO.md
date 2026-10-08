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

### 4. Validation Split Sizes (High Priority — reviewer flagged)
- [ ] **Add exact train/val split sizes** to Table I or the Experiment 1 text. The current text references this but the table doesn't include it. Report the number of training images and validation images used in the Auto-Rickshaw-Annotation-7 split.

---

### 5. Future Experimental Work (Critical — reviewer flagged)
The following experiments were identified as necessary for a full validation paper:
- [ ] **Ground-truth counting evaluation**: Multiple clips, manual event annotation, Bland-Altman/F1 analysis
- [ ] **Ablation studies**: centroid vs. bottom-center, fallback on/off, voting vs. last-frame class, ByteTrack vs. SORT
- [ ] **GMC isolation ablation**: Disable only GMC within BoT-SORT to isolate its throughput cost
- [ ] **Ensemble benchmarking**: Dual-model ensemble counting accuracy and throughput
- [ ] **Verify claims about [1]**: Cross-check ~90% accuracy, 1.7h/hr processing, wall-clock binning against the original Majumder & Wilmot paper

---

### 6. Overleaf Compilation Instructions
1. Compress the `paper/` directory into a zip archive (`paper.zip`).
2. Log into [Overleaf](https://www.overleaf.com) → Click **New Project** → **Upload Project** → Select `paper.zip`.
3. Verify that the compiler is set to **pdfLaTeX** and the main document is set to `main.tex`.
4. Click **Recompile** (compile twice to resolve citation cross-references and figure labels).

---

### 7. Ethical and AI-Assisted Writing Disclosure Reminder
- IEEE policy mandates that authors take full scientific responsibility for the accuracy and integrity of their manuscript. If required by your target venue, include an AI-assisted writing disclosure in the manuscript or submission form according to IEEE author guidelines.
