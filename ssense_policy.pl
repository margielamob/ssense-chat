% Optimized SSENSE Return Policy - Prolog Knowledge Base (Revised Logic v4 - Fixed + LLM Helpers)

% --- Directives ---
:- discontiguous(instance/2).
:- discontiguous(has_attribute/3).
:- discontiguous(initiation_method/3).
:- discontiguous(authorization_type/2).
:- discontiguous(possible_status/2).
:- discontiguous(constraint/3).
:- discontiguous(requires/3).
:- discontiguous(condition_definition/2).
:- discontiguous(packaging_definition/2).
:- discontiguous(tag_condition/2).
:- discontiguous(applies_rule/3).
:- discontiguous(rule_definition/2).
:- discontiguous(excluded_item_type/3).
:- discontiguous(excluded_fee/2).
:- discontiguous(excluded_condition/2).
:- discontiguous(condition_for/3).
:- discontiguous(possible_deduction/2).
:- discontiguous(denial_outcome/2).
:- discontiguous(shipping_cost/3).
:- discontiguous(label_provided/3).
:- discontiguous(return_fee/3).
:- discontiguous(instruction/3).
:- discontiguous(recommendation/3).
:- discontiguous(required_action/3).
:- discontiguous(has_right/2).
:- discontiguous(action_on_rejection/2).
:- discontiguous(action/2).
:- discontiguous(action_on_abuse/2).
:- discontiguous(contact_method/3).
:- discontiguous(phone_details/4).
:- discontiguous(return_option/2).
:- discontiguous(is_eligible/5). % Added for is_eligible itself
:- discontiguous(check_category_specific_rules/4). % Added for the helper

% Directives for new LLM Helper Predicates
:- discontiguous(get_return_window/1).
:- discontiguous(get_shipping_cost/2).
:- discontiguous(get_return_label_info/2).
:- discontiguous(get_return_fee/3).
:- discontiguous(is_item_excluded/2).
:- discontiguous(get_initiation_method/2).
:- discontiguous(can_exchange/1).
:- discontiguous(get_contact_email/1).
:- discontiguous(get_contact_chat_availability/1).
:- discontiguous(get_phone_number/3).
:- discontiguous(get_damaged_item_action/1).
:- discontiguous(get_warranty_provider/1).
:- discontiguous(is_warranty_by_ssense/1).


% --- Basic Definitions ---
entity(return_policy).
entity(return_request).
entity(item).
entity(eligibility_criteria).
entity(exclusion_rule).
entity(refund).
entity(return_shipping).
entity(exchange_policy).
entity(damaged_defective_policy).
entity(warranty_policy).
entity(company_rights).
entity(customer_care).
entity(guest_order_policy).

% --- Entity: Return Policy ---
instance(p1, return_policy).
has_attribute(p1, policy_name, 'SSENSE Return Policy').
has_attribute(p1, strict_no_paper_policy, true).
has_attribute(p1, right_to_reject_non_compliant, true).
has_attribute(p1, frequent_return_monitoring, true).

% --- Entity: Return Request ---
instance(req, return_request).
has_attribute(req, request_window_duration, 30).
has_attribute(req, request_window_unit, calendar_days).
has_attribute(req, request_window_start, delivery_date).

% Initiation Methods
initiation_method(req, account_holder, via_order_history).
initiation_method(req, guest, create_account_same_email).
initiation_method(req, guest, use_self_service_tool).
initiation_method(req, guest, contact_customer_care).
initiation_method(req, general, contact_customer_care). % Note: general might be useful if user type unknown

has_attribute(req, authorization_required, true).
authorization_type(req, ppl).
authorization_type(req, ra_number).

has_attribute(req, proof_of_postage_required, true).
constraint(req, multiple_orders_per_return, false).

% Implicit Statuses
possible_status(req, requested).
possible_status(req, authorized).
possible_status(req, shipped).
possible_status(req, received).
possible_status(req, quality_check_pending).
possible_status(req, approved).
possible_status(req, rejected).
possible_status(req, refund_processing).
possible_status(req, refunded).

% --- Entity: Item Eligibility ---
instance(crit, eligibility_criteria).
requires(crit, item_condition, original).
condition_definition(original, not_used).
condition_definition(original, not_altered).
condition_definition(original, not_washed).
condition_definition(original, not_marked).
condition_definition(original, not_damaged).

