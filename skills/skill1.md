---
name: codebase-to-ieee-paper
description: Turn a software codebase into a research paper written in LaTeX using the IEEE conference/journal template (IEEEtran), ready to upload to Overleaf. Use this skill whenever the user wants to write a paper, article, manuscript, or publication based on a repository, project, or source code, mentions IEEE format, IEEEtran, Overleaf, arXiv, JOSS, or asks to "document my code as a paper", "write up my system", or "generate a research paper from my project", even if they do not say "LaTeX". Also use it when the user has code plus experiment results and needs the Method, Evaluation, or Related Work sections drafted.
---

# Codebase to IEEE Paper

Produce a well-structured, honest, IEEE-formatted LaTeX paper from a codebase. The output is a folder of `.tex` and `.bib` files the user can zip and upload to Overleaf.

## Core rules (read first)

1. **Never fabricate.** No invented results, benchmarks, datasets, baselines, citations, author names, or affiliations. Every number in the paper must come from (a) output the user pasted or a file they uploaded, (b) a script you ran in this session, or (c) the code itself (e.g., a constant, a complexity bound you can derive). If a number is missing, write `\todo{...}` and list it in the TODO report.
2. **Never invent citations.** Only cite papers you have verified via web search or that the user supplied. If you cannot verify, leave a `\cite{TODO-topic}` placeholder and a note. A paper with a few gaps is better than one with fake references.
3. **A codebase is not a contribution.** The paper needs a claim of what is new or useful, evidence for it, and context (related work). Identify these with the user before writing prose.
4. **Describe what the code actually does**, not what a README claims. Read the source and verify claims against it.
5. **Be upfront about limitations.** Include a real Limitations paragraph based on what you observed in the code (missing tests, untested scale, assumptions, known bugs).
6. **AI-assistance disclosure.** Remind the user that many venues (including IEEE) require disclosing AI-assisted writing, and that they must review and take responsibility for all content. Do not add authors for AI.

## Workflow

### Phase 0: Intake

Ask only what you cannot infer from the code. Keep it to a few questions at most:

- Target venue or type: conference, journal, arXiv preprint, or JOSS-style software paper? (Default: IEEE conference, two-column.)
- Field and intended audience.
- Authors, affiliations, emails (or leave as placeholders).
- Does the user already have results, benchmarks, or logs? If so, get them.
- Page limit, if any.

If the user does not answer, proceed with defaults and state your assumptions in one line.

### Phase 1: Understand the codebase

Explore before writing:

1. List the tree. Read README, config files, dependency manifests (`requirements.txt`, `package.json`, `pyproject.toml`, `Cargo.toml`, etc.), entry points, and tests.
2. Identify: purpose, main modules, data flow, key algorithms, data structures, external dependencies, supported inputs/outputs, and how it is run.
3. For large repos, summarize per module, then synthesize. Focus on the core 20% that carries the contribution.
4. Check for existing evaluation: tests, benchmarks, `results/`, notebooks, logs, CI configs.
5. Note the license, language(s), size (rough LOC), and commit history signals (e.g., maturity).

Produce an internal summary: *What problem does it solve? What is the approach? What is novel or distinctive? What evidence exists?*

### Phase 2: Define the contribution and paper type

Propose to the user, in a short message:

- **Paper type**: software/tool paper, systems/methods paper, or applied case study.
- **Working title** (2 or 3 options).
- **Problem statement** (1 or 2 sentences).
- **Contributions** (3 bullets maximum, each verifiable from code or results).
- **Claimed novelty vs. existing tools** (to be confirmed by literature search).

Wait for the user's confirmation or correction if the contribution is unclear. If the project is a plain utility with no novelty, say so honestly and steer toward a software/tool paper or an applied case study.

### Phase 3: Evaluation plan

Reviewers weigh evidence heavily. Based on the paper type:

- **Methods/systems**: define research questions (RQ1, RQ2...), metrics, baselines, datasets, hardware/software environment, and number of runs.
- **Software/tool**: describe functionality, usage examples, performance sanity checks, test coverage, and comparison with similar tools qualitatively.
- **Case study**: describe the scenario, data, outcomes, and lessons.

Then:

- If the user has results, use them as provided and cite their source file or log.
- If not, offer to write benchmark scripts (put them in `paper/experiments/`) and tell the user to run them and send back the output. If you have a code execution environment and the repo can run safely, run them yourself and report exactly what happened, including failures.
- Record environment details (OS, CPU, RAM, language version, library versions, random seeds) for the Experimental Setup section.
- Generate figures from real data with a script (matplotlib, pgfplots). Save as PDF/vector where possible.

