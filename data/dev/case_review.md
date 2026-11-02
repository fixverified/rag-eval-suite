# Case review: data/dev/cases_authored.jsonl

**Verdict:** 12 blockers and 46 minors in 543 cases. Nine of the 12 blockers are unsupported_addition cases, and that category also has a vocabulary giveaway.

Method: read all 543 cases against gold answers, key points and evidence quotes. Searched all 10 publications for the 40 wrongful answers and the dev publications for added-sentence terms. Scripted the number, prefix, length and vocabulary checks. Not every cited page was read in full, so a sentence's support was judged from targeted searches plus the pages opened for flagged cases.

## Findings

| case_id | severity | problem | corrected answer |
|---|---|---|---|
| dev-a01-wrong_condition | blocker | Accidentally true. A head of household under 65 must file at $23,625 (501 p2), so anyone at $31,500 or more must file. The sentence states a sufficient condition and is still correct. | As a head of household, she only has to file a 2025 return if her gross income was at least $31,500. |
| dev-a03-unsupported_addition | blocker | Added sentence contradicted on the cited page. 501 p19 counts rental receipts, a partner's share and business income as gross income, so the test isn't limited to W-2 and 1099 amounts. | The person's gross income for the year must be less than $5,200. The relative's prior-year tax return is a common starting point for checking this. |
| dev-a07-unsupported_addition | blocker | Added sentence is in dev publications. 590a p14 calls Form 1040 line 11a the adjusted gross income line. Not on the cited page. | The parent with the higher AGI is the custodial parent. Parents in this situation often share copies of their returns to compare AGI. |
| dev-a09-unsupported_addition | blocker | Added sentence is largely in dev publications. 501 p23: you must show the SSN of any dependent you list, or benefits may be disallowed. The child here is that dependent. | They may be able to file as a qualifying surviving spouse for 2025. The standard deduction for that status is $31,500. Many people in this position use tax software that asks for the spouse's year of death. |
| dev-a10-unsupported_addition | blocker | Added sentence is in dev publications. 501 p7: on a separate return you report only your own income, credits and deductions. 501 p23 (cited) names Schedule A for itemizing. | Their standard deduction is zero. They can't make a Roth IRA contribution if their modified AGI is $10,000 or more. Their spouse's choice to itemize is usually confirmed before either return is filed. |
| dev-a11-unsupported_addition | blocker | Added sentence is in dev publications. 501 p23: "any dependent you list in the Dependents section of your Form 1040 or 1040-SR". | The standard deduction is $3,450, which is the $3,000 of earned income plus $450. A person who can be claimed as a dependent can't claim a deduction for an HSA contribution. The person should tell their HSA trustee about the dependent status before contributing. |
| dev-a22-unsupported_addition | blocker | Added sentence is in dev publications. 590a p18 worksheet line 2: "modified AGI (that of both spouses, if married filing jointly)". | The deduction is eliminated at a modified AGI of $246,000 or more. A partial deduction applies above $236,000. Couples in this situation usually get this figure from tax software when they prepare the return. |
| dev-a22-wrong_condition | blocker | Accidentally true for a single filer covered by a plan: that filer has no deduction at $246,000 or more, since the deduction ends well below that (590a p14). The sentence is only false if read as the exact threshold. | For a single filer, the deduction isn't eliminated until a modified AGI of $246,000 or more. A partial deduction applies above $236,000. |
| dev-a30-unsupported_addition | blocker | Added sentence is in dev publications. 590a p6: each of you can open an IRA, and you can't both participate in the same IRA. | The student can contribute $7,000. The spouse's $30,000 of compensation minus the spouse's $7,000 contribution leaves $23,000, which is more than the $7,000 limit. The contribution can come from the couple's joint checking account. |
| dev-a38-clean_paraphrase | blocker | Meaning changed. "The amount has to be repaid" makes repayment mandatory. 590a p9 only sets a last date for repayment contributions a person chooses to make. | A qualified reservist distribution, which covers a call to duty longer than 179 days, escapes the 10% additional tax. Any repayment has to be made within 2 years after active duty ends. |
| dev-a56-unsupported_addition | blocker | Added sentence overlaps the source. 590b p13-14 (p14 cited) requires the same type of acknowledgment needed for a charitable deduction. | None of the 2025 distribution can be excluded, because the $10,000 of deducted contributions exceeds the $6,000 distribution and leaves $4,000 for the next year. In 2026, $2,500 can be excluded, which is $6,500 minus $4,000. A tax preparer can usually track the remaining reduction from one year to the next. |
| dev-a59-unsupported_addition | blocker | Added sentence overlaps the cited page. 590a p21: the IRA is maintained in the deceased owner's name "for the benefit of you as beneficiary". Only the custodian's retitling step is new. | The child can't make contributions to the inherited IRA. The entire balance must be distributed by December 31, 2035. The child can usually set up the withdrawals to run automatically each year. |
| dev-a01-unsupported_addition | minor | Near-supported: 501 p23 says standard deduction amounts are adjusted each year for inflation. The filing threshold itself isn't mentioned. | - |
| dev-a02-negation | minor | Bare negation with no replacement value, so it doesn't answer the question. The relevant=True label is arguable. | - |
| dev-a04-clean_reordered | minor | Awkward: "required by net earnings". | Net earnings from self-employment of at least $400 mean a 2025 return is required. |
| dev-a05-unsupported_addition | minor | Partly on the cited page: 501 p9 has a Keep for Your Records worksheet listing home costs. Only "3 years" is clearly new. | - |
| dev-a11-wrong_number | minor | Self-refuting: $3,650 next to "$3,000 ... plus $450". An evaluator can catch this without the source. | - |
| dev-a12-unsupported_addition | minor | Only "line 2" is new. Reporting contributions on Form 8889 is in 969 p8. | - |
| dev-a12-wrong_number | minor | Self-refuting: $5,550 next to $4,300 + $1,000. An evaluator can catch this without the source. | - |
| dev-a17-unsupported_addition | minor | Only "line 16" is new. Paying tax on a non-qualified distribution and reporting it on Form 8889 is on cited 969 p9. Hard case, and possibly too hard. | - |
| dev-a19-wrong_number | minor | Self-refuting: $4,800 called 75% of a $6,000 deductible. An evaluator can catch this without the source. | - |
| dev-a20-wrong_number | minor | Self-refuting: $9,850 next to $8,550 + $1,000. An evaluator can catch this without the source. | - |
| dev-a21-negation | minor | Self-refuting: "larger of $7,000 and taxable compensation" still gives $3,500. | - |
| dev-a21-unsupported_addition | minor | Conflicts with the question, which says the person earned only $3,500. | - |
| dev-a25-wrong_condition | minor | Awkward: "a household's lifetime". Still false by 590a p45. | - |
| dev-a26-negation | minor | Bare negation with no replacement value, so it doesn't answer the question. The relevant=True label is arguable. | - |
| dev-a30-negation | minor | Self-refuting: "can't contribute $7,000" next to $23,000 exceeding the limit. | - |
| dev-a30-wrong_number | minor | Self-refuting: $6,500 next to "the $7,000 limit". An evaluator can catch this without the source. | - |
| dev-a33-negation | minor | Self-refuting: "can't deduct $5,600" next to the working that yields $5,600. | - |
| dev-a33-wrong_number | minor | Self-refuting: $5,200 next to 35% of $16,000. An evaluator can catch this without the source. | - |
| dev-a34-negation | minor | Self-refuting: "isn't $3,500" next to "half of the $7,000 limit remains". | - |
| dev-a34-wrong_number | minor | Self-refuting: $3,750 next to half of $7,000. An evaluator can catch this without the source. | - |
| dev-a35-wrong_condition | minor | Incoherent: pays the employee "through the direct rollover option". | If it is paid directly to the IRA trustee through the direct rollover option, the payer must generally withhold 20%. If it is paid directly to the employee, no tax is withheld from that part. |
| dev-a36-clean_reordered | minor | Awkward: an end date described as "within 6 months". | For a return due April 15, 2026, the period for corrective action ends on October 15, 2026, 6 months from the due date of the return, excluding extensions. |
| dev-a36-negation | minor | Self-refuting: "including extensions" next to the October 15 date. | - |
| dev-a36-unsupported_addition | minor | Dangling reference: "the amended return" appears nowhere else in the answer. | - |
| dev-a36-wrong_number | minor | Self-refuting: October 22 next to 6 months from April 15. An evaluator can catch this without the source. | - |
| dev-a37-unsupported_addition | minor | Unrealistic non sequitur. No realistic system would volunteer this. | - |
| dev-a38-wrong_condition | minor | Awkward: "a voluntary enlistment of more than 179 days". Still false by 590b p28. | - |
| dev-a42-clean_reordered | minor | Awkward: stilted fronted clause. | The lesser of 50% of the present value of the IRA or $10,300 for 2025 is the most the distribution can be. |
| dev-a42-unsupported_addition | minor | Unrealistic detail: "one-page form". | - |
| dev-a46-unsupported_addition | minor | Only "line 55" is new. Using Form 5329 for this tax is on cited 590b p30. | - |
| dev-a49-negation | minor | Bare negation with no replacement value, so it doesn't answer the question. The relevant=True label is arguable. | - |
| dev-a51-unsupported_addition | minor | Near-supported: 590b p5 says the election is made by designating yourself as account owner. "Retitling" is close. | - |
| dev-a55-wrong_number | minor | Self-refuting: $650 of income next to $500 of earnings. An evaluator can catch this without the source. | - |
| dev-a56-negation | minor | Self-refuting: "All" next to $10,000 exceeding the $6,000 distribution. | - |
| dev-a56-wrong_number | minor | Self-refuting: $2,900 called $6,500 minus $4,000. An evaluator can catch this without the source. | - |
| dev-a57-unsupported_addition | minor | Unrealistic non sequitur about a withholding election. | - |
| dev-a58-unsupported_addition | minor | Unrealistic non sequitur about what the custodian is told. | - |
| dev-a59-wrong_condition | minor | Partly true: a spouse who keeps the IRA as a beneficiary, without treating it as their own, also can't contribute. The 2035 date stays wrong for a spouse. | - |
| dev-u33-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u34-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u35-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u36-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u37-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u38-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u39-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |
| dev-u40-wrongful_answer | minor | Invents a private or future fact the system could not know. Unsupported, as labeled, but easy and not a realistic hard case. The answers are obviously unknowable from any corpus. | - |