requires(crit, item_packaging, original_intact).
packaging_definition(original_intact, includes_all_original_components).
packaging_definition(original_intact, not_altered).
packaging_definition(original_intact, not_damaged).
packaging_definition(original_intact, not_removed).

requires(crit, ssense_security_tag_condition, intact).
tag_condition(intact, not_altered).
tag_condition(intact, not_damaged).
tag_condition(intact, not_removed).

requires(crit, brand_tags_included, true).

% Category Specific Rules Definitions
applies_rule(crit, intimate_apparel, rule_hygienic_sticker_intact).
applies_rule(crit, swimwear, rule_hygienic_sticker_intact).
rule_definition(rule_hygienic_sticker_intact, requires_attribute(hygienic_sticker, intact)).
rule_definition(rule_hygienic_sticker_intact, requires_state(item, not_worn)).

applies_rule(crit, self_care, rule_sealed_original_packaging).
applies_rule(crit, sexual_wellness_non_toy, rule_sealed_original_packaging).
applies_rule(crit, technology_if_sealed, rule_sealed_original_packaging). % Assuming applies to 'technology'
rule_definition(rule_sealed_original_packaging, requires_state(item, sealed)). % Key state

applies_rule(crit, technology, rule_include_manuals_accessories).
rule_definition(rule_include_manuals_accessories, requires_included(manuals)).
rule_definition(rule_include_manuals_accessories, requires_included(accessories)).
rule_definition(rule_include_manuals_accessories, requires_included(manufacturer_packaging)).


% --- Entity: Exclusions ---
instance(excl, exclusion_rule).
excluded_item_type(excl, final_sale_item, reason(marked_final_sale)).
excluded_item_type(excl, face_mask, reason(hygiene)).
excluded_item_type(excl, face_covering, reason(hygiene)).
excluded_item_type(excl, sexual_wellness_toy, reason(health_and_safety)).
excluded_item_type(excl, dangerous_good, includes([candle, fragrance, oil, pressurized_can, electronics_with_battery])).

excluded_fee(excl, shipping_fees).
excluded_condition(excl, not_meeting_eligibility_criteria).

% --- Entity: Refund ---
instance(ref, refund).
condition_for(ref, issuance, passes_quality_check).
condition_for(ref, issuance, approved).
has_attribute(ref, refund_method, original_payment_method).
has_attribute(ref, processing_time_company_max_days, 5).
has_attribute(ref, processing_time_financial_institution, varies).
has_attribute(ref, notification_method, email).
possible_deduction(ref, return_transportation_fee).
denial_outcome(ref, payment_withheld).
denial_outcome(ref, merchandise_kept_by_company).

% --- Entity: Shipping (Return) ---
instance(ship, return_shipping).

% Cost Responsibility by Region
shipping_cost(ship, region(canada), free).
shipping_cost(ship, region(usa), free).
shipping_cost(ship, region(japan), free).
shipping_cost(ship, region(australia), fee_deducted).
shipping_cost(ship, region(china), fee_deducted).
shipping_cost(ship, region(hong_kong), fee_deducted).
shipping_cost(ship, region(south_korea), fee_deducted).
shipping_cost(ship, region(uk), fee_deducted).
shipping_cost(ship, region(other_international), customer_pays).

% Label Provision by Region
label_provided(ship, region(canada), ppl_via_email).
label_provided(ship, region(usa), ppl_via_email).
label_provided(ship, region(japan), ppl_via_email).
label_provided(ship, region(australia), ppl_via_email).
label_provided(ship, region(china), ppl_via_email).
label_provided(ship, region(hong_kong), ppl_via_email).
label_provided(ship, region(south_korea), ppl_via_email).
label_provided(ship, region(uk), ppl_via_email).
label_provided(ship, region(other_international), ra_number_via_email).

% Return Transportation Fees
return_fee(ship, region(australia), amount(60, aud)).
return_fee(ship, region(china), amount(50, usd)).
return_fee(ship, region(hong_kong), amount(375, hkd)).
return_fee(ship, region(south_korea), amount(60, usd)).
return_fee(ship, region(uk), amount(34, gbp)).

% International Shipping Instructions (Customer Arranged)
instruction(ship, region(other_international), use_local_postal_service).
instruction(ship, region(other_international), use_standard_shipping).
recommendation(ship, region(other_international), insure_package).
recommendation(ship, region(other_international), use_tracking_number).

