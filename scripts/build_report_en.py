"""Build the English copy of the final assignment report."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "report" / "figures"
OUT = ROOT / "report" / "Assignment1_Report_EN.docx"


def set_run_font(run, *, bold=False, italic=False, size=11):
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")


def add_para(doc, text, *, bold=False, italic=False, size=11, align="justify",
             space_after=6, space_before=0, first_line=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if first_line and align == "justify":
        pf.first_line_indent = Cm(0.75)
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, bold=bold, italic=italic, size=size)
    return p


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(run, bold=True, size=14 if level == 1 else 12)
    h.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    return h


def add_caption(doc, text):
    return add_para(doc, text, italic=True, size=10, align="center",
                    space_before=4, space_after=10, first_line=False)


def add_figure(doc, path: Path, width_cm=12.0, caption: str = ""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        add_caption(doc, caption)


def add_table(doc, headers, rows, caption: str):
    add_caption(doc, caption)
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        set_run_font(run, bold=True, size=9)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            set_run_font(run, size=9)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    add_para(doc, "Assignment 1 – Final Report", bold=True, size=16,
             align="center", first_line=False, space_after=6)
    add_para(doc, "Customer Order Scheduling in a Permutation Flow Shop",
             bold=True, size=14, align="center", first_line=False, space_after=6)
    add_para(doc,
             "Comparison of Simulated Annealing with an Iterated Greedy Algorithm "
             "(Hoffmann, Neufeld, Buscher, 2025)",
             italic=True, size=11, align="center", first_line=False, space_after=12)
    add_para(doc, "Course: Metaheuristics and Nature-Inspired Optimisation Algorithms (MPO)",
             size=10, align="center", first_line=False, space_after=2)
    add_para(doc, "Variant B – own solution method",
             size=10, align="center", first_line=False, space_after=2)
    add_para(doc, "[Insert team member names]",
             italic=True, size=10, align="center", first_line=False, space_after=18)

    add_heading(doc, "1 Abstract", 1)
    add_para(
        doc,
        "This report addresses customer order scheduling (COSP) in a permutation flow shop "
        "as studied by Hoffmann, Neufeld and Buscher [1]. Each of n orders consists of o "
        "jobs processed on m machines; an order is complete only when its last job finishes, "
        "and the objective is to minimise the sum of order completion times. As our own "
        "method we design and implement simulated annealing (SA) on the same permutation "
        "representation used by IGA-String. We re-implemented that baseline from the "
        "authors’ pseudocode and compared it with SA on the same instances and the same "
        "computational budget. SA parameters were set on tuning instances; the main "
        "experiments use a budget of 190,000 full-schedule evaluations per run. On the "
        "Small testbed (540 instances, 5,400 runs) SA reached a mean RPD of 0.008% against "
        "0.044% for IGA-String (one-sided Wilcoxon test, p ≈ 1.6·10⁻⁸). On the Big "
        "testbed (135 instances, 1,350 runs) the RPDs were 0.389% and 0.907% "
        "(p ≈ 3.3·10⁻¹⁶). Follow-up experiments show that on 500-job instances the "
        "ranking at 190,000 evaluations is budget-sensitive, and that SA’s advantage "
        "does not depend on starting from MultipleNEH."
    )

    add_heading(doc, "2 Problem description and significance", 1)
    add_para(
        doc,
        "Manufacturers often ship all items of a customer order together. An order can "
        "therefore leave only when every item is finished; finishing one job early does "
        "not help if another finishes late. COSP captures this dependence by scoring "
        "complete orders rather than individual jobs [1, 3]."
    )
    add_para(
        doc,
        "Paper [1] studies COSP in a permutation flow shop with m machines: every job "
        "visits the machines in the same order, and the job sequence is identical on all "
        "machines. In three-field notation the problem is Fm → 0 | prmu | ΣCi. It is "
        "NP-hard already for two machines [1, Proposition 1], which follows from the "
        "NP-hardness of F2 || ΣCj [4] and motivates heuristics."
    )
    add_para(
        doc,
        "The criterion differs from makespan: a short makespan need not be attractive if "
        "most customers wait until nearly the end of production. The model has no due "
        "dates or priorities, so the result cannot be read as tardiness minimisation. "
        "The problem is a constrained, single-objective, discrete minimisation task. It "
        "is static and deterministic, and white-box because both the objective and the "
        "feasibility conditions are explicit."
    )

    add_heading(doc, "3 Formulation of the optimisation problem", 1)
    add_heading(doc, "3.1 Decision variables and the authors’ model", 2)
    add_para(
        doc,
        "The input consists of n orders with o jobs each, m machines and processing "
        "times p_{i j k} of job j of order i on machine k; the total number of jobs is "
        "N = n·o. The authors formulate a mixed-integer nonlinear programme (MINLP) "
        "with a binary variable x_{i j π} equal to 1 when job (i, j) occupies position "
        "π of the common sequence, and continuous variables for job and order "
        "completion times [1, Sections 3.1–3.2]. The constraints assign every job to "
        "exactly one position and every position to exactly one job; nonlinearity "
        "comes from products of decision and timing variables."
    )
    add_heading(doc, "3.2 Permutation representation and objective", 2)
    add_para(
        doc,
        "The assignment x is equivalent to a permutation Π of all N pairs (i, j); the "
        "candidate space has size N!. IGA-String and our SA both use this representation, "
        "so no transformation between methods is required. Let π_r be the job in "
        "position r and C(π_r, k) its completion time on machine k. For r = 1,…,N and "
        "k = 1,…,m,"
    )
    add_para(
        doc,
        "C(π_r, 1) = C(π_{r−1}, 1) + p(π_r, 1),    "
        "C(π_r, k) = max{ C(π_{r−1}, k), C(π_r, k−1) } + p(π_r, k)  (k ≥ 2),",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "with C(π_0, ·) = 0. Order i is complete when its last job leaves the last "
        "machine: Ci = max{ C(π_r, m) | π_r belongs to order i }. The objective is "
        "F(Π) = Σ_i Ci. Evaluating a candidate costs O(N·m) operations. By Lemma 2 of "
        "the paper there always exists an optimal schedule without deliberately "
        "inserted idle time [1]. Every permutation is feasible, so no repair or "
        "penalty mechanism is needed."
    )
    add_heading(doc, "3.3 Worked counter-example", 2)
    add_para(
        doc,
        "The counter-example in [1, Table 4] has n = 2, o = 2, m = 2. For the schedule "
        "(2,2), (1,2), (1,1), (2,1) the recurrence gives completion times 18, 20, 31 "
        "and 48 on the second machine, hence C₁ = 31, C₂ = 48 and F = 79, which is "
        "optimal. The best schedule with contiguous order blocks has value 80 "
        "[1, Table 5]; contiguous blocks therefore cannot be required (Lemma 3). We "
        "verified these values independently and use them as unit tests."
    )

    add_heading(doc, "4 The authors’ method", 1)
    add_para(
        doc,
        "The authors solve the MINLP with Gurobi (a reference for small instances) and "
        "propose four heuristics based on the iterated greedy algorithm (IGA) [1, 5], "
        "which seek good solutions within a limited time without an optimality "
        "guarantee. All variants start from MultipleNEH [1, Alg. 1]: first NEH on the "
        "jobs of each order (sorted by ascending total processing time—unlike "
        "classical NEH, which sorts descending—and inserted by the order’s makespan), "
        "then NEH on whole orders (inserted by F). Makespan is only an auxiliary "
        "criterion here."
    )
    add_para(
        doc,
        "IGA-String modifies a single permutation of all N jobs. Each iteration "
        "removes d random jobs, sorts them by ascending total processing time and "
        "reinserts each at the position with the lowest F; the MultipleInsertion "
        "local search then moves a random job to its best position ⌊z·d/d_min⌋ "
        "times. A better schedule is always accepted; a worse one is accepted with "
        "probability"
    )
    add_para(
        doc,
        "q ≤ exp( −y · (d_min / d) · (F(Π′) − F(Π)) / F(Π) ),",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "where q ∼ U[0,1]. After an improvement d is reset to d_min; otherwise it "
        "increases up to ⌊N/2⌋. The rule resembles the Metropolis criterion of SA "
        "[7], but the role of temperature is played by the adaptive d rather than a "
        "cooling schedule. A drawback is the cost of an iteration: every trial "
        "insertion recomputes the full permutation."
    )
    add_para(
        doc,
        "The matrix variants reduce that cost by changing shorter sequences (job "
        "order within an order and order sequence). IGA-Matrix1 keeps a block "
        "schedule; Matrix2 and Matrix3 add LocalSearch3, which allows order "
        "interleaving by adjacent swaps—sometimes necessary by Lemma 3. Matrix3 "
        "also scores job order by the F of the whole schedule rather than by an "
        "order’s own makespan. For IGA-String the authors choose y = 20,000 and "
        "z = 2 [1, Table 8]. Their experimental protocol (time limit "
        "n·o·m/2·0.12 s, 5 runs, RPD, Wilcoxon test) is the starting point of our "
        "comparison; deviations are stated in Section 6."
    )

    add_heading(doc, "5 Our solution method", 1)
    add_para(
        doc,
        "Our method is simulated annealing on the same permutation of all jobs. The "
        "initial solution is MultipleNEH (as for the IGAs), or a random permutation "
        "in the ablation. Each step applies one random move: job insertion with "
        "probability 0.6, swap of two jobs with 0.3, and relocation of one order’s "
        "job block with 0.1. Improvements are always accepted; a worsening Δ is "
        "accepted with probability exp(−Δ / T)."
    )
    add_para(
        doc,
        "The initial temperature T₀ is calibrated per instance: from 200 random "
        "moves the mean worsening Δ⁺ is taken and T₀ is set so that this mean "
        "worsening is accepted with probability p₀, i.e. T₀ = −Δ⁺ / ln p₀. "
        "Temperature then falls geometrically with the fraction of budget used "
        "τ ∈ [0,1]:"
    )
    add_para(
        doc,
        "T(τ) = T₀ · r^τ,",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "where r = t_ratio is the ratio of final to initial temperature. Tying "
        "cooling to the budget fraction ensures that the schedule always ends "
        "exactly when the run ends, regardless of instance size. The "
        "implementation is in Python 3.12; every run result is checked by an "
        "independent function that recomputes F from explicit start and finish "
        "times."
    )

    add_heading(doc, "6 Differences from the original paper", 1)
    add_para(
        doc,
        "The main difference is the metaheuristic: instead of IGA we use SA with "
        "geometric cooling and cheap local moves. The IGA-String baseline was "
        "re-implemented from the pseudocode [1, Alg. 2–6]; unlike the paper we "
        "also check the budget between individual job insertions (one IGA "
        "iteration can consume a large share of the limit on large instances). "
        "IGA-Matrix1–3 and the MINLP model were not implemented; their published "
        "RPDs are used only as a secondary reference."
    )
    add_para(
        doc,
        "Instead of the time limit n·o·m/2·t seconds (t = 0.12) we use a fixed "
        "budget of 190,000 full-schedule evaluations per run. The reason is "
        "reproducibility: a time limit depends on the machine and on background "
        "load (during parameter tuning the laptop went to sleep and some runs "
        "received far less work). On the development laptop (Intel Core "
        "i7-9750H), 190,000 evaluations roughly match the work bought by the "
        "paper’s time limit when four runs execute in parallel. The Big testbed "
        "was further reduced to 5 of the 20 comparison instances per size "
        "(ids 10–14) for computational budget."
    )

    add_heading(doc, "7 Experimental methodology", 1)
    add_para(
        doc,
        "We use the authors’ official instances [2] (commit c3d1a47). Processing "
        "times are drawn from U[1, 100]. Correctness of the objective was checked "
        "on all 90 instances with n = 3, o = 2: the optimum from full enumeration "
        "matches the best-known value in the files. Software: Python 3.12.10, "
        "Windows 10; runs used 4 workers."
    )
    add_table(
        doc,
        ["Item", "Setting"],
        [
            ["SA tuning", "9 combinations p₀ ∈ {0.01, 0.1, 0.3}, r ∈ {0.001, 0.01, 0.1}; "
             "3 sizes × 5 instances (ids 0–4) × 3 seeds; paper time limit"],
            ["Small testbed", "n ∈ {3,4,5}, o ∈ {2,3,4}, m ∈ {2,3,6}; instances 10–29; "
             "5 seeds; 190,000 evaluations; SA and IGA-String"],
            ["Big testbed", "n ∈ {10,20,50}, o ∈ {2,5,10}, m ∈ {2,3,6}; instances 10–14; "
             "5 seeds; 190,000 evaluations; SA and IGA-String"],
            ["Start ablation", "5 sizes, instances 10–14, 5 seeds; SA-NEH vs SA-random"],
            ["Extended budget", "n = 50, o = 10, m ∈ {2,3,6}; 760,000 evaluations"],
            ["Metric", "RPD = 100·(F − F_ref)/F_ref [%]; F_ref = min(published value, "
             "best run in the experiment)"],
            ["Statistics", "one-sided Wilcoxon signed-rank test on per-instance mean "
             "RPD, α = 0.05"],
            ["SA parameters", "p₀ = 0.3, r = 0.001 (lowest mean RPD in tuning); "
             "IGA-String: y = 20,000, z = 2"],
        ],
        "Table 1: Overview of the experimental protocol.",
    )
    add_para(
        doc,
        "In tuning, p₀ = 0.3 with r = 0.001 had the lowest mean RPD (0.234%), without "
        "a significant difference from three other settings at 0.27–0.31%. All "
        "settings with r = 0.1 were significantly worse. The chosen values are also "
        "the implementation defaults."
    )

    add_heading(doc, "8 Results", 1)
    add_heading(doc, "8.1 Small testbed", 2)
    add_para(
        doc,
        "On 540 instances (5,400 runs) SA reached a mean RPD of 0.008% and "
        "IGA-String 0.044%. Both medians are 0. SA hit the reference value in "
        "97.6% of runs and IGA-String in 92.0%. A one-sided Wilcoxon test on 540 "
        "instances confirms SA’s lead (p ≈ 1.6·10⁻⁸). On 469 instances the two "
        "methods have the same mean RPD; the gap appears mainly on larger sizes "
        "(n = 5, o ∈ {3,4}). On 19 instances we improved the published best-known "
        "value (mean improvement 0.24%); none of them is among the instances for "
        "which the authors report a proven optimum."
    )
    add_table(
        doc,
        ["Method", "Mean RPD [%]", "Median", "σ", "Reference hits [%]", "Mean time [s]"],
        [
            ["SA", "0.008", "0.000", "0.073", "97.6", "2.99"],
            ["IGA-String", "0.044", "0.000", "0.216", "92.0", "2.45"],
        ],
        "Table 2: Summary on the Small testbed (540 instances, 5 seeds).",
    )
    add_figure(
        doc, FIG / "small_convergence.png",
        caption="Figure 1: Convergence on the Small testbed – mean RPD of the best "
        "solution against the share of budget used.",
    )
    add_para(
        doc,
        "IGA-String leads for roughly the first third of the budget; SA overtakes "
        "it around 35% and then stays near zero. With a much smaller budget the "
        "ranking would likely reverse."
    )

    add_heading(doc, "8.2 Big testbed", 2)
    add_para(
        doc,
        "On 135 instances (1,350 runs) the mean RPD is 0.389% for SA and 0.907% "
        "for IGA-String (p ≈ 3.3·10⁻¹⁶). SA is better on 109 instances, "
        "IGA-String on 25. Mean run times are almost equal (26.0 s vs 25.0 s), so "
        "the imbalance in time per evaluation is small here. On 70 instances we "
        "found a value better than in the authors’ files (65 by SA alone)."
    )
    add_table(
        doc,
        ["Method", "Mean RPD [%]", "Median", "σ", "Reference hits [%]", "Mean time [s]"],
        [
            ["SA", "0.389", "0.339", "0.345", "18.4", "26.0"],
            ["IGA-String", "0.907", "0.823", "0.624", "6.8", "25.0"],
        ],
        "Table 3: Summary on the Big testbed (135 instances, 5 seeds).",
    )
    add_figure(
        doc, FIG / "big_convergence.png",
        caption="Figure 2: Convergence on the Big testbed. SA overtakes IGA-String "
        "at about 63% of the budget and is still improving at the end.",
    )
    add_figure(
        doc, FIG / "big_rpd_by_factor.png", width_cm=12.5,
        caption="Figure 3: Mean RPD with 95% confidence interval by n, o and m "
        "(Big testbed).",
    )
    add_para(
        doc,
        "The exception is the 500-job instances (n = 50, o = 10): at 190,000 "
        "evaluations IGA-String is better on 11 of 15 instances (RPD 0.600% "
        "against 0.735%). SA performs only about 380 moves per job there, which "
        "suggests incomplete convergence; Section 8.4 tests that hypothesis."
    )

    add_heading(doc, "8.3 Ablation of the initial solution", 2)
    add_para(
        doc,
        "On five sizes (25 instances) we compared SA starting from MultipleNEH "
        "with SA starting from a random permutation under the same 190,000-"
        "evaluation budget. The random start has a mean gap of 81% to the "
        "best-known value at the outset, NEH only 2%; yet the random start "
        "finishes better (mean RPD 0.369% against 0.429%, Wilcoxon on absolute "
        "F, p = 0.041). SA’s advantage therefore does not come from MultipleNEH; "
        "with the chosen cooling schedule a strong start may even restrict "
        "exploration."
    )

    add_heading(doc, "8.4 Extended budget on 500-job instances", 2)
    add_para(
        doc,
        "The same 15 instances with 500 jobs were re-run at four times the "
        "budget (760,000 evaluations). Against a common reference (the minimum "
        "of both experiments and the published value) SA’s RPD fell from 0.779% "
        "to 0.263% and IGA-String’s from 0.643% to 0.513%. At 760,000 "
        "evaluations SA wins on 11 of 15 instances (Wilcoxon p = 0.011); at "
        "190,000 it was behind (p = 0.93 for the hypothesis that SA is better). "
        "SA’s last improvement typically arrives at 99.8% of the budget. The "
        "loss of SA on 500-job instances in the main experiment is therefore a "
        "budget effect, not a systematic weakness of the method."
    )
    add_table(
        doc,
        ["m", "SA @190k", "IGA @190k", "SA @760k", "IGA @760k"],
        [
            ["2", "0.598", "0.772", "0.298", "0.757"],
            ["3", "0.621", "0.570", "0.353", "0.527"],
            ["6", "1.116", "0.587", "0.139", "0.255"],
            ["overall", "0.779", "0.643", "0.263", "0.513"],
        ],
        "Table 4: Mean RPD [%] on 15 instances with 500 jobs at two budgets "
        "(common reference).",
    )

    add_heading(doc, "9 Comparison with the authors’ results", 1)
    add_para(
        doc,
        "Table 5 places our RPDs next to the values in [1]. The comparison is not "
        "a direct replication: different hardware, a fixed evaluation count "
        "instead of a time limit, 5 of 20 instances per size on the Big testbed, "
        "and a stricter F_ref (19 + 70 new best-known values). Our IGA-String is "
        "close to the published figure on the Small testbed and higher on the "
        "Big one, consistent with the stricter reference. SA on the Big testbed "
        "lies in the range of the published IGA-Matrix variants, but without "
        "running those variants under the same conditions this is not evidence "
        "of superiority."
    )
    add_table(
        doc,
        ["Test / method", "Our RPD [%]", "Published RPD [%]"],
        [
            ["Small / IGA-String", "0.044", "0.058"],
            ["Small / SA", "0.008", "—"],
            ["Big / IGA-String", "0.907", "0.817"],
            ["Big / SA", "0.389", "—"],
            ["Big / IGA-Matrix1–3 (only [1])", "—", "0.32–0.44"],
        ],
        "Table 5: Indicative comparison with the published results [1].",
    )

    add_heading(doc, "10 Discussion", 1)
    add_para(
        doc,
        "SA benefits from a large number of cheap moves (on the order of 10⁵ per "
        "run) against hundreds to thousands of expensive IGA-String iterations, "
        "which explains the later but steeper drop in RPD. IGA-String is better "
        "under a short budget; SA is better when the full limit is used. Equal "
        "evaluations are not equal time: on the Small testbed an SA run took 22% "
        "longer (2.99 s against 2.45 s), on the Big testbed only 4%. Part of "
        "SA’s Small-testbed advantage may therefore come from slightly more "
        "wall-clock time; IGA-String is, however, already nearly flat at the end "
        "of the budget. The ablation shows that MultipleNEH is not necessary for "
        "SA quality. A fixed evaluation count also fails to give every size the "
        "same search depth (moves per job fall with N), which the paper’s time "
        "limit growing with n·o·m partly addresses."
    )

    add_heading(doc, "11 Limitations", 1)
    add_para(
        doc,
        "We did not implement IGA-Matrix1–3 or the MINLP/Gurobi model. The Big "
        "testbed covers only 5 of 20 instances per size. The evaluation-count "
        "budget differs from the authors’ protocol and, on the Small testbed, "
        "slightly favours SA in wall-clock time. Tuning used three sizes; the "
        "winning setting sits in a corner of the grid and is not significantly "
        "better than several neighbours. The results are tied to one pure-Python "
        "implementation on a single laptop."
    )

    add_heading(doc, "12 Conclusion", 1)
    add_para(
        doc,
        "We designed and implemented simulated annealing for COSP in a "
        "permutation flow shop and compared it fairly with a re-implementation "
        "of IGA-String from [1]. At 190,000 evaluations per run SA significantly "
        "outperforms IGA-String on both the Small and the Big testbed. The "
        "ranking, however, depends on budget and size: IGA-String is better "
        "early in a run and on 500-job instances under the main budget; with a "
        "fourfold budget SA leads again on those instances. The ablation showed "
        "that SA’s advantage does not depend on starting from MultipleNEH. "
        "Useful next steps would be to compare SA with IGA-Matrix3 under "
        "identical conditions and to tie the budget to the number of jobs rather "
        "than to a fixed evaluation count alone."
    )

    add_heading(doc, "13 References", 1)
    refs = [
        "[1] HOFFMANN, J., NEUFELD, J. S., BUSCHER, U. Customer order scheduling in a "
        "permutation flow shop environment. Operations Research Perspectives, 2025, 15, "
        "100362. https://doi.org/10.1016/j.orp.2025.100362",
        "[2] HOFFMANN, J. COSP_Flow_Shop: problem instances [online]. GitHub "
        "[accessed 2026-11-14]. Available at: https://github.com/Julius2627/COSP_Flow_Shop",
        "[3] FRAMINAN, J. M., PEREZ-GONZALEZ, P., FERNANDEZ-VIAGAS, V. Deterministic "
        "assembly scheduling problems: A review and classification of concurrent-type "
        "scheduling models and solution procedures. European Journal of Operational "
        "Research, 2019, 273(2), 401–417.",
        "[4] GAREY, M. R., JOHNSON, D. S., SETHI, R. The complexity of flowshop and "
        "jobshop scheduling. Mathematics of Operations Research, 1976, 1(2), 117–129.",
        "[5] HOFFMANN, J., NEUFELD, J. S., BUSCHER, U. Iterated greedy algorithms for "
        "customer order scheduling with dedicated machines. IFAC-PapersOnLine, 2022, "
        "55(10), 1594–1599.",
        "[6] NAWAZ, M., ENSCORE, E. E., HAM, I. A heuristic algorithm for the m-machine, "
        "n-job flow-shop sequencing problem. Omega, 1983, 11(1), 91–95.",
        "[7] KIRKPATRICK, S., GELATT, C. D., VECCHI, M. P. Optimization by simulated "
        "annealing. Science, 1983, 220(4598), 671–680.",
    ]
    for ref in refs:
        p = add_para(doc, ref, size=10, align="left", first_line=False,
                     space_after=4, space_before=0)
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)

    add_heading(doc, "Appendix: Note on tool use", 1)
    add_para(
        doc,
        "The experiment source code, configuration files and the first draft of this "
        "report were produced with assistance from an AI coding assistant (Cursor) in "
        "November 2026. The problem analysis, experimental design, interpretation of "
        "results and the final wording of the report are the team’s own work. The "
        "instances [2] come from the paper’s authors; IGA-String is a re-implementation "
        "of their pseudocode."
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
