# Group Assignment 2  (AI)
Group Name : SYNTAX-ERROR
Group members (manish    B24ME029
               sarup     B24ME042
               nitesh    B24MT016
               chingkhei B24ME013
               mohit     B24CS030)

## Folder layout
- Problem1_BayesianNetwork/  problem1_bayesian_network.py, output_log.txt, output/ (png, csv, datasets)
- Problem2_PDDL/             Domain.pddl, Problem.pddl, Problem_extended.pddl, run_planner.py, planner_output*/ 
- Problem3_Prolog/           royal_archive_access.pl, output.txt
- Analysis_Report.md         answers to all analysis questions

## How to run
Problem 1:  pip install pgmpy numpy pandas matplotlib networkx ;  python problem1_bayesian_network.py
Problem 2:  Fast Downward (fast):  python run_planner.py --planner fd --fd-path /path/to/fast-downward.py
            pyperplan (pip install pyperplan): python run_planner.py --planner pyperplan --scenarios base
            (pyperplan A* on the extended problem takes hours; Fast Downward needs ~2 minutes.)
Problem 3:  swipl royal_archive_access.pl      (SWI-Prolog, swi-prolog.org)
Take screenshots of each console output + the png plots for submission.
