# ULTRAGOAL — Revenue Intelligence OS
### A Gong Replacement Built on Hermes Agent + HydraDB
> Paste this file into LazyCodex as your Ultragoal. Run `$ulw-plan` first, then `$start-work`.

---

## 0. What We Are Building and Why

Gong is a $7.5B analytics company that watches your sales team and tells you what the best reps do differently. It is a passive observer. It generates dashboards and insights that someone still has to read, interpret, and act on. The gap between the insight and the action never closes automatically. That gap is the entire product opportunity.

This product is the active version of Gong. It does not show you what good reps do — it makes every rep perform like a good rep, automatically, before, during, and after every call. The agent does the work. The rep closes the deal.

The two things that make this possible that did not exist when Gong was built:

**Hermes Agent** — an open-source self-improving agent that creates executable skills from observed patterns. When a rep closes a deal, the agent captures what worked as a reusable skill. The next rep in the same situation gets that skill applied automatically. The team gets smarter with every deal.

**HydraDB** — a serverless context graph that stores team memory as a shared temporal knowledge graph. Every call, every email, every deal outcome, every rep's institutional knowledge lives in one graph that every other rep and agent can query. When a rep leaves, the knowledge stays. The graph compounds over time.

Gong is analytics without agency. This is agency without dashboards.

---

## 1. The Core Problem Gong Does Not Solve

Gong tells a sales manager what their best reps do. The manager then has to:
- Manually coach every other rep
- Remember to share relevant call clips
- Trust that reps will actually change behavior
- Update CRM themselves after calls
- Find prospect context scattered across tools before every call
- Notice deal risk before it is too late

None of this is automated. Every step requires a human to decide, act, and follow through. Gong is a dashboarding layer on top of a broken process. The process is still broken.

This product eliminates every manual step in that chain.

---

## 2. Stack Decisions — Non-Negotiable

**Agent Runtime: Hermes Agent (cloned fresh for this project)**
- Hermes provides the skill compounding loop — the core differentiator
- Every observed winning pattern gets stored as an executable SKILL.md
- The agent runs 24/7 as a persistent background process
- Delivery via Slack, WhatsApp, and email is native to Hermes

**Memory and Context Layer: HydraDB**
- All team call data, deal history, prospect context, and rep patterns live in HydraDB
- HydraDB separates Memories (dynamic, per-session state) from Knowledge (versioned documents)
- The temporal graph means we can answer "what changed about this prospect since Q1" — Gong cannot
- Multi-tenant isolation means rep A's personal patterns stay private but shared intel is org-wide
- No infrastructure management — serverless, scales automatically

**What we build on top of Hermes + HydraDB:**
- Call ingestion and transcription pipeline
- CRM connectors (Salesforce, HubSpot)
- Custom coaching UI (lightweight web dashboard — not the primary surface, push is)
- Deal scoring logic
- Calendar integration for pre-call triggers

---

## 3. The Architecture in Plain Language

The product has four layers:

**Layer 1 — Ingestion**
Every signal that matters gets pulled in: call recordings (Zoom, Meet, Teams), emails, CRM activity, calendar events, Slack messages, and deal stage changes. This layer normalizes everything into a consistent format and feeds it into HydraDB.

**Layer 2 — Memory (HydraDB)**
HydraDB holds two types of data. Memories are dynamic — they represent the current state of a deal, a prospect, a rep's recent performance, and open action items from calls. Knowledge is static — it represents things that are versioned and replaced rather than updated, like a prospect's company profile, a competitor's product positioning, or a proven closing playbook. Both live in one temporal graph. Relationships between entities (rep, deal, prospect, company, competitor, outcome) are extracted automatically.

**Layer 3 — Agent Intelligence (Hermes)**
Hermes runs continuously in the background. It watches for triggers (calendar event 10 minutes away, call just ended, deal stage change, rep inactivity on a hot deal) and fires the appropriate skill. Skills are created from winning patterns automatically. The agent improves every week without any manual configuration.

**Layer 4 — Delivery**
The agent pushes to wherever reps already are — Slack, WhatsApp, or email. There is a lightweight web dashboard for managers but it is not the primary surface. Value is delivered proactively. Nobody opens a dashboard to find a problem. The agent tells them.

---

