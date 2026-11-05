# Analysis Report – Group Assignment 2
Group members: <EDIT>

## Problem 1
**Expert results:** Q1 0.5806, Q2 0.7063, Q3 0.6402, Q4 0.4843, Q5 0.6082, Q6 0.6929, Q7 0.6499.
Q1 by hand = 0.55500*0.68883 + 0.44500*0.44569 = 0.38230 + 0.19833 = 0.58063 (matches code).

**Explaining away (Q6 vs Q7):** P(AC=On|E=High)=0.693 drops to 0.650 once Load=Heavy is known. Energy is a collider of AC and Load; observing it makes both causes more likely, and learning one cause is present reduces the need for the other.

**d-separation:** (1) W ⊥ D holds (path W→A←O←D blocked by unobserved collider A); P(Hot)=0.5 both with and without D. (2) W ⊥ D | E fails (observing E, a descendant of collider A, opens the path); 0.608 vs 0.600. (3) W ⊥ L | O holds (O observed fork blocks W→A←O→L; E unobserved collider blocks W→A→E←L); 0.5 vs 0.5.

**Learning (mean |diff| over Q1–Q7):** n=500 MLE 0.0287 / Bayesian 0.0272; n=5000 0.0019 / 0.0023; n=20000 0.0022 / 0.0023.
Largest error at n=500 is Q4 (MLE 0.064, Bayesian 0.057): its evidence (Cold, High occupancy) occurs in only 51 of 500 rows, and the estimates feeding it are noisy (P(E=High|AC=Off,Light) learned as 0.06 vs true 0.12; P(Heavy|High) 0.70 vs 0.75).
Small data: the Bayesian (BDeu) estimator is slightly better because the prior smooths sparse cells (Cold/Low AC: MLE 0.020, BDeu 0.035, true 0.05) and avoids 0/1 estimates. With more data the prior's influence vanishes and both are equal; the non-monotone 5000→20000 values are noise of a single random sample.

## Problem 2 (Fast Downward)
| Scenario | Config | Plan length | Expanded | Time |
|---|---|---|---|---|
| Base | Greedy best-first (FF) | 33 | 68 | 0.001 s |
| Base | A* (LM-cut) | 25 | 5,776 | 0.25 s |
| Extended | Greedy best-first (FF) | 46 | 143 | 0.002 s |
| Extended | A* (LM-cut) | 40 | 2,230,060 | ~120 s |
(pyperplan, base: greedy 32 steps/48 expanded, A* 25 steps/6,969 expanded/54 s. Greedy results vary slightly between runs/planners; optimal length is 25 in both.)

**Plan lengths:** greedy returns the first plan found; the FD greedy base plan makes five round trips carrying one rock each. A* proves minimality; 5 rocks with 2 bays need ≥3 trips (7 rocks: ≥4 trips).

**Optimal base plan:** trip 1 Base→B (Rock2, bay1)→D (Rock4, bay2)→B→Base, deposit both (soft rocks, no drill needed). Trip 2 A→C→E picks up the drill, →F Rock5 (bay1), →E→C Rock3 (bay2), →A→Base, deposit. Trip 3 A, Rock1, Base. Drill is picked up once, on trip 2, and kept. The one-way slope is not used.

**Extended:** with Base↔B closed, SiteB is reachable only via SiteD (B↔D is two-way). SiteD is reached via the one-way slope C→D (also possible from E). The optimal plan goes Base→A→C→D (Rock4)→B (Rock2)→D→E (drill)→C→A→Base; later trips fetch Rock5+Rock7 (F), Rock3+Rock6, then Rock1. The slope is used once, downhill; the return path never goes D→C.

**Verification:** run_planner.py simulates every plan; all four end with all rocks at Base, both bays empty, rover at Base.

## Problem 3
Empty clause at C20. Chain: C10 (¬trusted(mira)) + C1 → C11; C11 + C3 → C12; C12 + C7 → C14; C14 + C8 → C17; C17 + C9 → []. Rules 2 and 4 and facts 5, 6 are not needed (permitted-to-inspect is not the same as inspecting; verification comes from rule 3).
