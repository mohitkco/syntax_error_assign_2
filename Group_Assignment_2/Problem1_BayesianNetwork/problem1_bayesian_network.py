"""
PROBLEM 1 : Smart Home Energy Consumption Analysis using a Bayesian Network
Group Name : SYNTAX-ERROR
Group members (manish    B24ME029
               sarup     B24ME042
               nitesh    B24MT016
               chingkhei B24ME013
               mohit     B24CS030)

Run :  python problem1_bayesian_network.py
Needs: pip install pgmpy numpy pandas matplotlib networkx
All outputs (csv, png) are written to the folder  ./output
"""
import os, warnings, logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator

warnings.filterwarnings("ignore")
logging.getLogger("pgmpy").setLevel(logging.ERROR)

SEED = 42                                   # fixed random seed (reported)
SIZES = [500, 5000, 20000]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)


def header(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ---------------------------------------------------------------------------
# PART A.1  Structure + A.2 CPTs
# ---------------------------------------------------------------------------
EDGES = [("Weather", "AC"), ("Occupancy", "AC"), ("DayType", "Occupancy"),
         ("Occupancy", "ApplianceLoad"), ("AC", "Energy"), ("ApplianceLoad", "Energy")]

STATES = {
    "Weather": ["Hot", "Mild", "Cold"],
    "DayType": ["Weekday", "Weekend"],
    "Occupancy": ["High", "Low"],
    "AC": ["On", "Off"],
    "ApplianceLoad": ["Heavy", "Light"],
    "Energy": ["High", "Low"],
}
TOPO = ["Weather", "DayType", "Occupancy", "AC", "ApplianceLoad", "Energy"]


def build_expert():
    m = DiscreteBayesianNetwork(EDGES)
    cw = TabularCPD("Weather", 3, [[0.5], [0.3], [0.2]], state_names={"Weather": STATES["Weather"]})
    cd = TabularCPD("DayType", 2, [[0.7], [0.3]], state_names={"DayType": STATES["DayType"]})
    # columns: DayType = Weekday, Weekend
    co = TabularCPD("Occupancy", 2, [[0.45, 0.80], [0.55, 0.20]],
                    evidence=["DayType"], evidence_card=[2],
                    state_names={"Occupancy": STATES["Occupancy"], "DayType": STATES["DayType"]})
    # columns: (Weather,Occupancy) = Hot/High, Hot/Low, Mild/High, Mild/Low, Cold/High, Cold/Low
    p_on = [0.90, 0.60, 0.40, 0.15, 0.10, 0.05]
    ca = TabularCPD("AC", 2, [p_on, [1 - p for p in p_on]],
                    evidence=["Weather", "Occupancy"], evidence_card=[3, 2],
                    state_names={"AC": STATES["AC"], "Weather": STATES["Weather"],
                                 "Occupancy": STATES["Occupancy"]})
    cl = TabularCPD("ApplianceLoad", 2, [[0.75, 0.35], [0.25, 0.65]],
                    evidence=["Occupancy"], evidence_card=[2],
                    state_names={"ApplianceLoad": STATES["ApplianceLoad"], "Occupancy": STATES["Occupancy"]})
    # columns: (AC,Load) = On/Heavy, On/Light, Off/Heavy, Off/Light
    p_hi = [0.92, 0.68, 0.55, 0.12]
    ce = TabularCPD("Energy", 2, [p_hi, [1 - p for p in p_hi]],
                    evidence=["AC", "ApplianceLoad"], evidence_card=[2, 2],
                    state_names={"Energy": STATES["Energy"], "AC": STATES["AC"],
                                 "ApplianceLoad": STATES["ApplianceLoad"]})
    m.add_cpds(cw, cd, co, ca, cl, ce)
    return m


header("PART A : EXPERT BAYESIAN NETWORK")
expert = build_expert()
print("Edges :", expert.edges())
print("Model check_model() ->", expert.check_model(), "(structure + CPDs consistent)")

# A.2 programmatic verification that every CPT column sums to 1
print("\nCPT column-sum verification (each parent configuration must sum to 1):")
all_ok = True
for cpd in expert.get_cpds():
    vals = cpd.get_values()
    sums = vals.sum(axis=0)
    ok = np.allclose(sums, 1.0)
    all_ok &= ok
    print(f"  P({cpd.variable:<13}| parents) : sums = {np.round(sums, 6).tolist()}  -> {'OK' if ok else 'FAIL'}")
assert all_ok, "A CPT does not sum to 1"
print("All CPTs valid:", all_ok)


# A.3 visualise
def draw_network(model, path):
    G = nx.DiGraph(model.edges())
    pos = {"Weather": (0, 2), "DayType": (3, 3), "Occupancy": (3, 1.8), "AC": (1.2, 0.8),
           "ApplianceLoad": (4.8, 0.8), "Energy": (3, -0.4)}
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_size=6500, node_color="#cfe8ff", edgecolors="k",
            font_size=8, arrowsize=22, arrows=True)
    plt.title("Smart-Home Energy Bayesian Network (expert structure)")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


