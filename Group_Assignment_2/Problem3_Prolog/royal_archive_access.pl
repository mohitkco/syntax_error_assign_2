%% =====================================================================================
%%  PROBLEM 3 : ROYAL ARCHIVE ACCESS VERIFICATION USING RESOLUTION REFUTATION
%%  Group Name : SYNTAX-ERROR
%%  Group members : 
%%               manish    B24ME029
%%               sarup     B24ME042
%%               nitesh    B24MT016
%%               chingkhei B24ME013
%%               mohit     B24CS030
%%
%%  Run (SWI-Prolog):   swipl royal_archive_access.pl
%%                  or: swipl -q -g main -t halt royal_archive_access.pl
%% =====================================================================================
%%  PREDICATES : archivist(x)      x is an archivist
%%               trusted(x)        x is trusted
%%               verifies(x,r)     x verifies record r
%%               access(x,r)       x has access to record r
%%               sealed(r)         record r is sealed
%%               permitted(x,r)    x is permitted to inspect r  (NOT the same as inspecting)
%%               inspects(x,r)     x actually inspects r
%%               finds_mark(x,r)   x finds a hidden mark in r
%%               stored(r,a)       record r is stored in archive a
%%  CONSTANTS  : mira, scroll_7, royal_archive
%%  VARIABLES  : x, r   (Prolog variables; they are universally quantified)
%% =====================================================================================

:- initialization(main, main).
:- use_module(library(lists)).
:- use_module(library(apply)).

%% Formula language used below:
%%   all(X,F)  ex(X,F)  imp(A,B)  and(A,B)  or(A,B)  not(A)   atoms: archivist(X) ...

%% -------------------------------------------------------------------------------------
%% Step 1: Predicate logic representation
%% -------------------------------------------------------------------------------------
% 1. Every archivist who verifies a record is trusted.
fol(1, all(X, all(R, imp(and(archivist(X), verifies(X,R)), trusted(X))))).
% 2. Every trusted person who has access to a sealed record is permitted to inspect it.
fol(2, all(X, all(R, imp(and(trusted(X), and(access(X,R), sealed(R))), permitted(X,R))))).
% 3. Anyone who inspects a record and finds a hidden mark in it verifies that record.
fol(3, all(X, all(R, imp(and(inspects(X,R), finds_mark(X,R)), verifies(X,R))))).
% 4. Every record stored in the royal archive is sealed.
fol(4, all(R, imp(stored(R, royal_archive), sealed(R)))).
% 5. scroll_7 is stored in the royal archive.
fol(5, stored(scroll_7, royal_archive)).
% 6. Mira has access to scroll_7.
fol(6, access(mira, scroll_7)).
% 7. Mira inspects scroll_7 and finds a hidden mark in it.
fol(7, and(inspects(mira, scroll_7), finds_mark(mira, scroll_7))).
% 8. Mira is an archivist.
fol(8, archivist(mira)).

% Goal to prove
goal(trusted(mira)).

%% -------------------------------------------------------------------------------------
%% Step 2: Negation of the goal  (added to the knowledge base as formula 9)
%% -------------------------------------------------------------------------------------
negated_goal(not(G)) :- goal(G).

%% -------------------------------------------------------------------------------------
%% Step 3: Implication removal      A -> B   ==>   ~A v B
%% -------------------------------------------------------------------------------------
rm_imp(all(X,F), all(X,G)) :- !, rm_imp(F, G).
rm_imp(ex(X,F),  ex(X,G))  :- !, rm_imp(F, G).
rm_imp(imp(A,B), or(not(A1),B1)) :- !, rm_imp(A, A1), rm_imp(B, B1).
rm_imp(and(A,B), and(A1,B1)) :- !, rm_imp(A, A1), rm_imp(B, B1).
rm_imp(or(A,B),  or(A1,B1))  :- !, rm_imp(A, A1), rm_imp(B, B1).
rm_imp(not(A),   not(A1))    :- !, rm_imp(A, A1).
rm_imp(A, A).

