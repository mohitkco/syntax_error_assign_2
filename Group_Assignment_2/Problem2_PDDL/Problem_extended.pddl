;; Extended scenario: + Rock6 (soft, SiteE), Rock7 (hard, SiteF); dust storm closes Base<->SiteB
(define (problem mars-rover-extended)
  (:domain mars-rover)

  (:objects
    base sitea siteb sitec sited sitee sitef - location
    rock1 rock2 rock3 rock4 rock5 rock6 rock7 - rock
    bay1 bay2 - bay
    curiosity - rover
    drill1 - drill)

  (:init
    (connected base sitea)  (connected sitea base)
    ;; Base <-> SiteB REMOVED (dust storm)
    (connected sitea sitec) (connected sitec sitea)
    (connected siteb sited) (connected sited siteb)
    (connected sitec sitee) (connected sitee sitec)
    (connected sited sitee) (connected sitee sited)
    (connected sitee sitef) (connected sitef sitee)
    (connected sitec sited)                         ; one-way slope

    (rover-at curiosity base)
    (drill-at drill1 sitee)
    (bay-empty bay1) (bay-empty bay2)

    (soft rock1) (soft rock2) (hard rock3) (soft rock4) (hard rock5)
    (soft rock6) (hard rock7)
    (rock-at rock1 sitea) (rock-at rock2 siteb) (rock-at rock3 sitec)
    (rock-at rock4 sited) (rock-at rock5 sitef)
    (rock-at rock6 sitee) (rock-at rock7 sitef))

  (:goal (and
    (rock-at rock1 base) (rock-at rock2 base) (rock-at rock3 base)
    (rock-at rock4 base) (rock-at rock5 base) (rock-at rock6 base) (rock-at rock7 base)
    (bay-empty bay1) (bay-empty bay2)
    (rover-at curiosity base))))