## 4. Feature Specifications

### 4.1 Call Ingestion and Transcription

**What Gong does:** Records calls on Zoom/Meet/Teams, transcribes them, generates a summary, identifies topics and speakers.

**What we do and why it is better:**

We do all of that plus we extract structured entities into HydraDB at ingestion time — not just a transcript, but a typed graph of who said what, what objections were raised, what commitments were made, what competitors were mentioned, and what the next step is. Gong stores transcripts. We store a queryable knowledge graph.

Crucially, every ingested call is linked to the existing HydraDB node for that prospect company and that deal. So when a rep queries "what has this prospect said about pricing across every call in the last 6 months" they get a synthesized answer, not a list of clips to scrub through.

The transcription pipeline must support Zoom, Google Meet, and Microsoft Teams. Audio is transcribed using a fast model. Speaker diarization identifies which voice is the rep and which is the prospect. The transcript is chunked, embedded, and ingested into HydraDB as both a Memory node (the specific call) and an update to the Knowledge node for that prospect.

Post-ingestion, the Hermes call-analysis skill runs automatically and populates the deal node with: sentiment trend, objections raised, commitments made (by both sides), next step agreed, risk signals, and competitor mentions.

### 4.2 Pre-Call Brief

**What Gong does:** Nothing proactively. Reps have to manually search for past calls. Most do not.

**What we do:**

Ten minutes before every call (triggered by calendar integration), Hermes fires the pre-call-brief skill. It queries HydraDB for everything relevant to this prospect and deal: all past call summaries, open commitments from the last call, prospect company news from the last 30 days, what competitors the prospect has mentioned, what objections they raised previously, and what the rep promised to follow up on. HydraDB synthesizes this into a single brief — not a list of links, a prose answer with citations.

The brief is pushed to the rep via Slack DM or WhatsApp message within 60 seconds of the trigger. The rep walks into the call knowing everything the team knows about this prospect. Every time. Automatically.

This is zero effort for the rep. It just shows up.

### 4.3 Post-Call Automation

**What Gong does:** Surfaces a call summary. Rep still has to update CRM, write the follow-up email, add notes, and move the deal stage manually.

**What we do:**

Within 5 minutes of a call ending (detected via calendar event completion or audio silence), Hermes fires the post-call skill chain in sequence:

First, the transcript is ingested and HydraDB is updated with the new call memory. Deal node, prospect node, and rep activity node are all updated.

Second, the CRM is updated automatically — deal stage, next step date, and call notes are written directly to Salesforce or HubSpot using the commitments extracted from the call. No rep input required.

Third, a follow-up email draft is written based on what was discussed, what was promised, and what the next step is. The draft uses patterns from successful follow-ups in HydraDB — it looks like what your best reps write, not a generic template. The draft is pushed to the rep for one-click send or light editing.

Fourth, if risk signals were detected (pricing objection unresolved, competitor mentioned for the first time, prospect went cold mid-call, next step was vague), the manager is notified with a specific flagged note — not a dashboard to check.

The entire post-call process takes less than 5 minutes and requires zero rep input.

### 4.4 Deal Health Scoring

**What Gong does:** Shows a deal score based on engagement metrics — emails sent, calls made, time since last touch. A lagging indicator. It tells you a deal is dying after it is already dying.

**What we do:**

Deal health in our system is a temporal graph query, not a metric. We score deals on five signals: momentum (rate of engagement change, not just engagement), sentiment trajectory (is prospect sentiment improving or declining across calls), commitment symmetry (are both sides honoring their stated next steps), competitive exposure (how often competitor is mentioned and how the prospect frames it), and relationship depth (is the rep talking to one person or has the conversation expanded to multiple stakeholders).

Because HydraDB tracks all of this as a temporal graph, we can answer "this deal's health has declined 30% in the last 3 weeks and the inflection point was the pricing call on May 14th." Gong gives you a number. We give you a cause.

Deals below a threshold score automatically trigger a Hermes coaching skill that runs the rep through what the data says is going wrong and what winning reps did in similar situations.

### 4.5 Skill Compounding from Win Patterns

**This is the feature that has no Gong equivalent.**

