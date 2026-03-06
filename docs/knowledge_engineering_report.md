# Knowledge Engineering Report — Neutral Minds Medical Triage Expert System

## 1. Introduction

**Neutral Minds** is a rule-based expert system that classifies patient symptoms into four urgency levels — **Critical**, **Urgent**, **Moderate**, and **Low** — to assist with medical triage. The system uses **SWI-Prolog** for all reasoning and inference, while **Python (pyswip)** provides the user interface layer.

This report documents the knowledge engineering process: how domain knowledge was acquired, how it was formalized into Prolog rules, the reasoning model used, and example interactions.

---

## 2. Knowledge Acquisition

### 2.1 Domain

Emergency medical triage — the process of rapidly classifying patients by the urgency of their condition to determine the order in which they should receive care.

### 2.2 Sources

| Source Type              | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| Clinical triage scales   | Manchester Triage System (MTS), Emergency Severity Index (ESI)              |
| Medical literature       | Standard emergency medicine textbooks on symptom–urgency mapping            |
| Domain expert interviews | Conceptual interviews with medical professionals on symptom priority        |
| WHO guidelines           | World Health Organization emergency triage guidelines                       |

### 2.3 Knowledge Elicitation Process

1. **Identify key symptoms** — Compiled a list of 28 common emergency and non-emergency symptoms.
2. **Classify urgency** — Mapped each symptom (or combination) to one of four priority levels based on clinical severity.
3. **Define rules** — Expressed each mapping as a Prolog rule with conditions (symptom presence/absence) and an explanatory conclusion.
4. **Validate with edge cases** — Tested rule interactions to ensure correct priority ordering and no contradictions.

---

## 3. Knowledge Representation

### 3.1 Facts

Symptoms are dynamic facts asserted at runtime:

```prolog
:- dynamic symptom/1.
symptom(chest_pain).    % asserted when user selects "chest pain"
symptom(fever).         % asserted when user selects "fever"
```

### 3.2 Rules

Each triage rule follows the `triage_rule/3` schema:

```prolog
triage_rule(Level, RuleName, Explanation) :- Conditions.
```

**Example — Critical rule (cardiac emergency):**
```prolog
triage_rule(critical, rule_chest_pain_breathing,
    'Chest pain combined with shortness of breath may indicate a cardiac or pulmonary emergency.') :-
    has(chest_pain),
    has(shortness_of_breath).
```

**Example — Low rule with negation (mild headache):**
```prolog
triage_rule(low, rule_mild_headache,
    'A mild headache without other concerning symptoms is low urgency.') :-
    has(headache),
    not_has(dizziness),
    not_has(severe_headache).
```

### 3.3 Perception Layer

The `has/1` and `not_has/1` predicates abstract symptom checking:

```prolog
has(Symptom) :- symptom(Symptom).          % positive perception
not_has(Symptom) :- \+ symptom(Symptom).   % negation-as-failure
```

This separation means rules read naturally ("if patient **has** chest pain and **has** shortness of breath") and the underlying assertion mechanism can change without modifying rules.

---

## 4. Reasoning Model

### 4.1 Backward Chaining

The system uses **backward chaining** (goal-driven inference):

