;; Base scenario: Rock1..Rock5
(define (problem mars-rover-base)
  (:domain mars-rover)

  (:objects
    base sitea siteb sitec sited sitee sitef - location
    rock1 rock2 rock3 rock4 rock5 - rock
    bay1 bay2 - bay
    curiosity - rover
    drill1 - drill)

  (:init
    ;; two-way routes (both directions)
    (connected base sitea)  (connected sitea base)
    (connected base siteb)  (connected siteb base)
    (connected sitea sitec) (connected sitec sitea)
    (connected siteb sited) (connected sited siteb)
    (connected sitec sitee) (connected sitee sitec)
    (connected sited sitee) (connected sitee sited)
    (connected sitee sitef) (connected sitef sitee)
    ;; one-way steep slope SiteC -> SiteD only
    (connected sitec sited)

    (rover-at curiosity base)
    (drill-at drill1 sitee)
    (bay-empty bay1) (bay-empty bay2)

    (soft rock1) (soft rock2) (hard rock3) (soft rock4) (hard rock5)
    (rock-at rock1 sitea) (rock-at rock2 siteb) (rock-at rock3 sitec)
    (rock-at rock4 sited) (rock-at rock5 sitef))

  ;; all rocks at Base, both bays empty, rover at Base
  (:goal (and
    (rock-at rock1 base) (rock-at rock2 base) (rock-at rock3 base)
    (rock-at rock4 base) (rock-at rock5 base)
    (bay-empty bay1) (bay-empty bay2)
    (rover-at curiosity base))))