%% -------------------------------------------------------------------------------------
%% Step 4: Move negation inward (De Morgan, quantifier duality, double negation)
%% -------------------------------------------------------------------------------------
nnf(all(X,F), all(X,G)) :- !, nnf(F, G).
nnf(ex(X,F),  ex(X,G))  :- !, nnf(F, G).
nnf(and(A,B), and(A1,B1)) :- !, nnf(A, A1), nnf(B, B1).
nnf(or(A,B),  or(A1,B1))  :- !, nnf(A, A1), nnf(B, B1).
nnf(not(not(A)), B)       :- !, nnf(A, B).
nnf(not(and(A,B)), or(A1,B1))  :- !, nnf(not(A), A1), nnf(not(B), B1).
nnf(not(or(A,B)),  and(A1,B1)) :- !, nnf(not(A), A1), nnf(not(B), B1).
nnf(not(all(X,F)), ex(X,G))    :- !, nnf(not(F), G).
nnf(not(ex(X,F)),  all(X,G))   :- !, nnf(not(F), G).
nnf(A, A).                                   % atom or negated atom

%% -------------------------------------------------------------------------------------
%% Step 5: Standardize variables apart (every formula gets its own fresh variables)
%% -------------------------------------------------------------------------------------
standardize(Fs, Gs) :- maplist(copy_term, Fs, Gs).

%% -------------------------------------------------------------------------------------
%% Step 6: Skolemization (existentials -> Skolem constants/functions of enclosing universals)
%% -------------------------------------------------------------------------------------
skolemize(F, G) :- sk(F, [], G).
sk(all(X,F), U, all(X,G)) :- !, sk(F, [X|U], G).
sk(ex(X,F), U, G) :- !,
    gensym(sk, Name),
    (   U == [] -> X = Name
    ;   reverse(U, Us), X =.. [Name|Us] ),
    sk(F, U, G).
sk(and(A,B), U, and(A1,B1)) :- !, sk(A, U, A1), sk(B, U, B1).
sk(or(A,B),  U, or(A1,B1))  :- !, sk(A, U, A1), sk(B, U, B1).
sk(A, _, A).

%% -------------------------------------------------------------------------------------
%% Step 7: CNF  (drop universal quantifiers, distribute  v  over  &)  -> list of clauses
%%         literal = p(Atom) (positive) | n(Atom) (negative);   clause = list of literals
%% -------------------------------------------------------------------------------------
cnf(all(_,F), C) :- !, cnf(F, C).
cnf(and(A,B), C) :- !, cnf(A, CA), cnf(B, CB), append(CA, CB, C).
cnf(or(A,B),  C) :- !, cnf(A, CA), cnf(B, CB), cross(CA, CB, C).   % no findall: it would copy variables
cnf(not(A), [[n(A)]]) :- !.
cnf(A, [[p(A)]]).

% cross product of two clause lists (v distributes over &), keeping shared variables
cross([], _, []).
cross([P|Ps], CB, R) :- maplist(join_clause(P), CB, R1), cross(Ps, CB, R2), append(R1, R2, R).
join_clause(P, Q, K) :- append(P, Q, K0), dedup(K0, K).

dedup([], []).
dedup([L|T], R) :- ( memberchk_eq(L, T) -> dedup(T, R) ; dedup(T, R0), R = [L|R0] ).
memberchk_eq(X, [Y|T]) :- ( X == Y -> true ; memberchk_eq(X, T) ).

%% -------------------------------------------------------------------------------------
%% Pretty printing helpers (ASCII:  ~ not, & and, | or, -> implies, all(x) / ex(x))
%% -------------------------------------------------------------------------------------
pp(all(X,F)) :- !, write('all('), pw(X), write(') '), pp(F).
pp(ex(X,F))  :- !, write('ex('),  pw(X), write(') '), pp(F).
pp(imp(A,B)) :- !, write('('), pp(A), write(' -> '), pp(B), write(')').
pp(and(A,B)) :- !, write('('), pp(A), write(' & '),  pp(B), write(')').
pp(or(A,B))  :- !, write('('), pp(A), write(' | '),  pp(B), write(')').
pp(not(A))   :- !, write('~'), pp(A).
pp(A)        :- pw(A).
pw(T) :- write_term(T, [numbervars(true), quoted(false)]).

