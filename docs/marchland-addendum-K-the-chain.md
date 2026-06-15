# MARCHLAND — Addendum K: The Chain
### Officers and command across army cultures — authority as a typed graph, capability as roles, orders as interpretation

**Extends:** Addendum J's stations (where *you* stand) with the question of everyone between you and the spear: how officers and the chain of command work, and how the chain itself differs by culture. **The constraint, restated:** no officer may be a leadership aura. Devereaux's Officers installment (Total Generalship IIIb) supplies the positive model — junior officers were the army's actual control system, making real decisions without orders (his sources show centurions spontaneously halting a charge begun too early, re-forming the line, and charging again at the proper distance, all uncommanded; and Caesar's own rear ranks executing an about-face that Caesar, dismounted, may not even have ordered or seen). An army *is* its officer layer. The design has to make that literally true.

---

## 1 — The reframe

Total War's officer is a buff radius. Ours is three different things braided together, and the braid is where the cultures differ:

**Authority** — *why* this man is obeyed — which is a typed edge in a graph, not a number. **Capability** — *what* this unit can be ordered to do — which lives in roles the officers hold, not in the unit's stat block. **Judgment** — what this officer does when no order has arrived or the order no longer fits — which is his appraisal, his priors, and his culture's initiative norms.

The chain of command is then: a graph of typed authority edges, carrying messages that are *interpreted, not executed*, between nodes that keep the army's repertoire alive and make their own decisions in the gaps. Every clause of that sentence is a mechanic below.

---

## 2 — The officer node

```
OFFICER
  role            from the doctrine file: centurion | optio | file-closer |
                  banner-bearer | magnate | serjeant | induna | tsukai-ban
                  rider | staff officer | political officer ...
                  → roles KEY the repertoire (see §3b) and set station defaults
  authority_in    the edge(s) by which he is obeyed — TYPED:
                    institutional   (office + pay; survives his death via
                                     succession rule; Rome's centurionate)
                    personal-feudal (his men are HIS; your edge reaches HIM
                                     only, politically, conditionally)
                    kinship/age-set (obeyed as senior of the cohort that
                                     grew up together; Zulu ibutho)
                    charismatic     (the warband bond; dies with him)
                    purchased       (the commission as property; obedience
                                     institutional, respect earned separately)
  priors          class E: appraisal priors from his actual record
                  (battles survived, holds witnessed, routs witnessed)
  initiative      class D norm, cultural: act-then-report ↔ ask-then-act
  bonds           edges into the lattice: his anchor radius is his
                  relationships, not a glow
  record          his service history — the player-facing object; there is
                  no character sheet, there is a FILE
  trust           his running ledger about YOU (see §4)
  succession      what happens to his edges when he falls (see §3e)
```

Nothing here is a quality coefficient. The "good officer" decomposes entirely: a veteran centurion is good because his priors are calm, his drill enables actions, his institutional edge survives him, and forty men's bond edges route through him — every clause purchasable, every clause destructible.

---

## 3 — Five mechanics that fall out

**a. Orders bind edges, not units.** An order's execution semantics depend on the edge type it travels. Down an institutional edge, "refuse the left" is an instruction to a subordinate whose office exists to receive it. Down a personal-feudal edge, the same words are a *request to a peer* — the Earl commands his own retinue absolutely, and you command the Earl approximately; his compliance is conditional on the plan he agreed to, his standing with you, and what his own eyes tell him mid-battle. This single typing rule generates the deepest historical difference between armies without a single stat: the Roman consul's order reaches the maniple through four reliable links; the feudal king's "chain" is one political link deep, repeated twelve times, and Hastings' historiographical arguments about whether anyone *could* have stopped the fyrd are arguments about exactly this.

**b. Capability lives in roles — articulation as data.** A doctrine file doesn't just list actions; it lists *which roles must be alive and in place* for each action to be orderable. Line relief requires file-closer roles. The triplex acies' passage-of-lines requires the centurion/optio pair. The feigned withdrawal requires riders who can carry the recall and wing officers drilled to turn it. Strip the roles and the actions grey out — which means **killing officers deletes capability, locally and immediately**: a century that loses its centurion doesn't fight 10% worse, it *loses menu items* and falls back on what leaderless men do, which the appraisal engine already models. The Isandlwana square's missing relief drill (Addendum E) was secretly a missing *role*, and the engine experiments have already priced what its absence costs.