### Phase 4: Related work

1. Search for the topic using web search (Google Scholar, Semantic Scholar, arXiv, IEEE Xplore, ACM DL).
2. Collect 15 to 40 relevant references for a full paper (fewer for short papers). Prefer peer-reviewed or well-established sources, and include recent work (last 3 to 5 years).
3. For each, verify the title, authors, venue, and year from the source page. Record the DOI or URL when available.
4. Write BibTeX entries only from verified metadata. Use consistent keys (`lastnameYEARkeyword`).
5. Organize Related Work by theme, not by paper. End with a sentence positioning this work against the closest alternatives.
6. Quote sparingly. Paraphrase and cite.

If search is unavailable, create `references.bib` with only user-provided entries plus clearly marked `TODO` placeholders, and tell the user.

### Phase 5: Write the LaTeX

Create this folder structure:

```
paper/
├── main.tex
├── references.bib
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── method.tex
│   ├── evaluation.tex
│   ├── discussion.tex
│   └── conclusion.tex
├── figures/
├── experiments/        (scripts and raw outputs, optional)
└── TODO.md             (open items for the author)
```

For short papers, a single `main.tex` is fine. Default to the split structure for anything over four pages.

#### main.tex skeleton (IEEE conference)

```latex
\documentclass[conference]{IEEEtran}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{listings}
\usepackage{url}
\usepackage[hidelinks]{hyperref}

\newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}

\lstset{
  basicstyle=\ttfamily\footnotesize,
  breaklines=true,
  frame=single,
  columns=fullflexible
}

\begin{document}

\title{Your Paper Title Here}

\author{
  \IEEEauthorblockN{First Author}
  \IEEEauthorblockA{\textit{Department} \\
  \textit{Institution}\\
  City, Country \\
  email@example.com}
  \and
  \IEEEauthorblockN{Second Author}
  \IEEEauthorblockA{\textit{Department} \\
  \textit{Institution}\\
  City, Country \\
  email@example.com}
}

\maketitle

\begin{abstract}
\input{sections/abstract}
\end{abstract}

\begin{IEEEkeywords}
keyword one, keyword two, keyword three
\end{IEEEkeywords}

\input{sections/introduction}
\input{sections/related_work}
\input{sections/method}
\input{sections/evaluation}
\input{sections/discussion}
\input{sections/conclusion}

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
```

Variants:
- **Journal / Transactions**: `\documentclass[journal]{IEEEtran}`.
- **Review draft**: `\documentclass[conference,draft]{IEEEtran}` or `[journal,onecolumn,draftcls]`.
- **Not IEEE**: if the user switches venue (ACM, NeurIPS, Springer LNCS), tell them to use that venue's official Overleaf template and adapt the section files, which stay the same.

Overleaf has an official "IEEE Conference Template" and "IEEE Journal" template; `IEEEtran.cls` is built in to Overleaf's TeX Live, so no extra files are needed when compiling there.

#### Section guidance

**Abstract** (150 to 250 words, one paragraph, no citations, no math if avoidable): problem, gap, approach, key results with real numbers, takeaway. Write it last.

**Introduction** (about 1 to 1.5 columns): motivation and problem; why existing approaches fall short (backed by citations); your approach in one paragraph; a bulleted contribution list (3 items max); paper roadmap in one sentence.

**Related Work**: thematic paragraphs, each ending with how this work differs. Verified citations only.

**Method / System Design / Architecture**: derive this directly from the code.
- Start with an overview figure (architecture or pipeline diagram). Create it with TikZ or a script. Do not reference a figure you have not made.
- Describe components in the order data flows through them.
- Present key algorithms with the `algorithm` and `algorithmic` environments or pseudocode, simplified from the real implementation.
- State assumptions, complexity (only if derivable), and design trade-offs and why they were made, if the code or comments justify it. Otherwise mark `\todo{rationale}`.
- Use short code listings only when they illustrate something that prose cannot. Keep to 10 to 15 lines.
- Mention implementation details: language, main libraries with versions, repository URL, license.

**Evaluation**:
- Experimental setup (hardware, software, datasets, baselines, metrics, runs, seeds).
- Results as tables (`booktabs`) and figures, each referenced in the text and interpreted: what does the result show, and why?
- Include variance or confidence intervals if multiple runs exist.
- Do not claim statistical significance without a test.
- Include an ablation or sensitivity analysis if the data supports it.

