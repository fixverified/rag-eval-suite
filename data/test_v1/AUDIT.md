# Test set audit

**Verdict:** 21 wrong labels found and fixed, plus 4 cases that embedded the same text. No gold answers, key points or unanswerable questions changed.

## Scope
- Questions: test-a01..test-a30, test-u01..test-u20 (50).
- Cases checked: 664.
- Sources: page text for the cited pages, plus searches across all ten publications with hyphenation removed.
- Not checked: other questions, the shift set, evaluators/, results/.

## Blockers by category
| Category | Fixed |
|---|---|
| Gold, key points | 0 |
| Unanswerable questions | 0 |
| wrongful_answer, clean_refusal | 0 |
| clean variants | 0 |
| bad_citation, clean_cited | 0 |
| incomplete | 0 |
| negation | 0 |
| context_number | 7 |
| wrong_condition | 5 |
| unsupported_addition | 4 |
| wrong_number | 2 |
| number_format | 2 |
| copied_source | 1 |
| **Total** | **21** |

## Changes (cases.jsonl and the matching answer in tasks.jsonl)
| Case | Reason |
|---|---|
| test-a01-unsupported_addition | Old addition (leased car) was close to a context sentence on owned or leased cars and the standard rate. |
| test-a02-context_number | $90 is not in the context; $50 is. |
| test-a04-wrong_number | Self-refuting: $440 a day is not $153,300 a year. |
| test-a04-context_number | Self-refuting: $420 a day is not $1,800 a year. $480 is in the context. |
| test-a06-unsupported_addition | Old addition followed from the context rule that amounts paid must be divided by time spent. |
| test-a06-copied_source | Old passage stated the excluded $30 of the $300, which gives the answer by subtraction. |
| test-a09-unsupported_addition | Old addition followed from the percentage depending only on AGI. |
| test-a15-context_number | 90 is not in the context; 4 years is. |
| test-a16-context_number | $17,880 is not in the context; $8,490 is. |
| test-a17-wrong_condition | Old text was true: the table's footnote sends qualifying married-filing-separately filers to that column, which shows the same credit. |
| test-a18-wrong_number | Self-refuting: 25% of $10,000 is not $2,000. |
| test-a18-number_format | Self-refuting: 20% of $10,000 is not $2.4k. |
| test-a18-context_number | Self-refuting: 20% of $10,000 can't reach a $5,000 maximum. Both new values are in the context. |
| test-a19-number_format | Self-refuting: range ran past the stated cutoff. |
| test-a19-context_number | Self-refuting: reversed range from $160,000 down to $90,000. |
| test-a20-wrong_condition | Old text was literally true, since a per-beneficiary cap also bounds each contributor. |
| test-a25-wrong_condition | Old text was literally true for itemizers; it did not exclude anyone. |
| test-a26-unsupported_addition | Old addition followed from the context definition of a prescribed drug. |
| test-a26-wrong_condition | Old text was literally true for that age group; it did not exclude anyone. |
| test-a28-context_number | 3 is not in the context; 13 is. |
| test-a30-wrong_condition | Old text was literally true for that subgroup; it did not exclude anyone. |

Carried over because they embed a changed answer:

- test-a04-padding
- test-a18-padding
- test-a20-prompt_injection
- test-a26-prompt_injection

questions.jsonl and contexts.json were not changed, so no rebuild was needed. The unsupported_addition `added` field was updated for all 4 of those cases. validate_question and validate_case return no problems for the whole file (100 questions, 1,333 cases), and every answer task matches its case.

## Judgment calls, left unchanged
- test-a14 wrong_condition (married filing separately): kept. The separated-spouse rule needs a qualifying child, so it is false for a filer with none.
- test-a18 unsupported_true: kept. The no-gold context gives the $2,000 maximum but not the 20% of $10,000 rule, so the answer is still not fully supported.
- test-a18 incomplete: kept. The maximum is no longer stated, though it can be worked out from 20% of $10,000.
- test-a29 context_number: 27 appears in context only in the page header ("Page 9 of 27"). It meets the rule as written but is a weak distractor.
- test-a10 and test-a30 clean_longer add a sentence fragment copied from a source list; test-a12 clean_longer says "separately" oddly. All are supported, so the labels stand.
- test-a04 number_format ($0.16 million) is loose against $420 a day, but it is plainly a different amount from the source figure.
- test-u03 cites 501 p7, which gives only a relationship between filing statuses and no amount, so refusal stands. test-u01: 970 p16 has only an example amount of the additional credit, not a maximum.
