---
name: duel
description: Two independent subagents tackle the same question or task (optionally debate), then a judge compares and decides. About 3x the cost of one answer (5x with debate), so only on request or for real decisions. Use when the user says "two agents", "second opinion", "compare approaches", "duel", "dos opiniones", "debate".
---

# Duel

Before starting, say the cost (number of subagent runs) and get an "ok" unless the user already asked for a duel.

1. **Brief** (you, once, max ~40 lines): goal, context (files, constraints, what is already known from the notes), what "done" looks like, output format and length. Both get the same brief verbatim; never the whole chat.
2. **Round 1**, two subagents in parallel, read-only. Make them differ so they catch different mistakes: different models when available (e.g. the strongest and a mid-tier one), and/or different stances (one optimises for simplicity and cost, the other for robustness and long term).
   - `build` (a design, plan or solution): the proposal, why each choice, risks, how to test it. Max ~80 lines.
   - `review` (an existing plan, document, diff or claim): findings `severity | where | issue | fix`, evidence only. Max ~40 lines.
   - `analysis` (a research question): answer, key facts with sources, confidence and what would change it. Max ~60 lines.
3. **Round 2**, only with `debate`: each gets the other's answer and returns what it keeps, what is wrong (with evidence) and its revised answer. Max ~40 lines each.
4. **Judge** (you, or a strong-model subagent if you run on a small one): a table `criterion | A | B` (correctness with evidence, simplicity, cost, risk, fit with the user's context), then the verdict (pick one or merge, one line of reason per decision). Findings both agree on: confirmed. Found by one: check them yourself before keeping them. Drop anything without evidence.
5. Show the result; apply changes only after the user confirms. End with the cost: number of subagent runs. Save the verdict with `save-knowledge` when it is a reusable decision.
