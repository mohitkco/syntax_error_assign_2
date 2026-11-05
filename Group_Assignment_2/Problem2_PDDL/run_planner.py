"""
PROBLEM 2 : Mars Rover - run planner (pyperplan) with two configurations on both scenarios,
then validate every plan with a step-by-step STRIPS simulator (Task 4).
Group Name : SYNTAX-ERROR
Group members (manish    B24ME029
               sarup     B24ME042
               nitesh    B24MT016
               chingkhei B24ME013
               mohit     B24CS030)

Run :  (a) Fast Downward (recommended, fast; see README for how to build it)
           python run_planner.py --planner fd --fd-path /path/to/fast-downward.py
       (b) pyperplan (pure Python, pip install pyperplan). A* on the EXTENDED problem is very slow
           with pyperplan (hours), so use  --scenarios base  or skip the optimal run there:
           python run_planner.py --planner pyperplan --scenarios base
Outputs are written to ./planner_output  (or --out DIR)
"""
import argparse, os, re, subprocess, sys, time, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--planner", choices=["fd", "pyperplan"], default="pyperplan")
ap.add_argument("--fd-path", default="fast-downward.py", help="path to fast-downward.py (planner fd)")
ap.add_argument("--scenarios", choices=["base", "extended", "both"], default="both")
ap.add_argument("--out", default=os.path.join(HERE, "planner_output"))
ARGS = ap.parse_args()
OUT = ARGS.out
os.makedirs(OUT, exist_ok=True)

DOMAIN = os.path.join(HERE, "Domain.pddl")
SCENARIOS = {"base": "Problem.pddl", "extended": "Problem_extended.pddl"}
# name : (pyperplan search, pyperplan heuristic, Fast-Downward --search string, file tag)
CONFIGS = {
    "satisficing (greedy best-first, h_FF)": ("gbf", "hff", "lazy_greedy([ff()],preferred=[ff()])", "gbfs_ff"),
    "optimal (A*, admissible LM-cut)":       ("astar", "lmcut", "astar(lmcut())", "astar_lmcut"),
}
if ARGS.scenarios != "both":
    SCENARIOS = {k: v for k, v in SCENARIOS.items() if k == ARGS.scenarios}

# ----------------------------------------------------------------------------------------
# Minimal PDDL (STRIPS + typing) parser / simulator  -> independent plan validator
# ----------------------------------------------------------------------------------------
def tokenize(text):
    text = re.sub(r";.*", "", text)
    return text.replace("(", " ( ").replace(")", " ) ").lower().split()

def parse_sexpr(tokens):
    def rec(i):
        if tokens[i] != "(":
            return tokens[i], i + 1
        lst, i = [], i + 1
        while tokens[i] != ")":
            x, i = rec(i)
            lst.append(x)
        return lst, i + 1
    return rec(0)[0]

def typed_list(items):
    """['a','b','-','t','c','-','u'] -> [('a','t'),('b','t'),('c','u')]"""
    out, pend, i = [], [], 0
    while i < len(items):
        if items[i] == "-":
            out += [(n, items[i + 1]) for n in pend]; pend = []; i += 2
        else:
            pend.append(items[i]); i += 1
    return out + [(n, "object") for n in pend]

def load_domain(path):
    d = parse_sexpr(tokenize(open(path).read()))
    actions = {}
    for sec in d[2:]:
        if sec[0] == ":action":
            name = sec[1]; kv = dict(zip(sec[2::2], sec[3::2]))
            params = [n for n, _ in typed_list(kv[":parameters"])]
            def lits(e):
                if e[0] == "and": return e[1:]
                return [e]
            pre = [tuple(l) for l in lits(kv[":precondition"])]
            add, dele = [], []
            for l in lits(kv[":effect"]):
                (dele if l[0] == "not" else add).append(tuple(l[1]) if l[0] == "not" else tuple(l))
            actions[name] = (params, pre, add, dele)
    return actions

def load_problem(path):
    p = parse_sexpr(tokenize(open(path).read()))
    init, goal = set(), []
    for sec in p[2:]:
        if sec[0] == ":init": init = {tuple(x) for x in sec[1:]}
        if sec[0] == ":goal": goal = [tuple(x) for x in sec[1][1:]]
    return init, goal

def parse_plan(path):
    return [tuple(re.sub(r"[()]", "", l).lower().split()) for l in open(path) if l.strip().startswith("(")]