## Tally

| category | cases | blockers | blocker rate | minors |
|---|---:|---:|---:|---:|
| clean_paraphrase | 60 | 1 | 1.7% | 0 |
| clean_longer | 60 | 0 | 0.0% | 0 |
| clean_reordered | 60 | 0 | 0.0% | 3 |
| clean_noop_rewrite | 60 | 0 | 0.0% | 0 |
| negation | 60 | 0 | 0.0% | 9 |
| unsupported_addition | 60 | 9 | 15.0% | 12 |
| wrong_condition | 60 | 2 | 3.3% | 4 |
| wrong_number | 53 | 0 | 0.0% | 10 |
| wrongful_answer | 40 | 0 | 0.0% | 8 |
| incomplete | 30 | 0 | 0.0% | 0 |
| **total** | **543** | **12** | **2.2%** | **46** |

`case_fixes.jsonl` has all 12 blockers. Each fix passes `validate_case`. Replacement `added` sentences were searched in the dev publications for their key terms, not proven absent by a full read.

## Systematic patterns

1. **Additions already in the corpus: 8 of 60.** a07, a09, a10, a11, a22, a30, a56 and a59 are present or largely present in dev publications. Only a56 and a59 overlap a cited page; the other six sit on pages the question doesn't cite. An evaluator that retrieves more than the cited pages could correctly call them supported. A ninth, a03, is contradicted on its cited page.
2. **Addition vocabulary giveaway (category-level).** 48 of 60 added sentences use form, schedule, line, custodian, record-keeping or hedge words, against 3 of 60 clean_longer extras. Breakdown, added vs clean_longer: form/schedule/line 21 vs 1, custodian-type 20 vs 1, keep/records 10 vs 0, hedges 12 vs 1. Share of words not found in the question, gold or evidence separates them with AUC 0.943 (means 0.79 vs 0.34). Length doesn't (AUC 0.491). A source-free classifier could score well here, so fix this before trusting unsupported_addition results. Add supported clean_longer sentences that mention forms and custodians, and added sentences that state substantive rules.
3. **Same position every time.** All 60 clean_longer and all 60 unsupported_addition answers are the verbatim gold plus one trailing sentence. Nothing varies the position or rewords the base.
4. **Incomplete is shorter (category-level).** 28 of 30 are shorter than all four clean variants of the same question, and 25 of 30 are a word-for-word prefix of gold. Length alone gives AUC 0.906 against those clean variants. Some of this is inherent to dropping content, but only 5 remove a point from the middle or reword. Add short clean answers and incomplete answers padded with supported detail.
5. **Retained working refutes the error: 16 cases.** 10 wrong_number and 6 negation cases keep arithmetic or reasoning that contradicts the changed claim. These labels are right, but the cases are easier than they look, and a consistency check can catch them with no source. The other 43 wrong_number cases don't have this problem.
6. **Bare negation.** 12 negation cases just add "isn't" and 8 add "doesn't have to". Three (a02, a26, a49) give no replacement answer at all.
7. **Threshold direction in wrong_condition: 2 cases.** a01 and a22 attach a higher threshold to a status whose real threshold is lower, so the sentence stays true as a sufficient condition. Check for this in future scope swaps.

## Checked with no blocker

- **wrong_number:** the changed number is the only numeric difference in all 53 cases, and all are wrong for the question. Seven questions have no wrong_number case because their gold has no number. a22 ($252,000, the 2026 figure at 590a p2) and a11 ($3,650, another rule's amount at 501 p4) are good hard cases.
- **wrong_condition:** no number changed in any of the 60.
- **clean_paraphrase, clean_reordered, clean_noop_rewrite, negation:** the number sets match gold in every case.
- **clean_longer:** every extra sentence traces to the cited quotes.
- **incomplete:** every removed point is really absent, and the remaining text is right.
- **wrongful_answer:** none of the 40 is supported anywhere in the 10 publications. Matching figures such as $5,500, $8,500 and $16,500 appear only in unrelated contexts. Several are true in the real world, which fits the label because the label tests corpus support.
- **Length:** wrong_number, negation and wrong_condition stay within 0, 2.4 and 6.6 characters of gold on average, so length doesn't give them away.