pcl([]) :- !, write('[]  (EMPTY CLAUSE)').
pcl(C)  :- write('{ '), pcl_(C), write(' }').
pcl_([L]) :- !, plit(L).
pcl_([L|T]) :- plit(L), write(',  '), pcl_(T).
plit(p(A)) :- !, pw(A).
plit(n(A)) :- write('~'), pw(A).

% name the variables of a term X,Y,Z,U,V,W ... (local naming, restarts for every formula)
local_names(T) :-
    term_variables(T, Vs),
    Names = ['X','Y','Z','U','V','W','S','T'],
    bind_names(Vs, Names).
bind_names([], _).
bind_names([V|Vs], [N|Ns]) :- V = '$VAR'(N), bind_names(Vs, Ns).

show_local(Prefix, Fs) :-
    forall(nth1(I, Fs, F),
           \+ \+ ( local_names(F), format("  ~w~d: ", [Prefix, I]), pp(F), nl )).
show_global(Prefix, Fs) :-            % one shared numbering A,B,C,... -> proves variables are distinct
    \+ \+ ( numbervars(Fs, 0, _),
            forall(nth1(I, Fs, F), ( format("  ~w~d: ", [Prefix, I]), pp(F), nl )) ).
show_clauses(Cs) :-
    \+ \+ ( numbervars(Cs, 0, _),
            forall(member(Id-C, Cs), ( format("  C~d  ", [Id]), pcl(C), nl )) ).

banner(Txt) :- format("~n~`=t~78|~n~w~n~`=t~78|~n", [Txt]).

%% -------------------------------------------------------------------------------------
%% Step 8: Resolution refutation (given-clause loop, set-of-support = negated goal)
%% -------------------------------------------------------------------------------------
% resolve(+C1, +C2, -Resolvent, -ResolvedAtom): standardise apart, unify complementary literals
resolve(C1, C2, R, Atom) :-
    copy_term(C1, D1), copy_term(C2, D2),
    select(L1, D1, Rest1), select(L2, D2, Rest2),
    complementary(L1, L2),
    ( L1 = p(Atom) -> true ; L1 = n(Atom) ),
    append(Rest1, Rest2, R0), dedup(R0, R),
    \+ tautology(R).
complementary(p(A), n(B)) :- A = B.
complementary(n(A), p(B)) :- A = B.
tautology(R) :- member(p(A), R), member(n(B), R), A == B.

% All: list of c(Id, Clause, Justification);  Queue: ids of set-of-support clauses still to use
refute(All0, Queue0, Next0, All, Result) :-
    (   Queue0 = [] -> All = All0, Result = failed
    ;   Queue0 = [G|Queue1],
        member(c(G, GC, _), All0),
        findall(r(Id2, R, A),
                ( member(c(Id2, C2, _), All0), Id2 \== G, resolve(GC, C2, R, A) ),
                Rs),
        process(Rs, G, All0, Queue1, Next0, All1, Queue2, Next1, Done),
        (   Done = yes(EId) -> All = All1, Result = proved(EId)
        ;   refute(All1, Queue2, Next1, All, Result) )
    ).

process([], _, All, Q, N, All, Q, N, no).
process([r(Id2, R, A)|Rs], G, All0, Q0, N0, All, Q, N, Done) :-
    (   R == []
    ->  Id = N0, N1 is N0 + 1,
        append(All0, [c(Id, [], res(G, Id2, A))], All),
        print_resolvent(Id, G, Id2, A, []),
        Q = Q0, N = N1, Done = yes(Id)
    ;   \+ \+ ( member(c(_, C, _), All0), C =@= R )     % variant already known -> skip
    ->  process(Rs, G, All0, Q0, N0, All, Q, N, Done)
    ;   Id = N0, N1 is N0 + 1,
        append(All0, [c(Id, R, res(G, Id2, A))], All1),
        print_resolvent(Id, G, Id2, A, R),
        append(Q0, [Id], Q1),
        process(Rs, G, All1, Q1, N1, All, Q, N, Done)
    ).