When a deal is marked Won in CRM, Hermes triggers the win-pattern-extraction skill. It queries HydraDB for the full history of that deal — every call, every email, every rep action, every prospect response. It identifies the pattern of actions that preceded the close: what the rep said on the discovery call, how they handled the pricing objection, what the follow-up cadence looked like, what the final push was.

That pattern is written as a SKILL.md file — a reusable, executable skill that Hermes can apply in future deals that match the same profile (industry, company size, deal size, competitor landscape, objection pattern).

When a rep is in a deal that matches the pattern, Hermes loads that skill and coaches them through it in real time. The win pattern from your best rep becomes the default behavior for every rep.

When a deal is marked Lost, the same process runs in reverse — what did the losing pattern look like, and what should reps do differently when they see it forming. Lost deal patterns get written as a risk-detection skill.

Over 6 months, the skill library compounds. The team does not get smarter because a manager coaches them. It gets smarter because the agent learns from every outcome.

### 4.6 Rep Coaching Without Dashboards

**What Gong does:** Shows coaching dashboards to managers. Managers have to find time to coach. Most do not coach consistently.

**What we do:**

Coaching in this product happens at the moment of relevance, not in a weekly one-on-one. After every call, if the call analysis detects a gap (rep talked more than 60% of the time, pricing raised too early, next step was vague, competitor not handled), Hermes sends the rep a specific note — not a score, a specific observation with a suggested approach based on what works. It arrives within 5 minutes of the call ending, while the rep still remembers the conversation.

Managers get a weekly digest (pushed to Slack, not a dashboard they open) showing which reps are improving, which deals are at risk, and what skills the team has built from recent wins. One message. Actionable. No login required.

For reps who consistently underperform on a specific signal, Hermes schedules a skills training sequence — a series of prompts and scenarios over the following week, pushed to Slack, based on the specific gap. It adapts based on how the rep responds.

### 4.7 Pipeline and Forecast Intelligence

**What Gong does:** Shows pipeline analytics. Managers can see deal velocity, stage conversion rates, and revenue at risk. Still requires human interpretation.

**What we do:**

Every week, Hermes runs a pipeline sweep — it queries HydraDB for all open deals, scores each one, and generates a forecast with explicit reasoning. Not "Q3 is 87% likely to close at $2.1M" — but "Q3 closes at $2.1M if the three deals flagged at risk receive intervention this week. The risk in each is: Deal A has no scheduled next step, Deal B has a competitor now involved, Deal C has not had a response in 14 days."

The forecast is pushed as a Slack message to the sales manager every Monday morning. It includes a prioritized action list — which deals to touch this week and exactly why. The manager does not analyze. They act.

For each at-risk deal, Hermes generates a specific recommended action: who to contact, what to say, and what winning reps did in similar situations. The action is linked to a one-click draft if an email or message is the recommended move.

### 4.8 Competitor Intelligence

**What Gong does:** Tracks competitor mentions in calls, shows you a competitor card with talking points. Static. The card does not update based on what you learn from calls.

**What we do:**

Every competitor mention in a call is extracted into HydraDB as a structured entity — what the prospect said, how they framed it, what the rep said in response, and what the outcome of that exchange was (did the prospect move forward, raise it again next call, or drop it). Over time, HydraDB builds a living competitive intelligence graph.

When a rep is facing a competitor objection, Hermes queries the graph and surfaces: the three responses that have historically resolved this specific objection with this type of prospect, the competitor claims your reps have successfully countered, and the claims that have not worked. The coaching is drawn from your own team's real experience, not a static battlecard.

When a new competitor pattern emerges across multiple deals in the same week, Hermes alerts the sales leader automatically — not in a report they pull, in a Slack message that says "Competitor X is being mentioned in 4 active deals this week, all at the pricing stage. Here is what reps are saying and what is working."

### 4.9 CRM Sync and Data Quality

**What Gong does:** Reads from CRM. Does not write back reliably. CRM data quality stays bad.

**What we do:**

The post-call skill writes structured data back to CRM after every call. Deal stage, contact activity, next step date, notes, and open action items are all kept current automatically. No rep has to touch CRM between calls.

Additionally, HydraDB detects when CRM data and call reality diverge — if a deal is marked "Negotiation" in CRM but the last 3 calls have had a prospect raising basic objections that belong in "Discovery," the system flags the mismatch. Data quality improves as a side effect of the agent doing its job.

