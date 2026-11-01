# Knowledge Base TODO Register

**Last updated:** 2026-11-01  
**Source:** `docs/Aamir_Khan_Knowledge_Base_Questionnaire_Answered.md`  
**Purpose:** Track all unresolved factual placeholders, deferred measurements, and pending verification items so the assistant never exposes unverified claims or literal `[FILL IN]` placeholders to recruiters.

---

## 1. Missing Factual Information (`[FILL IN]`)

| ID | Section | Item Required | Why Pending | What Aamir Needs to Supply | Status |
|----|---------|---------------|-------------|----------------------------|--------|
| TODO-01 | X11 / Final-Year Project | Final-year project team structure, individual role, and final metrics | Underway in 4th year CSE | Project details once semester milestones conclude | Open |
| TODO-02 | Project B (HealthTracker) / J2 | Exact data types and scope tracked in HealthTracker | Unconfirmed in app code | Confirm tracked fields (calories, macros, workouts, etc.) | Open |
| TODO-03 | Project B (HealthTracker) / J4 | Exact frontend/backend frameworks and DB schema | Need repo inspection | Inspect package.json and backend dependencies | Open |
| TODO-04 | Project B (HealthTracker) / J8 | Hardest bug personally fixed in HealthTracker | Awaiting real anecdote | Provide specific debugging incident | Open |
| TODO-05 | Project C (Health Premium) / J7, J14 | Dataset source, record count, and train/test split | Codebase check needed | Provide dataset origin (Kaggle/custom) and size | Open |
| TODO-06 | Project C (Health Premium) / J8 | Specific modelling challenge or data leakage check | Need exact bug details | Describe a concrete challenge encountered | Open |
| TODO-07 | Project C (Health Premium) / J14 | Formula behind "3% prediction error" (e.g. MAPE, MAE) | Metric definition | State exact mathematical formula used | Open |
| TODO-08 | Project E (Secure Auction) / J3, J4 | Dates, team role, and actual Django routes implemented | Learning project status | Confirm what was implemented vs planned | Open |
| TODO-09 | Project F (Browser Games) / J4, J11 | Repository paths and licensing for game assets | Codebase review needed | Confirm game repository link and assets used | Open |
| TODO-10 | S4 / Contest details | Official contest name, date, participant count, and proof link | Archival record | Provide certificate, email, or contest link | Open |
| TODO-11 | S5 / Git workflow | Specific PR / code review workflow used on projects | Workflow clarification | Describe branch/PR process | Open |
| TODO-12 | K1–K3 / Target Companies | Target companies, roles, and tailored "why us" notes | Deferred to Phase 9 | Will provide target company blocks in Phase 9 | Deferred |

---

## 2. Deferred Implementation and Evidence (`[TO BE FILLED IN]`)

| ID | Section | Deferred Task | Why Deferred | Completion Criteria | Status |
|----|---------|---------------|--------------|---------------------|--------|
| TODO-13 | X3 / Entropy-OJ | Malicious-input, fork bomb, and attack test results on Linux runner | Testing deferred | Run security test cases against unprivileged runner | Deferred |
| TODO-14 | X4 / Entropy-OJ | Maximum concurrent submissions stress-tested | Load test deferred | Measure queue latency under multi-job load | Deferred |
| TODO-15 | X5 / Entropy-OJ | Negative tests verifying hidden test cases never leak into AI prompt | Eval test deferred | Write test asserting hidden test cases excluded | Deferred |
| TODO-16 | Project B / J7 | Real-user count, offline sync tests, and CI performance benchmarks | Testing deferred | Document offline service-worker tests | Deferred |
| TODO-17 | V1, V6 / Repositories | Public/private visibility and README verification for all repos | Manual check | Audit GitHub repositories list | In Progress |

---

## 3. Clarifications and Unverified Claims (Strictly Prohibited Until Verified)

| Claim / Subject | Questionnaire Ref | Assistant Policy |
|-----------------|-------------------|------------------|
| **35% Latency Reduction** | X3, B10, T1 Q13 | **Removed completely.** Unmeasured; assistant must never claim this figure. |
| **"All Tests Pass" on Entropy-OJ** | J11, B10, T1 Q15 | **Prohibited.** Full test sequence was not run after Redis fix; state partial test status. |
| **Google/Apple/ByteDance Employment** | B6, B8, B10, T1 Q40 | **Prohibited.** Mentorship/hackathon association only; immediately correct false premises. |
| **"99% Real-World Accuracy" on ML** | J14, B10, T1 Q21 | **Prohibited.** $R^2 = 0.99$ on test split is not real-world insurance accuracy. |
| **Cursor Usage** | S5, B10, T1 Q25 | **Prohibited.** Aamir has not used Cursor; do not list it. |

---

## 4. Future Resource Publication

- Public Resume PDF URL (to be published in Phase 9 / Gate 2).
- Loom video walkthrough for Entropy-OJ (available: `https://www.loom.com/share/a982d7d46b654d11a39dd5e39f2372de`).
- Project architecture diagrams for HealthTracker and Health Premium Predictor.

---

## 5. Pending Retrieval Evaluations

- 45+ labeled recruiter evaluation queries loaded in `evals/seed_questions.yaml`.
- Benchmark Hit Rate@5 $\ge 90\%$ and MRR $\ge 0.80$ to be verified in Increment 6.
