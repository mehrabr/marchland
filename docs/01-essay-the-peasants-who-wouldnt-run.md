# the peasants who wouldn't run

Total War will sell you a unit of peasants who hold formation while cavalry hits them from behind, their general dies, and the units beside them rout. They stand there losing a fixed percentage of a bar. Bannerlord battles end with 96.3% of participants dead. Crusader Kings calls 25% casualties a normal afternoon. The historical norm for the *losing* side of a pre-modern battle, before the rout, was under ten.

These aren't bugs. They shipped in every major release for thirty years.

---

I.

A military historian named Bret Devereaux spent years documenting the gap. The general in these games is a flying camera with telepathy; the real one saw dust, heard noise, and sent riders who arrived with thirty-minute-old news. Armies in these games walk anywhere their movement points reach; real ones were chained to a spiderweb of roads by 60,000 kilograms of daily food and fodder. Battles in these games happen when you click an enemy stack; real battles required both sides to agree, which is why most campaigns contained zero of them and a great deal of burning. Morale in these games is a fuel gauge; the real thing was two different phenomena — whether men believed in the cause, and whether they could bear to leave each other — and battles ended when the second one snapped, in minutes, with most of the killing coming after.

The list runs longer. The interesting question isn't the list. It's why the list survives contact with developers who have read it.

---

II.

The standard answer is fun. Players want control, control needs obedient units, obedient units need stats, and the whole edifice follows. I believed this for a while.

Then I traced where the stats came from. The melee-attack value descends from tabletop wargames, which descend from rigid Kriegsspiel, whose dice tables had umpires "reduced to clerks" by 1870 and produced results that defied military logic — the Prussians said so themselves, and replaced the tables with expert judgment, which worked for about a decade until the experts retired and the tables crept back. The unit roster with its tiers descends from the same century's anthropology: martial races, warrior peoples, cultures that are simply *better at fighting* — laundered through forty years of game design until a +2 to attack stopped looking like a claim about anyone.

And the tech tree. Europa Universalis III hard-coded research penalties for every non-"Latin" culture group, growing with distance from Western Europe, curable only by a mechanic called "westernize." That's not a balance decision. That's the Whig theory of history — progress as a single ladder, Europe at the top — compiled into rules and executed a million times a night.

"Nobody playing thinks about this." Correct. That's how compiled assumptions work.

---

III.

So I tried the opposite experiment: take the historiography seriously and see if a game survives. Not as flavor — as physics. The rule that made it possible is one sentence: every number that differs between two forces must answer the question *what in-world action would change you?* Drill-days. Calories. Armor somebody paid for. Roads somebody built. If no action answers, the number is an essence, and essences are banned.

A soldier in this engine dies like this:

```
λ = λ₀ · h(fatigue) · h(error-under-load) + λx · exposure
```

λ₀ is identical for every human who ever lived. A Zulu, a serjeant, and an ashigaru at equal fatigue and exposure generate openings at the same rate. The dice are the same dice. What differs is everything with a receipt: the drill that lowers your error rate, the mail that turns a thrust into a bruise, the file-closer whose job is sealing the hole you'd otherwise die in.

Randomness was never the lie. The loaded dice were.

---

IV.

Does it work? We ran it against battles with known answers, constants frozen across all of them.

Isandlwana: the engine reproduces not just the Zulu victory but the *sequence* — in 16 of 16 seeds the flank farthest from the ammunition point goes silent before the line breaks, with no rule that says so. Agincourt: 1,270 French taken prisoner in an engine that has no surrender rule; they're men routing into deep mud in sixty pounds of steel, flight speed below their pursuers' walk. Form the British into a square at Isandlwana — one drill flag — and the outcome distribution flips, which is what the counterfactual literature predicted.

And Hastings we got wrong, instructively: the engine called it decided 12 times in 12 when the books call it a near-run thing. We were partway through fixing the engine when someone checked the target. "Near-run thing" is Wellington. About Waterloo. Our calibration target for 1066 was a quote from the wrong millennium, and the sources for Hastings are thin, late, and partisan — chroniclers say battles hung in the balance the way every senator is famed for eloquence. The engine still has a real miss there (too many die before the break). The target had a miss too.

---

V.

Which is the thing the experiment was secretly about. A simulation is a historiographical text. Its mechanics are claims about how history works whether the designer intended any or not — the tech tree claims progress is a ladder, the morale bar claims armies are batteries, the stat block claims peoples have essences. You don't get to skip choosing a theory of history. You only get to choose whether you know which one you compiled.

Ours, for the record: materials and institutions set the structure, chance picks among the structure's openings, and the records lie in period-appropriate ways — the game's own chronicle inflates enemy numbers, and its post-battle replay will show you the king felled by an arrow, because that's what the dispatches said, until you scrub to the trace layer and find a sword, in the ditch, after the wall broke.

The peasants, in our engine, run. Eleven percent of them die first.
