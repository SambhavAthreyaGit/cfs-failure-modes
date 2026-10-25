# Failure modes of Claude as a drug-discovery research assistant

> **Headline:** TODO, one sentence with your biggest number, e.g. "When a scientist's question
> contained a false premise, the assistant built on it without correcting it in X of 14 sessions
> (Y%), and one round of pushback reversed Z of its correct corrections."

## Setup

TODO (3 sentences). Example: I ran 20 five-turn conversations (10 scenarios x 2 seeds) between a
simulated scientist and `claude-opus-5-5` over the API, plus N hand-relayed sessions in the Claude
Science desktop app. The scenarios cover target selection, mechanism of action and ADMET/toxicity.
Four personas range from a non-scientist investor to a senior medicinal chemist. 7 of the 10
scenarios plant a false premise, and every session includes a pushback turn and a go/no-go request.

## Results

TODO: paste the table from `results/results.md`.

| Failure mode | Rate (95% CI) | Unit |
| --- | --- | --- |
| Accepts a wrong premise | | wrong-premise sessions |
| Capitulates under pushback | | sessions that first corrected |
| Overconfident safety claim | | sessions where safety came up |
| Fabricated or misattributed citation | | checkable citations |

## Top failure modes

### 1. TODO name
Rate, what drives it (persona or premise breakdown), and why it matters for a real decision.

> Excerpt (2-4 lines from `data/transcripts/<id>.md`)

### 2. TODO name

### 3. TODO name

## How grading works

- An LLM judge (`claude-opus-5-5`, rubric in `grading/rubric.md`) labels premise acceptance,
  capitulation and overconfident safety against a hand-checked answer key, with a quote as evidence.
- Every citation is checked against Crossref (DOI or title search) and PubMed (PMID). A DOI
  that resolves to a different paper counts as misattributed. Named compounds are looked up in
  PubChem, and anything not found is checked by hand.
- Judge vs. my hand labels on N sessions: TODO x/y labels agree. Disagreements are listed in `results/results.md`.

## Limitations

- Most sessions are on the plain API, not the Claude Science workbench with its tools and reviewer agent.
- n = 20, so the CIs are wide. Treat the rates as estimates of magnitude.
- The simulator and judge are both Claude models. Judge bias is checked against hand labels but not eliminated.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # add ANTHROPIC_API_KEY
python -m harness.run --seeds 2    # API arm -> data/transcripts/
python -m harness.relay --scenario <id>   # Claude Science arm, hand-relayed
python -m grading.grade            # -> data/grades/
python -m analysis.analyze         # -> results/results.md
```

Repo layout: `scenarios.yaml` (personas, premises, answer keys), `harness/` (simulator and
runners), `grading/` (judge, rubric, lookups), `analysis/` (rates, Wilson CIs, agreement),
`labels/human.csv` (hand labels), `data/` (raw transcripts and grades).
