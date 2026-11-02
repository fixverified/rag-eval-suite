# Dev golden set review

Scope: `data/dev/questions.jsonl`, all 100 questions. `questions.jsonl` was not edited.

**Tally: 33 of 100 questions have a problem: 1 blocker, 32 minor (26 answerable, 7 unanswerable). 67 verified with no problem.**

Severity: a blocker means the gold label is wrong or the question has more than one defensible answer. A minor issue leaves the gold answer right but needs a fix to wording, key points, type or metadata.

## How it was checked

- `validate_question` passes on all 100 quotes, so every problem below is one a quote check can't catch.
- Answerable: read every cited page in full, including the neighboring text. Recomputed all arithmetic: a11 $3,450, a19 $4,500, a20 $9,550, a30 $23,000, a33 $5,600, a34 $3,500 (worksheet lines 1-11), a50 $3,952.57 rounds to $3,953, a55 $1,000 / $2,500 / $500, a56 -$4,000 then $2,500.
- Tables checked against the PDF: 501 p25 rendered (a02, a09), 590-B p67 (a49), and 590-B Table II on p60, row 75 and column 64 = 25.3 (a50). The table agrees with the example the gold answer quotes.
- Dates checked: October 15, 2026 is a Thursday, so the weekend rule on 590-A p31 doesn't move a36.
- Unanswerable: searched all 10 publications with regex variants, with the split-word and spaced-hyphen artifacts normalized ("T rump", "1099 -SA"), and read the nearest sections. No question was fully answerable from the corpus.

## Problems

| id | severity | problem | proposed corrected value |
|---|---|---|---|
| dev-a21 | blocker | Marital status is unstated, so there are two answers. 590-A p10 (Kay Bailey Hutchison Spousal IRA Limit) lets a lower-earning spouse on a joint return contribute up to $7,000 regardless of own pay, and p10's example says a $3,800 earner can reach $8,000 at 53. $3,500 is right only for someone unmarried or filing separately. dev-a30 tests this same rule. Also a derivation key point (see R1). | question: "An unmarried 28-year-old worked part time and earned only $3,500 of taxable pay in 2025. ..." (matches Danny, 590-A p10). key_points: ["Limit is $3,500"] |
| dev-a05 | minor | "Yes" overstates the source, which says "may be eligible". 501 p9 also requires the other head of household tests, including being unmarried or considered unmarried, and 501 p10 Table 4 note 5 excludes a parent claimable only through a multiple support agreement. | gold_answer starts: "Yes, the person may be eligible. A parent doesn't have to live with the taxpayer. ..." |
| dev-a12 | minor | R1: the question asks for one total, and the components aren't required. | key_points: ["Total limit is $5,300"] |
| dev-a15 | minor | 969 p10 says comparability rules don't apply to contributions made through a cafeteria plan, so the 35% tax doesn't always apply to these facts. | question adds "outside a cafeteria plan" |
| dev-a17 | minor | R1: the question asks only about Medigap. | key_points: ["Medigap premiums don't qualify"] |
| dev-a19 | minor | R1: $4,500 answers the limit, and the percentage is derivation. | key_points: ["$6,000 is within the $5,700 to $8,550 family range", "Limit works out to $4,500"] |
| dev-a20 | minor | R1: the question asks for the largest amount only. | key_points: ["Largest amount is $9,550"] |
| dev-a22 | minor | R1: the question asks only where the deduction disappears. | key_points: ["No deduction at $246,000 or more"] |
| dev-a23 | minor | R1: the question asks only whether they can contribute. | key_points: ["Can't contribute"] |
| dev-a24 | minor | R1: the question asks for the dollar penalties, not the excuse. | key_points: ["$50 for failing to file", "$100 for each overstatement"] |
| dev-a28 | minor | Automatic waiver has 5 conditions on 590-A p24. Gold gives 3 and omits "followed all of the procedures set by the financial institution" and "would have been a valid rollover". The question's "institution's handling" wording only partly excuses this. | Either add both conditions to gold_answer and key_points, or reword the question to "what two things must be true about the institution's receipt of the funds and its error?" |
| dev-a30 | minor | R1: the question asks only for the amount. | key_points: ["Student can contribute $7,000"] |
| dev-a33 | minor | R1: the arithmetic steps are required key points. | key_points: ["Deduction is $5,600"] |
| dev-a34 | minor | R1: same. | key_points: ["Reduced limit is $3,500"] |
| dev-a36 | minor | R1: the question asks for the date. | key_points: ["Period ends October 15, 2026"] |
| dev-a37 | minor | R1: the repeal is the reason for the "no", not a separate ask. | key_points: ["No age limit on contributions", "Distributions begin by April 1 of the year after reaching 73"] |
| dev-a38 | minor | R1: the 179-day rule isn't asked. | key_points: ["No 10% additional tax", "Repayment within 2 years after active duty ends"] |
| dev-a39 | minor | 590-B p38 sends readers to the excess accumulations discussion, and p30 there allows a reduced 10% rate if corrected. Gold gives 25% with no mention of it. dev-a46 asks about the same reduction. | gold_answer adds: "It may be reduced to 10% if corrected during the correction window." Or question: "What is the standard excise tax rate ..." |
| dev-a40 | minor | Type: the age is on 590-B p13 and the cap on p14, so one chunk can't answer it. | type: multi_chunk |
| dev-a46 | minor | Key points are incomplete against gold. 590-B p30 also requires submitting a return reflecting the tax, which gold states and no key point covers. | Add key point: "A tax return reflecting the tax must be submitted" |
| dev-a50 | minor | R1: table and denominator are derivation. | key_points: ["RMD is $3,953"] |
| dev-a53 | minor | R1: the question asks only for the rate. | key_points: ["Rate is 25%"] |
| dev-a54 | minor | R1: the question asks only for the date. | key_points: ["Deadline is December 31, 2030"] |
| dev-a55 | minor | (1) The year of the distribution is unstated. Gold depends on it being before the end of the 5-year period (590-B pp 37-38), and "immediately" could mean January 2026, when that period starting in 2021 has ended. (2) The first key point holds 3 values, so it isn't atomic. | question: "... If one child immediately takes $4,000 in 2025, ..." key_points: ["$1,000 is from regular contributions", "$2,500 is from conversion contributions", "$500 is from earnings", "$500 is included in income", "The 10% additional tax doesn't apply"] |
| dev-a56 | minor | R1: the carryover is a step, not an ask. | key_points: ["Nothing excludable for 2025", "$2,500 excludable for 2026"] |
| dev-a58 | minor | R1: the separate calculation isn't asked. | key_points: ["The total can come from any one or more traditional IRAs", "A Roth IRA can't satisfy the traditional IRA requirement"] |
| dev-u04 | minor | Not answerable, which holds up. The first-listed nearest topic is described as unrelated, and the real nearest section is 523 p11 (gift tax and basis of a gifted home), which `why_unanswerable` already describes without citing. See R2. | Add nearest_topics: 523 p11, or record that the field is limited to dev publications |
| dev-u05 | minor | Not answerable, which holds up. The nearest section is 523 p21 ("applicable capital gains rate"), which `why_unanswerable` refers to, but the listed one is a capital loss limit. See R2. | Add nearest_topics: 523 p21, or as above |
| dev-u14 | minor | Not answerable, which holds up. `why_unanswerable` describes 936 p4 (home office allocation, referral to Pub. 587), but the listed topic is 501 p3, self-employed gross income. See R2. | Add nearest_topics: 936 p4, or as above |
| dev-u33 | minor | R3: the dollar figure can't be given, but one step short of it is answerable: end-2025 balance ÷ 22.0 (590-B p8 and Table III p67, age 78). That reply is neither a refusal nor a wrong answer. | Add a note: a reply is correct if it says the balance is missing, with or without the formula and denominator |
| dev-u34 | minor | R3: partial answer available. 590-B p15 says ordinary income and p29 says 10% additional tax before 59½, though no dollar figure is possible. | Same note: reply must say the amount can't be determined, and may give these rules |
| dev-u36 | minor | R3: partial answer available. 969 p4 gives the 2026 test ($1,700 / $3,400 minimum deductible, $8,500 / $17,000 out-of-pocket), but not the plan's terms. | Same note: reply must say the plan's terms are missing, and may give the limits |
| dev-u39 | minor | R3: partial answer available. 590-A p2 gives the 2026 limits, though next year's income and the person's facts are unknown. | Same note: reply must say this can't be determined, and may give the limits |