**c. Orders are interpreted against the recipient's belief DB, not the sender's.** A dispatch references landmarks, units, and intent — and the receiving officer resolves every reference against *his* picture of the field, which is minutes older or younger than yours and differently wrong. "Advance to the guns" is a different order on the recipient's hill than on the sender's. Balaclava is not a scripted event in this engine; it is a standing possibility of the message model, and the famous ambiguity of Raglan's fourth order becomes the genre's first *mechanically honest* light-brigade. Doctrine sets the interpretation norm as class D data: intent-style cultures (act on the purpose) versus literal-style cultures (act on the words) fail differently, and both fail.

**d. Officers propose — the opportunity feed at battle scale.** Subordinates are not idle between your orders. They report, and they *ask*: "Sir Aldric requests leave to take the mill before their archers occupy it." The campaign's central interaction (the AI offers, you sponsor) descends into the battle as a rhythm of proposals arriving at rider latency, which is what command from the Knot or Hill mostly *was* — and per the culture's initiative norm, officers will sometimes act first and report after, which is the centurions halting the charge: the army's nervous system firing reflexes your brain learns about later. The AI implementation is already specified: each officer evaluates his local situation with Front-tier lookahead (Addendum F), so his proposals are *reasoned in the same physics as the world*, and his reasons can be shown.

**e. Succession, and the dangling edge.** When an officer falls, his edges resolve by his culture's succession rule. Institutional edges promote (the optio steps up; the century mourns and functions — by design, this is *the point* of institutional armies and the game should let the player feel the Roman machine absorb losses that would behead anyone else's wing). Kinship edges pass to the next senior age-mate, with a shudder. Charismatic edges *dangle*: the warband that loses its lord is suddenly a crowd of grieving armed men whose authority graph points at a corpse, and what they do next — avenge, flee, follow the son if the son is present and credible — is an appraisal event the whole battle can hinge on. The magnate's death is therefore a different *kind* of event from the centurion's, not a bigger morale penalty, and the feudal player learns to fear it the way the sources do.

---

## 4 — The trust ledger runs both ways

