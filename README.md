# MARCHLAND — Complete Project Archive

A statless historical-warfare simulation and the strategy game built on it. Twenty-one design
documents, three validated simulation models, a graded validation battery, and the buildable spec.

## Start here
- **00-BIBLE.md** — the complete buildable specification. Laws, architecture, frozen constants,
  schemas, the battery, game design, presentation, and the milestone plan for a Claude Code
  prototype (Prototype 0: the 1415 vertical slice) through the Unity path.
- **01-essay-the-peasants-who-wouldnt-run.md** — the argument: why strategy games are bad
  history, why it isn't laziness, and what taking the historiography seriously produces.

## docs/ — the reasoning (read in order if reading deep)
main design doc → A resolver decision → B the statless model → C worked walkthrough →
D the interrogation loop → E adjudication + first battle experiments → F architecture/build →
G player walkthrough vs Total War → H interface (three rooms) → I POV (chronicler's eye) →
J the commission & stations → K officers & the chain → L the Day Layer spec → M loops &
the judgment of men → N personas & modularity → O progression without the ladder →
P the theory of history → Q rupture starts + the red-team review → R answering the review
(siege battery, graded calibration) → S the march model + the 1415 chain → T three logistics
loops (water, the eating train, the registry) → U the Table and the Window.

## code/ — reference implementations (Python; targets for the Rust core port)
- marchland_toy.py + scenarios.py + run.py — the BP-Lattice battle resolver (field battles,
  escalades, breaches; stochastic + deterministic modes)
- siege_clock.py — the operational siege (dual clocks, summons-and-terms)
- march_model.py — the Day Layer march (carrying equation, water, modes, entropy flows)

## results/ — acceptance baselines the bible's claims cite
res_*.json (ensemble outputs per scenario) · aggregate.json · assault_results.json ·
calibration_regrade.json (every target as [range, source-grade, achieved, verdict])

## The standard
Calibrate once, freeze, test everything; targets carry source-criticism; misses are findings.
Current real misses (open, ordered): Hastings casualty shape (needs phase pacing), the square's
full hold (needs relief roles), Isandlwana pursuit share. Everything else on the ledger: BIBLE Part IX.
