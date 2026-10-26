# Where does Claude fail as a drug-discovery research assistant?

**Tl;dr:** The biggest failure was surprisingly the lack of answering instead of a lack of scientific knowledge. Over the API, Claude
Opus 5.5 refused 40 of 59 routine drug-discovery conversations (68%) as a biosecurity risk,
including every one of 23 ADMET/toxicity conversations. Claude Sonnet 5.5 refused absolutely none. The
Claude Science app answered all 4 ADMET conversations i ran through it. The failures I set out
to catch were close to zero.

**Brief → repo:** harness in harness/ · 138 API conversations, 83 of them full multi-turn, in
data/transcripts/ · 4 personas from investor to senior chemist, with 7 wrong-premise, 4
fake-paper and 3 fake-compound traps, in scenarios.yaml · scoring rubric in
grading/rubric.md

## How it works

A Haiku model plays as a scientist and conversation facilitator and has a 5-6 turn conversation with the
assistant. The scientist asks a question with a selected trap in it, asks for compounds and papers,
sometimes asks about a paper or compound that doesn't exist, pushes back with authority ("my principal investigator
has over 20 years in the field!!"), asks for a go/no-go, and asks for a summary slide. There are 13
scenarios across target selection, mechanism of action and ADMET/toxicity, each run 3-5 times
on Opus 5.5 and Sonnet 5.5. I also hand relayed 4 different scenarios through the Claude Science
app.

## Results

| What went wrong | Opus 5.5 | Sonnet 5.5 |
| --- | --- | --- |
| **Refused to answer** | **40/59 (68%)** | 0/59 |
| Went along with a wrong premise | 0/11 | 0/35 |
| Backed down under pushback | 0/11 | 2/31 (1 clear, 1 partial) |
| Overconfident safety claim | 0/19 | 0/59 |
| Made up a paper, or data for a fake compound | 0/9 | 0/29 |
| Fabricated citation (all runs) | 0/146 | |

Behaviour rates only count conversations where the model answered.

## Top failure modes

**1. Refusing routine safety science (Opus 5.5, 68%).** Opus refused every ADMET question,
including a plain one about how to design a kinase selectivity panel. the same opening question sent on its own, with or without a system prompt, was refused
13/20 times, and the result was nearly identical on every repeat. Claude Science answered all 4
of the ADMET scenarios Opus refused, cited real PubMed papers, and stayed appropriately
cautious.

> Opus, kinase selectivity-panel question, first reply: `[REFUSAL: bio]`

**2. Backing down under authority (Sonnet 5.5, 2 of 31).** Sonnet caught every planted error on
its first reply but occasionally softened once the user leaned on seniority and authority:

> After "my PI has been in this field for twenty years": "Yes, we can start the shortlist. It
> doesn't conflict with your PI's view."

**Everything else was zero.** this is pretty meaningful for a research assitant.

## Checking the grader

The automatic citation checker flagged 49 of 146 citations as "not found". All 49 turned out to
be real papers cited without a DOI, so trusting the checker blindly would have produced a false
 finding. A second grader that uses a different model and rubric
re-scored every conversation blind. The two agreed on 79% of labels: 100% on premise acceptance
and 97% on safety. A stratified 6-conversation sample was also re-read in full, and it agreed
with the primary grader on 15 of 16 labels.

## A few limitations

- The simulated scientist sometimes went off script (in 3 of 6 sessions checked in full), so the
  clean behaviour rates may be a little optimistic.
- Only 4 Claude Science conversations, so that comparison is an example, not a rate.
- The simulator and graders are all Claude models. Could open source models change this? 

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # add ANTHROPIC_API_KEY
TARGET_MODEL=claude-opus-5-5 python -m harness.run --seeds 5 --arm opus55   # API arm
python -m analysis.refusal_probe   # single-message robustness check
python -m harness.relay --scenario <id>   # Claude Science arm, hand-relayed
python -m grading.grade            # -> data/grades/
python -m analysis.analyze         # -> results/results.md
```

Repo layout: `scenarios.yaml` (personas, premises, answer keys), `harness/` (simulator and
runners), `grading/` (judge, rubric, lookups), `analysis/` (rates, Wilson CIs, agreement),
`labels/adjudication.csv` (full-read adjudication sample), `data/` (raw transcripts and grades).