draw_network(expert, os.path.join(OUT, "bayesian_network.png"))
print("\nNetwork figure saved -> output/bayesian_network.png")

# A.4 queries
QUERIES = {
    "Q1": ("P(E=High)",                    "Energy",  "High", {}),
    "Q2": ("P(E=High | W=Hot)",            "Energy",  "High", {"Weather": "Hot"}),
    "Q3": ("P(E=High | D=Weekend)",        "Energy",  "High", {"DayType": "Weekend"}),
    "Q4": ("P(E=High | W=Cold, O=High)",   "Energy",  "High", {"Weather": "Cold", "Occupancy": "High"}),
    "Q5": ("P(W=Hot | E=High)",            "Weather", "Hot",  {"Energy": "High"}),
    "Q6": ("P(AC=On | E=High)",            "AC",      "On",   {"Energy": "High"}),
    "Q7": ("P(AC=On | E=High, L=Heavy)",   "AC",      "On",   {"Energy": "High", "ApplianceLoad": "Heavy"}),
}


def prob(model, var, val, evidence=None):
    inf = VariableElimination(model)
    try:
        f = inf.query([var], evidence=evidence or {}, show_progress=False)
        return float(f.get_value(**{var: val}))
    except Exception:
        return float("nan")


def run_queries(model):
    return {q: prob(model, v, s, e) for q, (_, v, s, e) in QUERIES.items()}


expert_res = run_queries(expert)
print("\nExpert-model query results:")
for q, (desc, *_) in QUERIES.items():
    print(f"  {q}: {desc:<32} = {expert_res[q]:.6f}")

# A.5 explaining away
print("\nA.5  Q6 vs Q7 (explaining away)")
print(f"  Q6 P(AC=On | E=High)               = {expert_res['Q6']:.4f}")
print(f"  Q7 P(AC=On | E=High, Load=Heavy)   = {expert_res['Q7']:.4f}")
print(f"  Prior P(AC=On)                     = {prob(expert, 'AC', 'On'):.4f}")
print(f"  Change Q7-Q6 = {expert_res['Q7'] - expert_res['Q6']:+.4f}")
print("""  Explanation: AC and ApplianceLoad are the two parents (causes) of Energy, so Energy is a
  collider (AC -> E <- L).  Observing E=High raises belief in *both* causes.  Once we also learn
  that Load=Heavy, that cause already 'explains' the high consumption, so the need to invoke the
  other cause (AC=On) is reduced: P(AC=On) falls from Q6 to Q7.  This is 'explaining away'.""")

# A.6 hand calculation of Q1
header("A.6  HAND CALCULATION OF Q1 = P(E = High)")
P_wd, P_we = 0.7, 0.3
P_oH = 0.45 * P_wd + 0.80 * P_we
P_oL = 1 - P_oH
print(f"Step 1  P(O=High) = 0.45*0.7 + 0.80*0.3 = {0.45*0.7:.3f} + {0.80*0.3:.3f} = {P_oH:.4f};  "
      f"P(O=Low) = {P_oL:.4f}")