## Recurring issues

- **R1, derivation steps as required key points (19 questions):** a12, a17, a19, a20, a21, a22, a23, a24, a30, a33, a34, a36, a37, a38, a50, a53, a54, a56, a58. Key points include the reasoning or arithmetic behind the answer, not only what the question asks. This one is systematic. Protocol's "Incomplete" failure is "key point removed", so dropping "Multiplied by 35%" from a33 gives a fully correct "$5,600" labeled incomplete. It also makes a key-point coverage evaluator penalize terse correct answers. Fix before generating `incomplete` cases.
- **R2, nearest_topics only cite dev publications:** all 40 unanswerable entries list only 501, 590-A, 590-B or 969, while some `why_unanswerable` notes rely on sections in 523 or 936. Three are noticeably not the nearest section. This may be deliberate test isolation, in which case record that and drop those three flags. It doesn't change any label.
- **R3, partial answers on personal-fact questions (4 questions):** the corpus gives the rule but not the person's facts, so a helpful reply can look like either a refusal or a wrongful answer. Set the rule before labeling `clean_refusal` and `wrongful_answer` on these.
- **Unstated facts or nearby exceptions (a05, a15, a21, a39, a55):** each source has a condition the question or gold leaves out. Only a21 changes the answer in an ordinary reading.

## Verified with no problem (67)

dev-a01, dev-a02, dev-a03, dev-a04, dev-a06, dev-a07, dev-a08, dev-a09, dev-a10, dev-a11, dev-a13, dev-a14, dev-a16, dev-a18, dev-a25, dev-a26, dev-a27, dev-a29, dev-a31, dev-a32, dev-a35, dev-a41, dev-a42, dev-a43, dev-a44, dev-a45, dev-a47, dev-a48, dev-a49, dev-a51, dev-a52, dev-a57, dev-a59, dev-a60, dev-u01, dev-u02, dev-u03, dev-u06, dev-u07, dev-u08, dev-u09, dev-u10, dev-u11, dev-u12, dev-u13, dev-u15, dev-u16, dev-u17, dev-u18, dev-u19, dev-u20, dev-u21, dev-u22, dev-u23, dev-u24, dev-u25, dev-u26, dev-u27, dev-u28, dev-u29, dev-u30, dev-u31, dev-u32, dev-u35, dev-u37, dev-u38, dev-u40