Officers keep books on you. Their belief-in-leader channel (Addendum B's belief, scoped to the commander) is written by your record as they witnessed it: the orders that worked, the wing you fed into a marsh, the ransom you paid or didn't, whether your station choices match what their culture expects of a commander (Addendum J's price list, now audited by your own staff). Low trust doesn't flip a disloyalty bit — it *changes interpretation*. The officer who trusts you resolves your ambiguous order generously, toward your intent; the one who doesn't resolves it safely, toward his own survival, or slow-walks it, or "fails to receive" it, all of which the dispatch system can represent as latency and interpretation rather than as a mutiny mechanic. Mutiny exists, but it is the far end of a continuum the player feels long before, as an army that has become *viscous*.

And you keep books on them — but the design law holds: **there is no character sheet, there is a file.** You learn that Aldric is rash the way his contemporaries would: from the chronicle, from the death certificates of the men his initiative spent, from the proposals he sends and the ones he acts on before sending. The UI surfaces the record, beautifully — the service file as a document in the era's hand — and the *judgment* stays where it belongs, in the player. Reading your officers is gameplay. Misreading them is the game's favorite tragedy.

---

## 5 — Four chains, one schema

**Rome, mid-Republic.** Deep institutional chain: consul → legates/tribunes (aristocrats, often green, rotating) → the centurionate (sixty professional repertoire-keepers per legion) → optiones behind the ranks as institutional file-closers. Articulation is maximal: passage of lines, the wheeling cohort, the army that maneuvers in parts, all keyed to roles the state pays for. Succession is the system's superpower — the chain heals. Initiative norm: act within drill, report after (the spontaneous re-formed charge). The aristocratic top layer is the brittleness: your tribunes hold office by class, not competence, and the commission deals them to you.

**The feudal host, eleventh–fifteenth century.** Shallow political chain: the crown's authority edges reach a dozen magnates and stop; each magnate's contingent hangs off him by personal-feudal and household bonds, with real institutional depth only inside retinues (banneret, serjeants). The *plan itself* is therefore negotiated, not ordered — the **war council** is a mechanic, not a cutscene: a pre-battle scene in the matrix-ledger register where the magnates argue the array and your plan needs sponsors, because tomorrow each "wing" is a peer who agreed, or didn't quite. Mid-battle command is requests, banners, and prayer; succession is brittle (the contingent whose lord falls is an appraisal crisis); and the levies beneath it all have nearly no officer layer, which the Hastings runs already price — the fyrd chased the feint because no role existed whose job was stopping them.

**The Zulu impi, 1879.** Kinship-institutional hybrid: amabutho raised as age-sets — the bond graph is literal, men who grew up together — under izinduna who are both appointed officers and senior age-mates, beneath commanders who direct from high ground by runner and signal, per a doctrine (the horns) every man has known since boyhood. The chain is shallow but the *shared plan is deep*: low order traffic because the repertoire itself encodes the battle, which is why it worked at the pace Isandlwana demonstrated and why our scripted-horn approximation in the toy should eventually be replaced by exactly this — izinduna nodes pacing the horns against what they can see.

**Sengoku Japan.** The middle case, and a gift to the dispatch system: daimyō → kashindan retainer commanders (personal-feudal edges, but disciplined by a century of war) → ashigaru-taishō, a genuinely professionalizing officer layer over commoner infantry — plus the institution our message model was built for: the **tsukai-ban**, elite mounted messenger corps wearing identifying sashibono, an actual office of carrying orders credibly through chaos. Authority edges here are feudal in law and increasingly institutional in practice, which the schema represents as edge type *changing over a campaign's receipts* — the long war professionalized the chain, and a culture file can let the player's career ride that transition.

(The 1879 British column completes the spectrum back where the project began: purchased-then-reformed commissions, written orders, a staff system, senior NCOs as the institutional memory — and at Isandlwana, a chain that functioned right up until its assumptions about ammunition logistics did not.)

---

## 6 — What the player touches

The commission deals you a staff along with an army (Addendum J), and the strings now have faces: the patron's nephew holding a wing-command his record doesn't justify; the political officer whose authority edge runs *past* you to the capital. Pre-battle, the war council scene (in consensus cultures) or the orders group (in institutional ones) is where the plan is socialized — same engine event, different cultural skin. During battle, your station (Addendum J) sets the rhythm: at the Hill, command is mostly *triage of proposals* arriving by rider; at the Knot, it's the same with shorter latency and a lottery; at the Front Rank, your officers are commanding the army, because someone has to and it is not you. Afterward, the files update — theirs and yours about them, and theirs about you — and the winter interlude is where the chain is rebuilt, promoted, married off, buried, or poached by your rivals.

---

## 7 — Risks

Legibility is the big one: a typed authority graph can rot into homework. The mitigations are the file UI (officers as documents, not spreadsheets), the proposal rhythm (the chain mostly manifests as *people talking to you*, which humans parse natively), and ruthless caps on visible depth — the player deals with their span of control, and the layers below surface only when they break. Officer-AI cost is bounded by design: proposals come from Front-tier lookahead already budgeted in Addendum F, throttled by rank and initiative norms. The political-officer string risks pure frustration; the answer is to make him *useful sometimes* (his channel to the capital cuts both ways) so the relationship is a texture, not a tax. And the war council must not become a skippable lore screen — its output (which magnate sponsored what) has to bind mid-battle compliance hard enough that players replan the council the way they replan deployments.

**Verdict:** the chain of command is the third pillar alongside the lattice and the campaign — authority as typed edges, capability as roles, judgment as appraisal — with culture expressed entirely in the typing, the role lists, the initiative norms, and the succession rules. **Punchlist:** officer node + typed-edge schema into the culture files; role-keyed repertoire gating in the resolver (and a re-run of the Isandlwana square with a relief *role* rather than a relief flag); the interpretation pass on the dispatch system (orders resolved against recipient belief DBs); the proposal generator on Front-tier lookahead; succession rules per edge type; the war-council scene spec; service-file UI; trust-as-interpretation tuning.