% --- Entity: Exchanges ---
instance(exch, exchange_policy).
has_attribute(exch, direct_exchange_offered, false).
has_attribute(exch, recommended_process, sequence([return_for_refund, place_new_order])).

% --- Entity: Damaged / Defective Goods ---
instance(dmg, damaged_defective_policy).
required_action(dmg, customer, contact_customer_care).

% --- Entity: Warranty ---
instance(warr, warranty_policy).
has_attribute(warr, provider, manufacturer).
has_attribute(warr, provided_by_ssense, false).
has_attribute(warr, ssense_liability, disclaimed).
required_action(warr, customer, consult_manual).
required_action(warr, customer, contact_manufacturer).

% --- Entity: Company Rights & Actions ---
instance(rights, company_rights).
has_right(rights, reject_non_compliant_returns).
action_on_rejection(rights, send_rejected_item_back_to_customer).
action_on_rejection(rights, process_no_refund).
action(rights, monitor_return_frequency).
action_on_abuse(rights, block_account).
action_on_abuse(rights, cancel_future_orders).

% --- Entity: Customer Care ---
instance(cc, customer_care).
contact_method(cc, email, 'customercare@ssense.com').
contact_method(cc, phone, details(see_below)). % Keep original for context if needed
contact_method(cc, chat, availability('24/7')).

phone_details(cc, north_america_toll_free, '1-877-637-6002', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).
phone_details(cc, local, '1-514-600-5818', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).
phone_details(cc, quebec, '1-514-700-2078', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).

% --- Entity: Guest Orders ---
instance(guest_pol, guest_order_policy).
return_option(guest_pol, create_account_with_order_email).
return_option(guest_pol, use_online_self_service_tool).
return_option(guest_pol, contact_customer_care).


% --- Core Eligibility Logic (Internal - Keep as is) ---

% is_eligible/5 checks the main criteria for return eligibility.
% LLM should target this directly when *all* details are potentially available.
is_eligible(ItemType, Condition, Packaging, Tags, DaysSinceDelivery) :-
    get_return_window(MaxDays), % Use helper internally for consistency
    DaysSinceDelivery =< MaxDays,
    \+ is_item_excluded(ItemType, _), % Use helper internally
    requires(crit, item_condition, RequiredCondition),
    Condition == RequiredCondition, % e.g., Condition = original
    requires(crit, item_packaging, RequiredPackaging), % e.g., RequiredPackaging = original_intact
    ( Packaging == sealed -> % Handle 'sealed' as a valid override if applicable
        member(ItemType, [self_care, sexual_wellness_non_toy, technology_if_sealed])
      ;
        Packaging == RequiredPackaging % Check against general requirement otherwise
    ),
    requires(crit, ssense_security_tag_condition, RequiredTagState), % e.g., RequiredTagState = intact
    ( Tags == RequiredTagState ; Tags == hygienic_sticker_intact ), % Allow general intact OR specific sticker state
    !, % Cut optimization
    check_category_specific_rules(ItemType, Condition, Packaging, Tags). % Check category specifics

% check_category_specific_rules/4 remains an internal helper for is_eligible/5
% ... (rest of check_category_specific_rules clauses remain unchanged) ...
% Special case for self_care items with sealed packaging
check_category_specific_rules(self_care, _Condition, sealed, _Tags) :- !.
% Special case for sexual_wellness_non_toy items with sealed packaging
check_category_specific_rules(sexual_wellness_non_toy, _Condition, sealed, _Tags) :- !.
% Special case for technology_if_sealed items with sealed packaging
check_category_specific_rules(technology_if_sealed, _Condition, sealed, _Tags) :- !.
% Special case for swimwear with hygienic sticker
check_category_specific_rules(swimwear, _Condition, _Packaging, hygienic_sticker_intact) :- !.
% Special case for intimate_apparel with hygienic sticker
check_category_specific_rules(intimate_apparel, _Condition, _Packaging, hygienic_sticker_intact) :- !.
% General case: Check for items with sealed packaging rule
check_category_specific_rules(ItemType, _Condition, Packaging, _Tags) :-
    applies_rule(crit, ItemType, rule_sealed_original_packaging), !, Packaging == sealed.
% General case: Check for hygiene sticker rule
check_category_specific_rules(ItemType, _Condition, _Packaging, Tags) :-
    applies_rule(crit, ItemType, rule_hygienic_sticker_intact), !, Tags == hygienic_sticker_intact.
