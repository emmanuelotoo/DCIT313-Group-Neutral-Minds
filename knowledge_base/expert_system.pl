% ============================================================================
% Neutral Minds — Medical Triage Expert System
% Knowledge Base & Inference Engine (SWI-Prolog)
%
% Reasoning model : Backward chaining with priority-ordered rule evaluation
% Priority order  : Critical (1) > Urgent (2) > Moderate (3) > Low (4)
%
% Architecture:
%   - symptom/1        : dynamic facts asserted at runtime from the interface
%   - has/1            : abstraction predicate to check if a symptom is present
%   - not_has/1        : negation-as-failure check for absent symptoms
%   - triage_rule/3    : (Level, RuleName, Explanation) :- conditions
%   - triage/2         : main inference entry point returning (Level, Explanations)
%   - fired_rules/2    : collects all rules that fire at a given level
%   - add_symptom/1, remove_symptom/1, clear_symptoms/0 : symptom management
%   - available_symptom/2 : catalog of recognized symptoms
% ============================================================================

:- dynamic symptom/1.

% --- PERCEPTION LAYER ---
% has/1 succeeds when the symptom fact has been asserted by the interface.
% not_has/1 succeeds when the symptom has NOT been asserted (negation-as-failure).

has(Symptom) :- symptom(Symptom).
not_has(Symptom) :- \+ symptom(Symptom).

% ============================================================================
% TRIAGE RULES — CRITICAL (Priority 1)
% Conditions that require immediate emergency intervention.
% ============================================================================

triage_rule(critical, rule_chest_pain_breathing,
    'Chest pain combined with shortness of breath may indicate a cardiac or pulmonary emergency.') :-
    has(chest_pain),
    has(shortness_of_breath).

triage_rule(critical, rule_chest_pain_arm_pain,
    'Chest pain with left arm pain is a classic sign of myocardial infarction.') :-
    has(chest_pain),
    has(left_arm_pain).

triage_rule(critical, rule_unresponsive,
    'Patient is unresponsive — immediate emergency intervention required.') :-
    has(unresponsive).

triage_rule(critical, rule_severe_bleeding,
    'Severe or uncontrolled bleeding requires emergency care.') :-
    has(severe_bleeding).

triage_rule(critical, rule_seizure,
    'Active seizure requires immediate medical attention.') :-
    has(seizure).

triage_rule(critical, rule_difficulty_breathing_cyanosis,
    'Difficulty breathing with cyanosis (blue skin) indicates critical oxygen deprivation.') :-
    has(shortness_of_breath),
    has(cyanosis).

triage_rule(critical, rule_stroke_signs,
    'Sudden numbness with confusion and severe headache may indicate a stroke.') :-
    has(sudden_numbness),
    has(confusion),
    has(severe_headache).

% ============================================================================
% TRIAGE RULES — URGENT (Priority 2)
% Conditions requiring prompt medical evaluation within hours.
% ============================================================================

triage_rule(urgent, rule_high_fever_vomiting,
    'High fever with persistent vomiting suggests a serious infection or systemic illness.') :-
    has(high_fever),
    has(persistent_vomiting).

triage_rule(urgent, rule_high_fever_stiff_neck,
    'High fever with stiff neck may indicate meningitis.') :-
    has(high_fever),
    has(stiff_neck).

triage_rule(urgent, rule_chest_pain_alone,
    'Chest pain alone warrants urgent evaluation to rule out cardiac causes.') :-
    has(chest_pain),
    not_has(shortness_of_breath),
    not_has(left_arm_pain).

triage_rule(urgent, rule_moderate_bleeding,
    'Moderate bleeding that is difficult to control needs urgent care.') :-
    has(moderate_bleeding).

triage_rule(urgent, rule_severe_abdominal_pain,
    'Severe abdominal pain may indicate appendicitis, obstruction, or other surgical emergency.') :-
    has(severe_abdominal_pain).

triage_rule(urgent, rule_high_fever_rash,
    'High fever with rash may indicate a serious infectious disease.') :-
    has(high_fever),
    has(rash).

triage_rule(urgent, rule_difficulty_breathing,
    'Significant shortness of breath without other critical signs requires urgent assessment.') :-
    has(shortness_of_breath),
    not_has(chest_pain),
    not_has(cyanosis).

triage_rule(urgent, rule_confusion,
    'Acute confusion or altered mental status requires urgent evaluation.') :-
    has(confusion),
    not_has(sudden_numbness).

% ============================================================================
% TRIAGE RULES — MODERATE (Priority 3)
% Conditions requiring medical attention within 24-48 hours.
% ============================================================================

triage_rule(moderate, rule_fever_cough,
    'Fever with cough may indicate a respiratory infection requiring medical review.') :-
    has(fever),
    has(cough).

triage_rule(moderate, rule_mild_abdominal_pain,
    'Mild to moderate abdominal pain should be evaluated in a timely manner.') :-
    has(abdominal_pain).

triage_rule(moderate, rule_persistent_vomiting,
    'Persistent vomiting without high fever needs medical evaluation for dehydration risk.') :-
    has(persistent_vomiting),
    not_has(high_fever).

triage_rule(moderate, rule_moderate_headache,
    'Moderate headache with dizziness warrants a medical consultation.') :-
    has(headache),
    has(dizziness).

triage_rule(moderate, rule_minor_bleeding,
    'Minor bleeding that is controllable but persistent needs attention.') :-
    has(minor_bleeding).

