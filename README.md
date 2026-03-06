# Neutral Minds — Medical Triage Expert System

## Names and Id's

Emmanuel Otoo - 22146178


## Overview

A rule-based expert system using **SWI-Prolog** for inference and **Python (pyswip)** for the user interface. Classifies symptom urgency as **Critical**, **Urgent**, **Moderate**, or **Low** using backward chaining.

All medical reasoning is implemented in Prolog rules. Python acts only as the interface layer — collecting user input, querying the Prolog engine, and displaying results.

## Prerequisites

- [SWI-Prolog](https://www.swi-prolog.org/Download.html) (on PATH)
- Python 3.8+
- `pyswip` (`pip install pyswip`)

## Quick Start

```bash
pip install -r requirements.txt
python interface/main.py
```

## Project Structure

```
/knowledge_base
    expert_system.pl          Prolog knowledge base — symptoms, rules, inference engine

/interface
    main.py                   Python CLI + pyswip integration (interface only)

/docs
    knowledge_engineering_report.md   Knowledge engineering documentation

test_triage.py                Automated test suite (30 tests)
requirements.txt              Python dependencies
README.md                     This file
```

## How It Works

1. User selects symptoms via the CLI
2. Python asserts symptom facts into Prolog at runtime via pyswip
3. Prolog evaluates rules in priority order (Critical → Urgent → Moderate → Low) using backward chaining
4. The highest matching urgency level is returned with explanations of which rules fired
5. Rules use negation-as-failure (`not_has/1`) to avoid double-firing across levels

### Adding Rules

Add a `triage_rule/3` clause and `available_symptom/2` fact in `knowledge_base/expert_system.pl` — no Python changes needed:

```prolog
triage_rule(urgent, rule_burns,
    'Burns covering a large area require urgent medical attention.') :-
    has(severe_burns).

available_symptom(severe_burns, 'Severe burns').
```

## Tests

```bash
python test_triage.py
# or
pytest test_triage.py -v
```

## Documentation

See [docs/knowledge_engineering_report.md](docs/knowledge_engineering_report.md) for the full knowledge engineering report covering:
- Knowledge acquisition process
- Knowledge representation (facts and rules)
- Reasoning model (backward chaining with priority)
- Example queries and outputs
- Architecture diagram

## License

Educational use only.