print_resolvent(Id, G, Id2, A, R) :-
    \+ \+ ( numbervars(A-R, 0, _),
            format("  C~d = Resolve(C~d, C~d) on ", [Id, G, Id2]), pw(A), format("~n        => "), pcl(R), nl ).

% collect the clauses that really contribute to the empty clause
ancestors(Id, All, Set) :-
    member(c(Id, _, J), All),
    (   J = res(A, B, _) -> ancestors(A, All, SA), ancestors(B, All, SB),
                            append([SA, SB, [Id]], S0), sort(S0, Set)
    ;   Set = [Id] ).

print_proof(All, EId) :-
    ancestors(EId, All, Used),
    forall(( member(Id, Used), member(c(Id, C, J), All) ),
           \+ \+ ( numbervars(C-J, 0, _),
                   format("  C~d  ", [Id]), pcl(C),
                   ( J = res(A, B, At) -> format("     [Resolve C~d, C~d on ", [A, B]), pw(At), write(']')
                   ; J = input(L) -> format("     [~w]", [L]) ; true ), nl )).

%% -------------------------------------------------------------------------------------
%% main : run Steps 1 - 8
%% -------------------------------------------------------------------------------------
main :-
    banner("STEP 1 : Predicate-logic representation (KB)"),
    findall(F, fol(_, F), F1), show_local("F", F1),
    format("  Goal to prove: "), goal(G), pp(G), nl,

    banner("STEP 2 : Negation of the goal (added as formula 9)"),
    negated_goal(NG), append(F1, [NG], F2),
    \+ \+ ( local_names(NG), format("  F9: "), pp(NG), nl ),

    banner("STEP 3 : Implication removal  (A -> B  becomes  ~A | B)"),
    maplist(rm_imp, F2, F3), show_local("F", F3),

    banner("STEP 4 : Negation moved inward"),
    maplist(nnf, F3, F4), show_local("F", F4),

    banner("STEP 5 : Standardise variables apart (distinct names across all formulas)"),
    standardize(F4, F5), show_global("F", F5),

    banner("STEP 6 : Skolemisation"),
    maplist(skolemize, F5, F6), show_global("F", F6),
    format("  (No existential quantifiers occur, so no Skolem constants/functions are needed.)~n"),

    banner("STEP 7 : Conjunctive normal form -> clause set"),
    findall(C, ( member(F, F6), cnf(F, Cs), member(C, Cs) ), Clauses),
    length(Clauses, NC), numlist(1, NC, IdL),
    pairs_keys_values(Numbered, IdL, Clauses), show_clauses(Numbered),
    format("  (C~d is the negated goal.)~n", [NC]),

    banner("STEP 8 : Resolution refutation (set of support = negated goal)"),
    findall(c(I, C, input(kb)), member(I-C, Numbered), All0),
    NC1 is NC + 1,
    refute_start(All0, NC, NC1, All, Result),
    (   Result = proved(EId)
    ->  banner("PROOF TRACE (only the clauses that contribute to the empty clause)"),
        print_proof(All, EId),
        format("~nThe EMPTY CLAUSE [] has been derived.~n"),
        format("KB + ~~trusted(mira) is unsatisfiable  =>  trusted(mira) follows from the KB. QED.~n")
    ;   format("~nNo refutation found (goal does not follow).~n") ).

refute_start(All0, GoalId, Next, All, Result) :-
    format("  Input clauses are C1..C~d; resolvents are numbered from C~d.~n~n", [GoalId, Next]),
    refute(All0, [GoalId], Next, All, Result).
