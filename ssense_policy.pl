% SSENSE Return Policy - Prolog Knowledge Base

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
instance(req, return_request). % Represents a generic return request instance
has_attribute(req, request_window_duration, 30).
has_attribute(req, request_window_unit, calendar_days).
has_attribute(req, request_window_start, delivery_date).

% Initiation Methods
initiation_method(req, account_holder, via_order_history).
initiation_method(req, guest, create_account_same_email).
initiation_method(req, guest, use_self_service_tool).
initiation_method(req, guest, contact_customer_care).
initiation_method(req, general, contact_customer_care).

has_attribute(req, authorization_required, true).
authorization_type(req, ppl). % Prepaid Return Label
authorization_type(req, ra_number). % Return Authorization Number

has_attribute(req, proof_of_postage_required, true).
constraint(req, multiple_orders_per_return, false). % Must be separate

% Implicit Statuses (can be represented as states)
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
instance(crit, eligibility_criteria). % Represents the set of criteria
requires(crit, item_condition, original).
condition_definition(original, not_used).
condition_definition(original, not_altered).
condition_definition(original, not_washed).
condition_definition(original, not_marked).
condition_definition(original, not_damaged).

requires(crit, item_packaging, original_intact).
packaging_definition(original_intact, includes_all_original_components). % e.g., box, dust bags, tags, cards
packaging_definition(original_intact, not_altered).
packaging_definition(original_intact, not_damaged).
packaging_definition(original_intact, not_removed).

requires(crit, ssense_security_tag_condition, intact). % if applicable
tag_condition(intact, not_altered).
tag_condition(intact, not_damaged).
tag_condition(intact, not_removed).

requires(crit, brand_tags_included, true). % Part of original packaging

% Category Specific Rules
applies_rule(crit, intimate_apparel, rule_hygienic_sticker_intact).
applies_rule(crit, swimwear, rule_hygienic_sticker_intact).
rule_definition(rule_hygienic_sticker_intact, requires_attribute(hygienic_sticker, intact)).
rule_definition(rule_hygienic_sticker_intact, requires_state(item, not_worn)).

applies_rule(crit, self_care, rule_sealed_original_packaging).
applies_rule(crit, sexual_wellness_non_toy, rule_sealed_original_packaging).
applies_rule(crit, technology_if_sealed, rule_sealed_original_packaging).
rule_definition(rule_sealed_original_packaging, requires_attribute(packaging, original)).
rule_definition(rule_sealed_original_packaging, requires_state(item, unused)).
rule_definition(rule_sealed_original_packaging, requires_state(item, unaltered)).
rule_definition(rule_sealed_original_packaging, requires_state(item, sealed)).

applies_rule(crit, technology, rule_include_manuals_accessories).
rule_definition(rule_include_manuals_accessories, requires_included(manuals)).
rule_definition(rule_include_manuals_accessories, requires_included(accessories)).
rule_definition(rule_include_manuals_accessories, requires_included(manufacturer_packaging)).

% --- Entity: Exclusions ---
instance(excl, exclusion_rule). % Represents the set of exclusions
excluded_item_type(excl, final_sale_item).
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
possible_deduction(ref, return_transportation_fee). % If applicable by region/method
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
label_provided(ship, region(other_international), ra_number_via_email). % Customer arranges shipping

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
has_attribute(warr, provider, manufacturer). % If applicable
has_attribute(warr, provided_by_ssense, false).
has_attribute(warr, ssense_liability, disclaimed). % Where permitted
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
contact_method(cc, phone, details(see_below)). % Details represented by specific facts below
contact_method(cc, chat, availability('24/7')).

phone_details(cc, north_america_toll_free, '1-877-637-6002', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).
phone_details(cc, local, '1-514-600-5818', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).
phone_details(cc, quebec, '1-514-700-2078', hours('Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST')).

% --- Entity: Guest Orders ---
instance(guest_pol, guest_order_policy). % Renamed instance atom slightly to avoid conflict with guest atom in initiation_method
return_option(guest_pol, create_account_with_order_email).
return_option(guest_pol, use_online_self_service_tool).
return_option(guest_pol, contact_customer_care).