pW = {"Hot": .5, "Mild": .3, "Cold": .2}
pOn = {("Hot", "High"): .9, ("Hot", "Low"): .6, ("Mild", "High"): .4, ("Mild", "Low"): .15,
       ("Cold", "High"): .1, ("Cold", "Low"): .05}
pOnO = {o: sum(pW[w] * pOn[(w, o)] for w in pW) for o in ("High", "Low")}
print("Step 2  (W is independent of O)  P(AC=On | O) = sum_w P(w) P(On|w,O)")
print(f"        P(On|O=High) = .5*.9 + .3*.4 + .2*.1   = {pOnO['High']:.4f}")
print(f"        P(On|O=Low ) = .5*.6 + .3*.15 + .2*.05 = {pOnO['Low']:.4f}")
pH = {"High": .75, "Low": .35}
pE = {("On", "Heavy"): .92, ("On", "Light"): .68, ("Off", "Heavy"): .55, ("Off", "Light"): .12}
print("Step 3  Given O, AC and Load are independent, so for each O:")
print("        P(E=High|O) = sum_{a,l} P(a|O) P(l|O) P(E=High|a,l)")
total = 0
for o, po in (("High", P_oH), ("Low", P_oL)):
    a = pOnO[o]
    h = pH[o]
    terms = [(a * h, "On", "Heavy"), (a * (1 - h), "On", "Light"),
             ((1 - a) * h, "Off", "Heavy"), ((1 - a) * (1 - h), "Off", "Light")]
    s = 0
    print(f"        O={o}:")
    for pr, ac, ld in terms:
        c = pr * pE[(ac, ld)]
        s += c
        print(f"           P(AC={ac:<3},L={ld:<5}|O)={pr:.5f} x P(E=H|..)={pE[(ac, ld)]:.2f} = {c:.5f}")
    print(f"           P(E=High|O={o}) = {s:.5f}")
    total += po * s
    print(f"           contribution  P(O={o}) x {s:.5f} = {po * s:.5f}")
print(f"Step 4  Q1 = {total:.6f}")
print(f"Code (variable elimination) gives Q1 = {expert_res['Q1']:.6f}   -> match: "
      f"{np.isclose(total, expert_res['Q1'])}")
assert np.isclose(total, expert_res["Q1"])

# ---------------------------------------------------------------------------
# PART B  d-separation + numeric verification
# ---------------------------------------------------------------------------
header("PART B : CONDITIONAL INDEPENDENCE (d-separation)")
checks = [
    ("1. Weather _|_ DayType", "Weather", "DayType", [],
     ("Weather", "Hot", {}), ("Weather", "Hot", {"DayType": "Weekend"}),
     "Only path: W->A<-O<-D.  A (collider) is unobserved and has no observed descendant -> BLOCKED. Independent."),
    ("2. Weather _|_ DayType | Energy", "Weather", "DayType", ["Energy"],
     ("Weather", "Hot", {"Energy": "High"}), ("Weather", "Hot", {"Energy": "High", "DayType": "Weekend"}),
     "Path W->A<-O<-D: collider A has an observed descendant E -> collider OPENED; O is a "
     "non-collider and unobserved -> path ACTIVE. NOT independent."),
    ("3. Weather _|_ ApplianceLoad | Occupancy", "Weather", "ApplianceLoad", ["Occupancy"],
     ("Weather", "Hot", {"Occupancy": "High"}), ("Weather", "Hot", {"Occupancy": "High", "ApplianceLoad": "Heavy"}),
     "Path W->A<-O->L : O is an observed fork -> BLOCKED (collider A also unobserved). "
     "Path W->A->E<-L : E collider unobserved -> BLOCKED. Independent."),
]
for name, x, y, z, (v1, s1, e1), (v2, s2, e2), why in checks:
    dsep = not expert.is_dconnected(x, y, observed=z)
    p1 = prob(expert, v1, s1, e1)
    p2 = prob(expert, v2, s2, e2)
    print(f"\n{name}")
    print(f"  d-separated (pgmpy)  : {dsep}")
    print(f"  Reasoning            : {why}")
    e1s = ",".join(f"{k}={v}" for k, v in e1.items())
    e2s = ",".join(f"{k}={v}" for k, v in e2.items())
    print(f"  Numeric : P({v1}={s1}|{e1s or '-'}) = {p1:.6f}   vs   P({v1}={s1}|{e2s}) = {p2:.6f}"
          f"   |diff| = {abs(p1 - p2):.2e}")
    print(f"  Conclusion: {'INDEPENDENT (values equal)' if np.isclose(p1, p2) else 'DEPENDENT (values differ)'}")


