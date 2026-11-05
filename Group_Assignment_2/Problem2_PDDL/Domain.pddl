;; Mars Rover sample-collection domain  (requirements: :strips :typing only)
(define (domain mars-rover)
  (:requirements :strips :typing)

  (:types
    location rock bay rover drill)

  (:predicates
    (connected ?from - location ?to - location)  ; directed edge: rover may move ?from -> ?to
    (rover-at ?r - rover ?l - location)          ; rover position
    (rock-at ?k - rock ?l - location)            ; rock lying on the ground at a location
    (drill-at ?d - drill ?l - location)          ; drill lying on the ground at a location
    (soft ?k - rock)                             ; soft rock : can be collected directly
    (hard ?k - rock)                             ; hard rock : needs the drill
    (has-drill ?r - rover ?d - drill)            ; rover is carrying the drill (permanent)
    (bay-empty ?b - bay)                         ; storage bay is free
    (stored ?k - rock ?b - bay))                 ; rock is held in a bay

  ;; Move along a directed edge. Two-way routes are given as two connected facts,
  ;; the one-way slope SiteC -> SiteD as a single fact.
  (:action move
    :parameters (?r - rover ?from - location ?to - location)
    :precondition (and (rover-at ?r ?from) (connected ?from ?to))
    :effect (and (rover-at ?r ?to) (not (rover-at ?r ?from))))

  ;; Pick up the drill at the current location; it is never dropped again.
  (:action pick-drill
    :parameters (?r - rover ?d - drill ?l - location)
    :precondition (and (rover-at ?r ?l) (drill-at ?d ?l))
    :effect (and (has-drill ?r ?d) (not (drill-at ?d ?l))))

  ;; Soft rocks can be collected directly into an empty bay.
  (:action collect-soft
    :parameters (?r - rover ?k - rock ?l - location ?b - bay)
    :precondition (and (rover-at ?r ?l) (rock-at ?k ?l) (soft ?k) (bay-empty ?b))
    :effect (and (stored ?k ?b) (not (rock-at ?k ?l)) (not (bay-empty ?b))))

  ;; Hard rocks additionally require the rover to be carrying the drill.
  (:action collect-hard
    :parameters (?r - rover ?k - rock ?l - location ?b - bay ?d - drill)
    :precondition (and (rover-at ?r ?l) (rock-at ?k ?l) (hard ?k) (bay-empty ?b) (has-drill ?r ?d))
    :effect (and (stored ?k ?b) (not (rock-at ?k ?l)) (not (bay-empty ?b))))

  ;; Drop a stored rock at the rover's current location, freeing the bay.
  (:action deposit
    :parameters (?r - rover ?k - rock ?l - location ?b - bay)
    :precondition (and (rover-at ?r ?l) (stored ?k ?b))
    :effect (and (rock-at ?k ?l) (bay-empty ?b) (not (stored ?k ?b))))
)