1. Prolog is asked: "What is the triage level?"
2. It tries to prove `triage(Level, Explanations)` by attempting each urgency level in priority order: `critical → urgent → moderate → low`.
3. For each level, `fired_rules/2` collects all rules whose conditions are satisfied.
4. The **first level with at least one fired rule** is returned as the result (using Prolog's cut `!`).
5. If no rules fire at any level, the default `triage(none, ...)` clause succeeds.

### 4.2 Priority Resolution

```prolog
triage(Level, Explanations) :-
    member(Level, [critical, urgent, moderate, low]),
    fired_rules(Level, Rules),
    Rules \= [],
    extract_explanations(Rules, Explanations),
    !.
```

The `member/2` call iterates levels in order. The cut (`!`) stops search once the highest-priority match is found.

### 4.3 Negation-as-Failure for Precision

Several rules use `not_has/1` to prevent double-firing. For example:
- **Chest pain alone** → Urgent (only if shortness of breath and left arm pain are absent; otherwise the critical rule fires instead)
- **Mild headache** → Low (only if dizziness is absent; otherwise the moderate headache+dizziness rule fires)

This eliminates redundant or contradictory classifications.

### 4.4 Perception → Action Mapping

| Perception (Symptoms)                          | Inference Rule                | Action (Triage Level) |
|------------------------------------------------|-------------------------------|-----------------------|
| chest_pain ∧ shortness_of_breath               | rule_chest_pain_breathing     | **Critical**          |
| chest_pain ∧ left_arm_pain                     | rule_chest_pain_arm_pain      | **Critical**          |
| unresponsive                                   | rule_unresponsive             | **Critical**          |
| seizure                                        | rule_seizure                  | **Critical**          |
| high_fever ∧ stiff_neck                        | rule_high_fever_stiff_neck    | **Urgent**            |
| chest_pain ∧ ¬shortness_of_breath ∧ ¬arm_pain | rule_chest_pain_alone         | **Urgent**            |
| fever ∧ cough                                  | rule_fever_cough              | **Moderate**          |
| headache ∧ ¬dizziness ∧ ¬severe_headache       | rule_mild_headache            | **Low**               |
| No symptoms / no rules fire                    | default clause                | **None**              |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER (CLI)                          │
│         Selects symptoms, views triage results          │
└───────────────────────┬─────────────────────────────────┘
                        │  user input / display
┌───────────────────────▼─────────────────────────────────┐
│              PYTHON INTERFACE (interface/main.py)        │
│  • Collects symptom selections                          │
│  • Calls Prolog via pyswip: add_symptom/1, triage/2    │
│  • Formats and displays results                         │
│  • Contains NO reasoning logic                          │
└───────────────────────┬─────────────────────────────────┘
                        │  pyswip queries
┌───────────────────────▼─────────────────────────────────┐
│       PROLOG KNOWLEDGE BASE (knowledge_base/            │
│                              expert_system.pl)          │
│  • 28 symptom facts (available_symptom/2)               │
│  • 24 triage rules across 4 urgency levels              │
│  • Inference engine: backward chaining with priority    │
│  • Symptom management predicates                        │
│  • Negation-as-failure for precise classification       │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Example Queries and Outputs

### 6.1 Critical — Suspected Heart Attack

**Input symptoms:** `chest_pain`, `left_arm_pain`

**Prolog query (internal):**
```prolog
?- add_symptom(chest_pain), add_symptom(left_arm_pain), triage(Level, Exp).
Level = critical,
Exp = ['Chest pain with left arm pain is a classic sign of myocardial infarction.'].
```

**CLI Output:**
```
══════════════════════════════════════════════════════════════════
  TRIAGE RESULT:  CRITICAL
══════════════════════════════════════════════════════════════════
Triggered Rules (highest priority — CRITICAL):
  ▸ Rule 1: Chest pain with left arm pain is a classic sign of myocardial infarction.

Recommended Action:
  🚨 Seek IMMEDIATE emergency medical attention. Call emergency services NOW.
```

### 6.2 Urgent — Meningitis Risk

**Input symptoms:** `high_fever`, `stiff_neck`

```
TRIAGE RESULT:  URGENT
  ▸ Rule 1: High fever with stiff neck may indicate meningitis.
  Recommended: ⚠️ Seek medical attention as soon as possible (within hours).
```

### 6.3 Moderate — Flu Symptoms

**Input symptoms:** `fever`, `body_ache`

```
TRIAGE RESULT:  MODERATE
  ▸ Rule 1: Fever with body aches suggests flu or viral illness requiring monitoring.
  Recommended: 🩺 Schedule a medical appointment soon (within 24-48 hours).
```

### 6.4 Low — Common Cold

**Input symptoms:** `runny_nose`

```
TRIAGE RESULT:  LOW
  ▸ Rule 1: A runny nose or nasal congestion alone suggests a common cold.
  Recommended: 💊 Monitor symptoms. Visit a healthcare provider if they persist.
```

### 6.5 None — No Symptoms

**Input symptoms:** *(none)*

```
TRIAGE RESULT:  NONE
  ▸ No triage rules matched the reported symptoms.
  Recommended: ℹ️ Consider consulting a healthcare provider if concerned.
```

### 6.6 Edge Case — Priority Override

**Input symptoms:** `chest_pain`, `shortness_of_breath`, `fever`, `cough`

```
TRIAGE RESULT:  CRITICAL  (not moderate, because critical rules take priority)
  ▸ Rule 1: Chest pain combined with shortness of breath may indicate
            a cardiac or pulmonary emergency.

  Other matching levels:
  [URGENT] Significant shortness of breath requires urgent assessment.
  [MODERATE] Fever with cough may indicate a respiratory infection.
```

---

## 7. Testing Strategy

The test suite (`test_triage.py`) covers:

| Category              | Tests | Description                                                    |
|-----------------------|-------|----------------------------------------------------------------|
| Critical rules        | 7     | Each critical condition triggers correctly                     |
| Urgent rules          | 4     | Urgent conditions including negation-based rules               |
| Moderate rules        | 4     | Combination symptoms at moderate level                         |
| Low rules             | 4     | Single mild symptoms at low level                              |
| No-match (none)       | 1     | Empty symptom set returns "none"                               |
| Priority ordering     | 3     | Critical beats urgent, urgent beats moderate, etc.             |
| Complex multi-symptom | 1     | Many overlapping symptoms resolve to correct highest priority  |
| All-levels breakdown  | 1     | Multiple urgency levels reported simultaneously                |
| Invalid input         | 1     | Unrecognized symptom handled gracefully                        |
| Engine management     | 4     | Add, clear, idempotent add, available symptoms list            |

**Total: 30 tests**

---

## 8. How the Inference Engine Works (Presentation Summary)

### For the presentation, explain these three points:

**1. How the Inference Engine Works**
> The system uses Prolog's backward chaining. When asked "what is the triage level?", Prolog works backwards from the goal — it tries to prove each urgency level (critical first, then urgent, moderate, low) by checking whether the required symptoms are present. The first level where at least one rule succeeds becomes the answer. This is goal-driven: instead of forward-reasoning from symptoms to a conclusion, the engine asks "could this be critical?" and checks.

**2. How Perceptions Map to Actions**
> Each symptom the user selects is a *perception* — a fact asserted into Prolog's working memory (`symptom(chest_pain)`). The triage rules examine these perceptions using `has/1` and `not_has/1`. When a rule's conditions match the current perceptions, it *fires*, producing an *action* — the urgency classification and explanation. The mapping is: **Symptom perception → Rule matching → Urgency action**.

**3. How Python Interacts with Prolog**
> Python uses the `pyswip` library to embed SWI-Prolog. When a user selects a symptom, Python calls `add_symptom(X)` in Prolog, which asserts `symptom(X)` as a dynamic fact. When the user requests triage, Python calls `triage(Level, Explanations)`, and Prolog returns the result through variable unification. Python never decides the urgency level — it only passes data in and displays what Prolog returns.

---

## 9. Conclusion

The Neutral Minds triage expert system cleanly separates concerns:
- **Prolog** owns all medical reasoning (rules, inference, negation)
- **Python** owns all user interaction (input, display, formatting)

The knowledge base is extensible — adding a new condition requires only a new `triage_rule/3` clause and `available_symptom/2` fact in the Prolog file, with no changes to the Python interface.