# ---------------------------------------------------------------------------
# PART C  ancestral sampling (own implementation)
# ---------------------------------------------------------------------------
header(f"PART C : SYNTHETIC DATA (ancestral sampling, seed = {SEED})")


def cpt_lookup(model, var, parent_values):
    """P(var | parents) as a vector over STATES[var] for the given parent assignment."""
    cpd = model.get_cpds(var)
    return np.array([cpd.get_value(**{var: s}, **parent_values) for s in STATES[var]])


def ancestral_sample(model, n, seed):
    rng = np.random.default_rng(seed)
    rows = []
    parents = {v: list(model.get_parents(v)) for v in TOPO}
    cache = {}
    for _ in range(n):
        sample = {}
        for v in TOPO:                                  # visit nodes in topological order
            pa = {p: sample[p] for p in parents[v]}
            key = (v, tuple(pa.items()))
            if key not in cache:
                cache[key] = cpt_lookup(model, v, pa)
            sample[v] = STATES[v][rng.choice(len(STATES[v]), p=cache[key])]
        rows.append(sample)
    return pd.DataFrame(rows, columns=TOPO)


datasets = {}
for n in SIZES:
    df = ancestral_sample(expert, n, SEED)
    datasets[n] = df
    df.to_csv(os.path.join(OUT, f"data_{n}.csv"), index=False)
    print(f"\n--- Dataset n = {n} ---")
    freq = df["Weather"].value_counts(normalize=True).reindex(STATES["Weather"])
    print("Empirical Weather frequency (true: Hot .50, Mild .30, Cold .20):")
    print(freq.round(4).to_string())
    ct = pd.crosstab(df["Weather"], df["Occupancy"]).reindex(index=STATES["Weather"],
                                                              columns=STATES["Occupancy"])
    print("Counts per (Weather, Occupancy):")
    print(ct.to_string())

# ---------------------------------------------------------------------------
# PART D  learning
# ---------------------------------------------------------------------------
header("PART D : LEARNING FROM DATA (MLE and BDeu, equivalent sample size = 10)")


def learn(df, method):
    m = DiscreteBayesianNetwork(EDGES)                  # same structure as expert
    m.add_nodes_from(TOPO)
    if method == "MLE":
        est = MaximumLikelihoodEstimator(m, df, state_names=STATES)
        cpds = est.get_parameters()
    else:
        est = BayesianEstimator(m, df, state_names=STATES)
        cpds = est.get_parameters(prior_type="BDeu", equivalent_sample_size=10)
    m.add_cpds(*cpds)
    return m


def ac_table(model):
    cpd = model.get_cpds("AC")
    rows = []
    for w in STATES["Weather"]:
        for o in STATES["Occupancy"]:
            rows.append((w, o, cpd.get_value(AC="On", Weather=w, Occupancy=o)))
    return pd.DataFrame(rows, columns=["Weather", "Occupancy", "P(AC=On)"]).set_index(["Weather", "Occupancy"])