% Technology items require manuals and accessories
check_category_specific_rules(technology, _Condition, _Packaging, _Tags) :-
    applies_rule(crit, technology, rule_include_manuals_accessories), !, true. % Placeholder - assumes checked elsewhere
% Default case: No specific rule applies
check_category_specific_rules(ItemType, _Condition, _Packaging, _Tags) :-
    \+ applies_rule(crit, ItemType, _).

% --- LLM Helper Predicates ---
% These predicates provide a simplified interface for the LLM.

% What is the return window duration?
get_return_window(Days) :-
    instance(req, return_request),
    has_attribute(req, request_window_duration, Days).

% What is the return shipping cost for a region?
% Region atoms: canada, usa, japan, australia, china, hong_kong, south_korea, uk, other_international
% CostType atoms: free, fee_deducted, customer_pays
get_shipping_cost(Region, CostType) :-
    shipping_cost(ship, region(Region), CostType).

% How is the return label provided for a region?
% LabelInfo atoms: ppl_via_email, ra_number_via_email
get_return_label_info(Region, LabelInfo) :-
    label_provided(ship, region(Region), LabelInfo).

% What is the return fee for a region (if applicable)?
% Succeeds only if a specific fee amount is defined for the region.
get_return_fee(Region, Amount, Currency) :-
    return_fee(ship, region(Region), amount(Amount, Currency)).

% Is a specific item type excluded from returns?
% ItemType atoms: final_sale_item, face_mask, face_covering, sexual_wellness_toy, dangerous_good
% MODIFIED: Returns the full reason/exclusion structure found in the KB
is_item_excluded(ItemType, ReasonStructure) :-
    % We assume 'excl' is the constant instance name for exclusion rules based on KB structure
    excluded_item_type(excl, ItemType, ReasonStructure).

% How can a user initiate a return?
% UserType atoms: account_holder, guest, general
% Method atoms: via_order_history, create_account_same_email, use_self_service_tool, contact_customer_care
get_initiation_method(UserType, Method) :-
    instance(req, return_request),
    initiation_method(req, UserType, Method).

% Can items be directly exchanged?
% Result atoms: true, false
can_exchange(Result) :-
    instance(exch, exchange_policy),
    has_attribute(exch, direct_exchange_offered, Result).

% What is the customer care email?
get_contact_email(Email) :-
    instance(cc, customer_care),
    contact_method(cc, email, Email).

% What is the availability of chat support?
get_contact_chat_availability(Availability) :-
    instance(cc, customer_care),
    contact_method(cc, chat, availability(Availability)). % Assuming format is availability(...)

% Get specific phone number details.
% PhoneType atoms: north_america_toll_free, local, quebec
get_phone_number(PhoneType, Number, Hours) :-
    instance(cc, customer_care),
    phone_details(cc, PhoneType, Number, hours(Hours)). % Assuming format is hours(...)

% What should a customer do if an item is damaged/defective?
% Action atoms: contact_customer_care
get_damaged_item_action(Action) :-
    instance(dmg, damaged_defective_policy),
    required_action(dmg, customer, Action).

% Who provides the warranty?
% Provider atoms: manufacturer
get_warranty_provider(Provider) :-
    instance(warr, warranty_policy),
    has_attribute(warr, provider, Provider).

% Does SSENSE provide the warranty?
% Result atoms: true, false
is_warranty_by_ssense(Result) :-
    instance(warr, warranty_policy),
    has_attribute(warr, provided_by_ssense, Result).

% --- Wrapper Predicates for LLM Compatibility (Arity-Extended) ---

% is_eligible/6
is_eligible(ItemType, Condition, Packaging, Tags, Days, true) :-
    is_eligible(ItemType, Condition, Packaging, Tags, Days), !.
is_eligible(_, _, _, _, _, false).

% get_return_window/2
get_return_window(Days, true) :-
    get_return_window(Days), !.
get_return_window(_, false).

% get_shipping_cost/3
get_shipping_cost(Region, Cost, true) :-
    get_shipping_cost(Region, Cost), !.
get_shipping_cost(_, _, false).

% get_return_fee/4
get_return_fee(Region, Amount, Currency, true) :-
    get_return_fee(Region, Amount, Currency), !.
get_return_fee(_, _, _, false).

% is_item_excluded/3
is_item_excluded(ItemType, Reason, true) :-
    is_item_excluded(ItemType, Reason), !.
