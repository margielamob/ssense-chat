# SSENSE Return Policy - IR Schema

This schema outlines the structure of information contained within the SSENSE return policy document.

## 1. Entity: Return Policy
   - **Attributes:**
     - `policy_name`: SSENSE Return Policy
     - `strict_no_paper_policy`: True
     - `right_to_reject_non_compliant`: True (Company reserves the right)
     - `frequent_return_monitoring`: True (Policy abuse may lead to action)

## 2. Entity: Return Request
   - **Attributes:**
     - `request_window_days`: 30 (Calendar days from delivery date)
     - `initiation_method`:
       - Account Holders: Via 'Order History' in SSENSE account
       - Guest Orders: Create account with order email, use online self-service tool, or contact Customer Care
       - General: Contact Customer Care
     - `authorization_required`: True (Return Authorization - RA)
     - `authorization_type`:
       - Prepaid Return Label (PPL)
       - Return Authorization (RA) Number
     - `proof_of_postage_required`: True (Customer must keep receipt)
     - `multiple_orders_per_return`: False (Must be requested and shipped separately)
     - `status`: (Implicit: Requested, Authorized, Shipped, Received, Quality Check, Approved, Rejected, Refund Processing, Refunded)

## 3. Entity: Item Eligibility
   - **Attributes:**
     - `required_condition`: "Original" (Cannot be used, altered, washed, marked, or damaged)
     - `required_packaging`: "Original Intact" (Includes shoe box, dust bag(s), brand tag(s), authenticity card; cannot be altered, damaged, or removed)
     - `required_tags`:
       - `ssense_security_tag`: Must not be altered, damaged, or removed (if applicable)
       - `brand_tags`: Must be included (part of original packaging)
     - `category_specific_rules`:
       - `intimate_apparel_swimwear`: Cannot be worn, must have original hygienic protection sticker intact.
       - `self_care (face, body, hair, make-up)`: Must be in original packaging, unused, unaltered, sealed.
       - `sexual_wellness (non-toy)`: Must be in original packaging, unused, unaltered, sealed.
       - `technology`: Must include original manuals, accessories, manufacturer packaging; must be returned sealed if received sealed.

## 4. Entity: Exclusions (Items/Fees Not Eligible for Return/Refund)
   - **Attributes:**
     - `item_types`:
       - Final Sale items (explicitly marked)
       - Face masks / face coverings (Hygiene reasons)
       - Sexual wellness toys (Health and safety reasons)
       - Dangerous goods (Candles, fragrances, oils, pressurized canned products, electronics containing batteries)
     - `fees`: Shipping fees
     - `condition`: Items not meeting `Item Eligibility` criteria.

## 5. Entity: Refund
   - **Attributes:**
     - `issuance_condition`: Returned merchandise passes quality check and is approved.
     - `refund_method`: Original method of payment
     - `processing_time_company`: Up to 5 business days (after approval)
     - `processing_time_financial_institution`: Varies (additional time)
     - `notification_method`: Confirmation email
     - `deductions`: Return Transportation Fee (applicable regions/methods)
     - `denial_outcome`: Payment withheld, merchandise kept by SSENSE (if quality check fails)

## 6. Entity: Shipping (Return)
   - **Attributes:**
     - `cost_responsibility_by_region`:
       - `Canada, United States, Japan`: Free (PPL provided)
       - `Australia, China, Hong Kong, South Korea, United Kingdom`: Customer pays via deduction (Return Transportation Fee); PPL provided.
       - `Other International`: Customer pays and coordinates shipping.
     - `label_provision`:
       - `Canada, US, Japan, Australia, China, Hong Kong, SK, UK`: PPL provided via email.
       - `Other International`: RA number provided; customer arranges shipping.
     - `return_transportation_fee`: (Applicable per package for specific regions)
       - `Australia`: 60 AUD
       - `China`: 50 USD
       - `Hong Kong`: 375 HKD
       - `South Korea`: 60 USD
       - `United Kingdom`: 34 GBP
     - `international_shipping_instructions`:
       - Use local postal service
       - Use standard shipping
       - Recommended: Insure package, use tracking number

## 7. Entity: Exchanges
   - **Attributes:**
     - `direct_exchange_offered`: False
     - `recommended_process`: Return original item for refund, place a new order for the desired item.

## 8. Entity: Damaged / Defective Goods
   - **Attributes:**
     - `customer_action`: Contact Customer Care

## 9. Entity: Warranty
   - **Attributes:**
     - `provider`: Manufacturer (if applicable)
     - `ssense_provided`: No (Subject only to manufacturer warranties)
     - `ssense_liability`: Disclaimed (where permitted by law)
     - `customer_action`: Consult user manual or contact manufacturer

## 10. Entity: Company Rights & Actions
    - **Attributes:**
      - `reject_non_compliant_returns`: True
      - `send_rejected_items_back`: True (To original shipping address, no refund)
      - `monitor_return_frequency`: True
      - `address_policy_abuse`: True (May block account, cancel future orders)

## 11. Entity: Customer Care
    - **Attributes:**
      - `contact_methods`: Email, Phone, Chat
      - `email`: customercare@ssense.com
      - `phone_details`:
        - `North America Toll Free`: 1-877-637-6002 (Mon-Fri 9 AM-8 PM EST, Sat 9 AM-5 PM EST)
        - `Local`: 1-514-600-5818 (Mon-Fri 9 AM-8 PM EST, Sat 9 AM-5 PM EST)
        - `Quebec`: 1-514-700-2078 (Mon-Fri 9 AM-8 PM EST, Sat 9 AM-5 PM EST)
      - `chat_availability`: 24/7

## 12. Entity: Guest Orders
    - **Attributes:**
      - `return_process`:
        - Option 1: Create an account using the same email address used for the order.
        - Option 2: Use the online self-service tool.
        - Option 3: Contact Customer Care.