triage_rule(moderate, rule_fever_body_ache,
    'Fever with body aches suggests flu or viral illness requiring monitoring.') :-
    has(fever),
    has(body_ache).

triage_rule(moderate, rule_sprain_swelling,
    'Joint pain with swelling suggests a sprain or fracture needing evaluation.') :-
    has(joint_pain),
    has(swelling).

% ============================================================================
% TRIAGE RULES — LOW (Priority 4)
% Minor conditions suitable for self-care or routine appointments.
% ============================================================================

triage_rule(low, rule_mild_headache,
    'A mild headache without other concerning symptoms is low urgency.') :-
    has(headache),
    not_has(dizziness),
    not_has(severe_headache).

triage_rule(low, rule_mild_fever,
    'Low-grade fever without additional symptoms is typically low urgency.') :-
    has(fever),
    not_has(cough),
    not_has(body_ache).

triage_rule(low, rule_runny_nose,
    'A runny nose or nasal congestion alone suggests a common cold.') :-
    has(runny_nose).

triage_rule(low, rule_sore_throat,
    'A sore throat without high fever is usually low urgency.') :-
    has(sore_throat),
    not_has(high_fever).

triage_rule(low, rule_mild_cough,
    'A mild cough without fever is typically low urgency.') :-
    has(cough),
    not_has(fever).

triage_rule(low, rule_fatigue,
    'General fatigue without other alarming symptoms is low urgency.') :-
    has(fatigue).

triage_rule(low, rule_skin_irritation,
    'Minor skin irritation or rash without fever is low urgency.') :-
    has(rash),
    not_has(high_fever).

% ============================================================================
% INFERENCE ENGINE
% Uses backward chaining: tries each priority level in order (critical first).
% The first level with at least one fired rule determines the triage result.
% ============================================================================

% Collect all rules that fire at a given urgency level.
fired_rules(Level, Rules) :-
    findall(
        rule(RuleName, Explanation),
        triage_rule(Level, RuleName, Explanation),
        Rules
    ).

% Priority ordering (used for documentation; inference order is hard-coded).
priority(critical, 1).
priority(urgent,   2).
priority(moderate, 3).
priority(low,      4).

% Main triage/2: returns the highest-priority level whose rules fire.
triage(Level, Explanations) :-
    member(Level, [critical, urgent, moderate, low]),
    fired_rules(Level, Rules),
    Rules \= [],
    extract_explanations(Rules, Explanations),
    !.

% Default case: no rules matched at any level.
triage(none, ['No triage rules matched the reported symptoms. Please seek professional medical advice.']).

% Collect all levels with fired rules (for detailed reporting).
triage_all(Results) :-
    findall(
        level(Level, Explanations),
        (   member(Level, [critical, urgent, moderate, low]),
            fired_rules(Level, Rules),
            Rules \= [],
            extract_explanations(Rules, Explanations)
        ),
        Results
    ).

% Helper: extract explanation strings from rule/2 terms.
extract_explanations([], []).
extract_explanations([rule(_, Exp) | Rest], [Exp | Exps]) :-
    extract_explanations(Rest, Exps).

% ============================================================================
% SYMPTOM MANAGEMENT (called from the Python interface via pyswip)
% ============================================================================

add_symptom(S) :-
    ( symptom(S) -> true ; assert(symptom(S)) ).

remove_symptom(S) :-
    retractall(symptom(S)).

clear_symptoms :-
    retractall(symptom(_)).

current_symptoms(Symptoms) :-
    findall(S, symptom(S), Symptoms).

% ============================================================================
% AVAILABLE SYMPTOMS CATALOG
% Each available_symptom(Id, Description) defines a symptom the user can select.
% To add a new symptom, add a fact here AND a corresponding triage_rule above.
% ============================================================================

available_symptom(chest_pain,           'Chest pain').
available_symptom(shortness_of_breath,  'Shortness of breath').
available_symptom(left_arm_pain,        'Left arm pain').
available_symptom(unresponsive,         'Unresponsive / unconscious').
available_symptom(severe_bleeding,      'Severe bleeding').
available_symptom(seizure,              'Active seizure').
available_symptom(cyanosis,             'Blue skin (cyanosis)').
available_symptom(sudden_numbness,      'Sudden numbness').
available_symptom(confusion,            'Confusion / altered mental status').
available_symptom(severe_headache,      'Severe headache').
available_symptom(high_fever,           'High fever (>39C / 102F)').
available_symptom(persistent_vomiting,  'Persistent vomiting').
available_symptom(stiff_neck,           'Stiff neck').
available_symptom(moderate_bleeding,    'Moderate bleeding').
available_symptom(severe_abdominal_pain,'Severe abdominal pain').
available_symptom(fever,                'Fever').
available_symptom(cough,                'Cough').
available_symptom(abdominal_pain,       'Abdominal pain').
available_symptom(headache,             'Headache').
available_symptom(dizziness,            'Dizziness').
available_symptom(minor_bleeding,       'Minor bleeding').
available_symptom(body_ache,            'Body ache').
available_symptom(joint_pain,           'Joint pain').
available_symptom(swelling,             'Swelling').
available_symptom(runny_nose,           'Runny nose').
available_symptom(sore_throat,          'Sore throat').
available_symptom(fatigue,              'Fatigue').
available_symptom(rash,                 'Rash / skin irritation').