is_item_excluded(_, _, false).

is_within_return_window(Days, true) :- Days =< 30.
is_within_return_window(Days, false) :- Days > 30.

is_within_return_window(Days) :-
    get_return_window(Max), Days =< Max.

% ========================
% --- Decision Reasoning ---
% ========================

% Entry point: symbolic reasoning over user-provided facts
% Facts: list of structured input (e.g., item_type(...), days_since_delivery(...))
% Decision: one of return_allowed | return_denied(reason(...)) | unknown

decide(Facts, Decision) :-
    reason_about_return(Facts, Decision), !.
decide(_, unknown("Unable to determine based on provided facts.")).

% --- Reasoning rules ---

% 1. Item type is excluded
reason_about_return(Facts, return_denied(reason(excluded_item_type, ItemType))) :-
    member(item_type(ItemType), Facts),
    is_item_excluded(ItemType, _), !.

% 2. Return window exceeded
reason_about_return(Facts, return_denied(reason(outside_return_window, Days))) :-
    member(days_since_delivery(Days), Facts),
    \+ is_within_return_window(Days), !.

% 3. Item not in original condition
reason_about_return(Facts, return_denied(reason(not_original_condition))) :-
    member(item_condition(Condition), Facts),
    requires(crit, item_condition, Required),
    Condition \= Required, !.

% 4. Packaging not intact
reason_about_return(Facts, return_denied(reason(packaging_not_intact))) :-
    member(item_packaging(Packaging), Facts),
    requires(crit, item_packaging, Required),
    Packaging \= Required, !.

% 5. Tag removed or damaged
reason_about_return(Facts, return_denied(reason(tag_removed))) :-
    member(tag_condition(Tag), Facts),
    requires(crit, ssense_security_tag_condition, Required),
    Tag \= Required, !.

% 6. Passes all checks
reason_about_return(Facts, return_allowed) :-
    member(item_type(ItemType), Facts),
    member(item_condition(Condition), Facts),
    member(item_packaging(Packaging), Facts),
    member(tag_condition(Tags), Facts),
    member(days_since_delivery(Days), Facts),
    is_eligible(ItemType, Condition, Packaging, Tags, Days), !.

% --- Optional explanation mappings for NLG ---
decision_message(return_allowed, "You're eligible to return this item.").

decision_message(return_denied(reason(excluded_item_type, T)), Msg) :-
    format(atom(Msg), "Items of type ~w are excluded from returns.", [T]).

decision_message(return_denied(reason(outside_return_window, D)), Msg) :-
    format(atom(Msg), "It's been ~w days since delivery, which exceeds the return window.", [D]).

decision_message(return_denied(reason(not_original_condition)), "The item is not in its original condition and cannot be returned.").

decision_message(return_denied(reason(packaging_not_intact)), "The original packaging must be intact to qualify for a return.").

decision_message(return_denied(reason(tag_removed)), "The SSENSE security tag must be intact to process a return.").

decision_message(unknown(Reason), Msg) :-
    format(atom(Msg), "We couldn't make a decision: ~w", [Reason]).

% --- Decision Rule Interface ---
% Takes a list of facts and deduces Result = true or false.
decide(Facts, Result) :-
    include(ground_fact, Facts, Grounded),        % Ensure all terms are grounded
    maplist(assertz_if_new, Grounded),            % Assert temporary facts
    (
        extract_decision_params(ItemType, Condition, Packaging, Tags, Days),
        is_eligible(ItemType, Condition, Packaging, Tags, Days)
        -> Result = true
        ;  Result = false
    ),
    retract_all(Grounded).                        % Clean up temporary facts

% Helper to ensure only facts (not meta terms) are passed
ground_fact(Fact) :- ground(Fact).

% Helper to avoid duplicate fact assertion
assertz_if_new(Fact) :-
    \+ call(Fact), assertz(Fact), !.
assertz_if_new(_). % already exists

% Extracts known facts into variables for is_eligible/5
extract_decision_params(ItemType, Condition, Packaging, Tags, Days) :-
    item_type(ItemType),
    item_condition(Condition),
    item_packaging(Packaging),
    tag_condition(Tags),
    days_since_delivery(Days).

% Cleanup
retract_all([]).
retract_all([H|T]) :- retractall(H), retract_all(T).


% --- End of Knowledge Base ---