def validate(domain_path, problem_path, plan, verbose=True):
    actions = load_domain(domain_path)
    state, goal = load_problem(problem_path)
    state = set(state)
    for i, (name, *args) in enumerate(plan, 1):
        params, pre, add, dele = actions[name]
        sub = dict(zip(params, args))
        g = lambda f: tuple([f[0]] + [sub.get(a, a) for a in f[1:]])
        missing = [g(f) for f in pre if g(f) not in state]
        if missing:
            if verbose: print(f"  step {i:2d} ({name} {' '.join(args)}) INVALID, unmet preconditions: {missing}")
            return False, state
        for f in dele: state.discard(g(f))
        for f in add: state.add(g(f))
    ok = all(f in state for f in goal)
    return ok, state

def report_final(state, goal_ok):
    print("  Final state facts of interest:")
    for pred in ("rover-at", "has-drill", "bay-empty", "stored", "rock-at", "drill-at"):
        facts = sorted(" ".join(f) for f in state if f[0] == pred)
        print(f"    {pred:<10}: {facts}")
    rocks_base = sorted(f[1] for f in state if f[0] == "rock-at" and f[2] == "base")
    print(f"  Rocks at Base : {rocks_base}")
    print(f"  Both bays empty : {('bay-empty','bay1') in state and ('bay-empty','bay2') in state}")
    print(f"  Rover at Base   : {('rover-at','curiosity','base') in state}")
    print(f"  ==> GOAL SATISFIED: {goal_ok}")

# ----------------------------------------------------------------------------------------
def run_planner(ppath):
    """returns (plan list, expanded states, search time, raw log)"""
    if ARGS.planner == "fd":
        tmp = tempfile.mktemp(suffix=".plan")
        cmd = [sys.executable, ARGS.fd_path, "--plan-file", tmp, DOMAIN, ppath, "--search", fdsearch]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        log = proc.stdout + proc.stderr
        plan = parse_plan(tmp); os.remove(tmp)
        expanded = int(re.search(r"Expanded (\d+) state", log).group(1))
        stime = float(re.search(r"Search time: ([\d.e+-]+)s", log).group(1))
    else:
        cmd = [sys.executable, "-m", "pyperplan", "-l", "info", "-s", search, "-H", heur, DOMAIN, ppath]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        log = proc.stdout + proc.stderr
        soln = ppath + ".soln"
        plan = parse_plan(soln); os.remove(soln)
        expanded = int(re.search(r"(\d+) Nodes expanded", log).group(1))
        stime = float(re.search(r"Search time: ([\d.e+-]+)", log).group(1))
    return plan, expanded, stime, log

results = []
for scen, pfile in SCENARIOS.items():
    ppath = os.path.join(HERE, pfile)
    for cname, (search, heur, fdsearch, tag) in CONFIGS.items():
        print("=" * 90 + f"\nPlanner: {ARGS.planner} | Scenario: {scen:<9} | Configuration: {cname}\n" + "=" * 90, flush=True)
        t0 = time.time()
        plan, expanded, stime, log = run_planner(ppath)
        wall = time.time() - t0
        open(os.path.join(OUT, f"{scen}_{tag}.log"), "w").write(log)
        with open(os.path.join(OUT, f"{scen}_{tag}.plan"), "w") as fh:
            fh.write("\n".join("(" + " ".join(a) + ")" for a in plan) + "\n")
        n_moves = sum(1 for a in plan if a[0] == "move")
        print("Plan:")
        for i, a in enumerate(plan, 1):
            print(f"  {i:2d}. ({' '.join(a)})")
        print(f"\nPlan length (total number of actions) : {len(plan)}   (moves: {n_moves}, non-move: {len(plan)-n_moves})")
        print(f"States expanded                        : {expanded}")
        print(f"Planning (search) time                 : {stime:.3f} s   (wall clock incl. translation: {wall:.2f} s)")
        print("\nGoal verification (step-by-step simulation):")
        ok, final = validate(DOMAIN, ppath, plan)
        report_final(final, ok)
        results.append((scen, cname, len(plan), expanded, stime))

print("\n" + "=" * 90 + "\nSUMMARY\n" + "=" * 90)
print(f"{'Scenario':<10}{'Configuration':<42}{'Plan len':>9}{'Expanded':>10}{'Time (s)':>10}")
for sc, c, l, e, t in results:
    print(f"{sc:<10}{c:<42}{l:>9}{e:>10}{t:>10.3f}")