### 4.10 Onboarding New Reps

**What Gong does:** Has a library of curated call clips. Someone has to manually tag and curate them. Most libraries go stale within 2 months.

**What we do:**

New reps are onboarded through the HydraDB knowledge graph, not a clip library. On day one, the rep queries the system with questions like "how do we handle pricing objections in enterprise deals" or "what do the best reps say in the first discovery call." They get synthesized answers from the team's actual win history, with citations to the specific deals and calls the answer is drawn from.

Hermes generates a first-30-days skill pack for new reps based on the most common situations they will face in the first month — derived from deal history, not someone's opinion. The skill pack is pushed to them progressively, one skill per day, as Slack messages.

Because the knowledge graph accumulates, this gets better with every new hire. The knowledge left behind by reps who leave does not walk out the door.

---

## 5. Hermes Skills Map

These are the skills Hermes needs to run this product. Each becomes a SKILL.md file in the Hermes skills directory. LazyCodex should implement each skill in sequence.

**call-analysis** — Triggered after call ingestion. Extracts entities, commitments, objections, competitors mentioned, sentiment, and next step. Writes structured output to HydraDB.

**pre-call-brief** — Triggered 10 minutes before a calendar event with a prospect. Queries HydraDB, synthesizes a brief, delivers via Slack or WhatsApp.

**post-call-chain** — Triggered on call completion. Orchestrates: transcript ingestion → CRM update → follow-up draft → risk detection → manager alert if needed.

**deal-health-scorer** — Triggered daily for all active deals. Computes health score from HydraDB temporal graph. Flags declining deals and fires coaching skill for those below threshold.

**win-pattern-extractor** — Triggered on deal Won event from CRM. Extracts the winning sequence from HydraDB deal history and writes a new SKILL.md for the pattern.

**loss-pattern-extractor** — Triggered on deal Lost event from CRM. Extracts the losing pattern and writes a risk-detection SKILL.md.

**rep-coaching-nudge** — Triggered post-call when gaps are detected. Sends a specific, timed coaching note to the rep via Slack. Not a score, a specific observation and suggestion.

**pipeline-sweep** — Triggered every Monday at 8am. Queries all open deals, generates forecast with reasoning, delivers action-priority list to manager via Slack.

**competitor-signal-detector** — Triggered when competitor mentions spike across deals in a time window. Alerts sales leader with specific context and what is working in responses.

**onboarding-skill-pack** — Triggered when a new rep is added to the system. Queries deal history, generates a 30-day progressive skill pack, delivers one skill per day.

**crm-data-quality-watch** — Triggered daily. Detects divergence between CRM stage and actual call content. Flags mismatches to manager.

---

## 6. HydraDB Memory Architecture

HydraDB distinguishes between Memories (dynamic, session-level) and Knowledge (versioned, document-level). This distinction drives how we store everything.

**Stored as Memories (dynamic, evolves every session):**
- Current deal state (stage, health score, last activity, open commitments)
- Rep activity log (what they did, when, what outcome)
- Prospect sentiment trajectory (how their tone has changed across calls)
- Current open action items (what each side owes the other)
- Recent competitor mentions (per deal)

**Stored as Knowledge (versioned, replaced not updated):**
- Company profiles for each prospect (what they do, who the decision makers are, buying history)
- Competitor profiles (capabilities, weaknesses, common objections raised)
- Winning playbooks (the SKILL.md content extracted from won deals)
- Rep performance baselines (30/60/90-day rolling averages per signal)
- Product information (features, pricing tiers, common objections and responses)

**Key graph relationships HydraDB must capture:**
- Rep → owns → Deal
- Deal → has stage → Stage (with timestamp, so we can track velocity)
- Deal → involves → Prospect Company
- Call → is part of → Deal
- Call → mentions → Competitor
- Call → contains → Commitment (with owner and due date)
- Won Deal → produced → Skill (linking outcome to the playbook it generated)
- Lost Deal → produced → Risk Pattern

**Temporal queries we must be able to answer:**
- "What has this prospect said about pricing across every call this quarter?"
- "Which deals have had no rep activity in the last 7 days?"
- "What changed in this deal between last week and this week?"
- "Which competitor is appearing more frequently this