all_rows, summary = [], []
for n in SIZES:
    df = datasets[n]
    mle, bay = learn(df, "MLE"), learn(df, "BDeu")
    print(f"\n--- n = {n} : learned CPT of AC Usage, P(AC=On | Weather, Occupancy) ---")
    t = pd.concat([ac_table(expert).rename(columns={"P(AC=On)": "Expert"}),
                   ac_table(mle).rename(columns={"P(AC=On)": "MLE"}),
                   ac_table(bay).rename(columns={"P(AC=On)": "BDeu"})], axis=1)
    t["|MLE-Exp|"] = (t["MLE"] - t["Expert"]).abs()
    t["|BDeu-Exp|"] = (t["BDeu"] - t["Expert"]).abs()
    print(t.round(4).to_string())
    t.round(6).to_csv(os.path.join(OUT, f"AC_cpt_comparison_{n}.csv"))

    rm, rb = run_queries(mle), run_queries(bay)
    tab = pd.DataFrame({
        "Query": list(QUERIES), "Description": [QUERIES[q][0] for q in QUERIES],
        "Expert": [expert_res[q] for q in QUERIES], "MLE": [rm[q] for q in QUERIES],
        "Bayesian": [rb[q] for q in QUERIES]})
    tab["|Diff| MLE"] = (tab["MLE"] - tab["Expert"]).abs()
    tab["|Diff| Bayesian"] = (tab["Bayesian"] - tab["Expert"]).abs()
    tab.insert(0, "n", n)
    all_rows.append(tab)
    summary.append((n, tab["|Diff| MLE"].mean(), tab["|Diff| Bayesian"].mean()))
    print(f"\n=== PART E : comparison table, n = {n} ===")
    print(tab.drop(columns="n").round(5).to_string(index=False))
    print(f"Mean |Diff|  MLE = {summary[-1][1]:.5f}   Bayesian = {summary[-1][2]:.5f}")

full = pd.concat(all_rows)
full.round(6).to_csv(os.path.join(OUT, "comparison_all_sizes.csv"), index=False)

# ---------------------------------------------------------------------------
# PART E  plot + discussion data
# ---------------------------------------------------------------------------
header("PART E : MEAN ABSOLUTE DIFFERENCE vs DATASET SIZE")
sm = pd.DataFrame(summary, columns=["n", "MAE_MLE", "MAE_Bayesian"])
print(sm.round(5).to_string(index=False))
plt.figure(figsize=(6.5, 4.5))
plt.plot(sm.n, sm.MAE_MLE, "o-", label="MLE")
plt.plot(sm.n, sm.MAE_Bayesian, "s--", label="Bayesian (BDeu, ESS=10)")
plt.xscale("log")
plt.xlabel("Dataset size (log scale)")
plt.ylabel("Mean |difference| over Q1-Q7")
plt.title("Learning error vs dataset size")
plt.grid(alpha=.3)
plt.legend()
plt.savefig(os.path.join(OUT, "mae_vs_dataset_size.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Plot saved -> output/mae_vs_dataset_size.png")

t500 = full[full.n == 500].set_index("Query")
worst_mle, worst_bay = t500["|Diff| MLE"].idxmax(), t500["|Diff| Bayesian"].idxmax()
print(f"\nLargest error at n=500 : MLE -> {worst_mle} ({t500.loc[worst_mle, '|Diff| MLE']:.4f}),"
      f"  Bayesian -> {worst_bay} ({t500.loc[worst_bay, '|Diff| Bayesian']:.4f})")
d500 = datasets[500]
cold_high = d500[(d500.Weather == "Cold") & (d500.Occupancy == "High")]
print(f"Evidence frequency in the 500-sample set:")
print(f"   (Weather=Cold, Occupancy=High) rows = {len(cold_high)}  [evidence of Q4]")
print(f"   of which AC=On = {(cold_high.AC == 'On').sum()}  (true P(AC=On|Cold,High) = 0.10)")
print(f"   E=High rows = {(d500.Energy == 'High').sum()}  [evidence of Q5, Q6]")
print(f"   E=High & Load=Heavy rows = {((d500.Energy == 'High') & (d500.ApplianceLoad == 'Heavy')).sum()}  [Q7]")
print("\nResults written to ./output  (csv files, png figures)")