**Discussion**: interpretation, lessons learned, **Threats to Validity / Limitations**, and ethical considerations if relevant.

**Conclusion**: restate contributions and results without new claims; give 2 or 3 concrete future work items.

**Optional back matter**: Acknowledgment (funding, only if provided), Data and Code Availability (repo URL, archive DOI, such as Zenodo, if the user has one). Avoid anonymity-breaking info if the venue is double-blind.

#### Writing style

- Precise, neutral, past tense for what was done, present tense for what the paper does or what the system does.
- Define acronyms on first use. Use "we" for the authors.
- No marketing language ("revolutionary", "state-of-the-art" without evidence, "seamless").
- Every claim is supported by a citation, a result, or the code.
- Keep paragraphs focused, one idea each.
- Number figures and tables, caption them fully, reference them with `\ref` and `Fig.~\ref{}` / `Table~\ref{}`.
- Use `~` before `\cite` and `\ref` to avoid line breaks (`text~\cite{key}`).

#### Placeholders

Use `\todo{...}` for any missing fact. Examples: `\todo{insert speedup over baseline from run logs}`, `\todo{confirm dataset license}`. Never fill a gap with a plausible guess.

### Phase 6: Deliverables

1. Write all files under `paper/` and present them to the user. If a single file is easier, still provide `main.tex` plus `references.bib` at minimum.
2. If possible, create a zip: `paper.zip`.
3. If a LaTeX compiler (`pdflatex`, `latexmk`) is available in the environment, compile and fix errors; check for undefined references and citations. If not, review by eye for common errors (unbalanced braces, missing `\end{}`, undefined labels) and say that you could not compile.
4. Give the user short Overleaf instructions:
   - Overleaf → New Project → Upload Project → select `paper.zip`.
   - Set the compiler to pdfLaTeX and the main document to `main.tex` (Menu).
   - Alternatively, start from Overleaf's "IEEE Conference Template", then paste in the section files.
   - Compile twice (or let Overleaf do it) to resolve references and bibliography.
5. Write `TODO.md` listing every `\todo`, every unverified citation, every missing result, and every assumption made. Summarize it in the chat reply, ranked by importance.

### Phase 7: Quality check before handing over

Go through this list and fix or flag:

- [ ] Contribution is clear in the abstract, introduction, and conclusion, and the three agree.
- [ ] Every number traces to a result, log, or the code.
- [ ] Every citation is verified; no hallucinated references; all `\cite` keys exist in the `.bib`.
- [ ] Every figure and table is referenced in the text and has a caption.
- [ ] Method section matches the real code (names, steps, parameters).
- [ ] Limitations are stated honestly.
- [ ] Terminology is consistent (same name for the same component throughout).
- [ ] No leftover template text ("Your Paper Title Here", sample authors).
- [ ] Page count is within the limit, if one was given.
- [ ] Code and data availability statement is present or intentionally omitted.
- [ ] Reminder given about AI-use disclosure and about the author's responsibility to review.

## Handling common situations

- **No experiments exist**: say so plainly. Offer (a) a benchmark plan with scripts, (b) a software/tool paper that does not rely on performance claims, or (c) a case-study framing. Do not make up results.
- **Huge codebase**: ask the user which component carries the contribution; write about that and mention the rest briefly.
- **Multiple languages or microservices**: use a layered architecture figure and describe each layer in a paragraph.
- **Proprietary or sensitive code**: ask before including listings or details; abstract away secrets, keys, and internal URLs.
- **Machine learning projects**: include dataset description and splits, model architecture, hyperparameters, training setup, metrics, baselines, seeds, and compute budget. Report mean ± std over multiple seeds when available.
- **User wants a different template**: keep section files; swap `main.tex` for the venue's template and adjust the bibliography style.
- **Overleaf compile errors**: ask for the log, identify the first error (later ones often cascade), and fix it.
- **Page limit exceeded**: cut in this order: redundant text, secondary results moved to a repository or appendix, long listings, then figure sizes.

## What to say when finished

Keep the final message short:

1. What you produced and where (files).
2. The paper's claimed contribution in one sentence.
3. The top open items from `TODO.md` (what the author must supply or verify).
4. How to open it in Overleaf.
5. The AI-disclosure reminder.