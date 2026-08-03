# NY DFS case selection log

Source: NY DFS External Appeals Searchable Database
(https://www.dfs.ny.gov/public-appeal/search). All cases accessed
2026-08-02. Selection followed Section 3.1: adult, non-urgent
prescription-drug medical-necessity denials, preferring 2021-2025
decisions with enough clinical/denial detail for a meaningful pre-decision
packet, targeting a 4/4 upheld/overturned split.

**Search method note:** the DFS site's filter/pagination UI is
JavaScript-driven and did not return content to this session's automated
fetch tool with any query string applied (filtered and unfiltered URLs
alike returned empty results once a `?` parameter was present; only the
bare, no-filter landing URL rendered). Individual case detail pages
(`/public-appeals/case-number-<id>`) do render normally, so candidate case
numbers were identified via targeted web search against
`site:dfs.ny.gov/public-appeals`, then each candidate was fetched and read
individually to confirm Appeal Type, age range, and content quality before
acceptance. This is slower than using the site's own filters but keeps
every accepted case individually verified. **Sophia: if you have normal
browser access to the site, it's worth spot-checking a couple of these
against the live filtered search UI, and possibly finding 2-4 more
candidates that way for the optional validation split.**

## Accepted (8 of 8 target reached, 4 upheld / 4 overturned)

| case_id | public case # | year | drug | diagnosis area | outcome | age | notes |
|---|---|---|---|---|---|---|---|
| NYDEV-001 | 202203-147477 | 2022 | Myfembree | Gynecological (menorrhagia/fibroid/polyp) | upheld | 40-49 F | clean single-summary case |
| NYDEV-002 | 202211-155386 | 2022 | Azstarys | ADHD | overturned | 40-49 M | clean single-summary case |
| NYDEV-003 | 202210-154794 | 2022 | Jynarque | ADPKD (kidney) | upheld | 60-69 F | clean single-summary case |
| NYDEV-004 | 202111-143658 | 2021 | Phexxi | Contraception | overturned | 30-39 F | clean single-summary case |
| NYDEV-005 | 202201-144913 | 2022 | Nurtec ODT | Migraine | overturned | 40-49 F | clean single-summary case |
| NYDEV-006 | 202202-146311 | 2022 | Vyepti | Migraine | upheld | 20-29 F | clean single-summary case |
| NYDEV-007 | 202305-163087 | 2023 | Wegovy 2.4mg | Obesity | upheld | 30-39 F | clean single-summary case |
| NYDEV-008 | 202305-162724 | 2023 | Wegovy 0.25mg | Obesity | overturned | 50-59 F | clean single-summary case |

Balance: 4 upheld / 4 overturned (meets the 4/4 target exactly). Years:
2021 (1), 2022 (5), 2023 (2) -- all within the preferred 2021-2025 window.
Diagnosis spread: gynecological, ADHD, kidney, contraception, migraine x2,
obesity x2. Note NYDEV-007 and NYDEV-008 are both Wegovy for obesity with
opposite outcomes (upheld vs. overturned on the strength of the
comprehensive-weight-management-program documentation) -- kept both
deliberately since it's a genuinely useful near-matched pair for later
failure analysis, but flagging the repetition for Sophia's judgment call.

## Rejected candidates (and why)

| public case # | drug | reason for rejection |
|---|---|---|
| 202303-160222 | Xeljanz | Appeal Type = "Experimental/Investigational," not "Medical necessity" -- wrong track. Also the page bundles three reviewer summaries with different conclusions under one case number, making it structurally unclear as a single case for this schema. |
| 202303-160802 | Oxycontin | Appeal Type = "Formulary Exception," not "Medical necessity" -- adjacent but distinct DFS category, excluded to stay faithful to Section 3.1's literal "medical-necessity denials" framing. |
| 202104-137146 | Zolinza | Age range 10-19 (pediatric) -- fails the "adult" requirement. |
| 202204-148111 | Genotropin | Age range 10-19 (pediatric) -- fails the "adult" requirement. |

Rejected-but-not-fetched (surfaced by search, not opened, once 8 acceptable
cases were already confirmed): 202302-159141 (Apidra), 202306-164750
(Focalin XR), 202301-158444 (Cosentyx), 202302-158935 (APRETUDE),
202301-157993 (Rybelsus), 202301-157587 (Pred Forte), 202211-155517
(Tarpeyo), 202302-158607 (Qulipta), 202301-157674 (Sunosi). These remain
good candidates for the optional 2-4 case validation split -- worth
opening first if Sophia wants to add validation cases before Day 4.

## Explicitly not done this week

- No bulk scraping of the DFS database (Section 3.1 prohibits this without
  founder sign-off on terms/robots/rate limits).
- No California cases opened or even searched for -- Section 3.2 requires
  NY schemas and the baseline prompt to be stable first, and challenge
  cases must stay locked until the repository is tagged as frozen.
- No out-of-network or billing-claim cases -- Section 3.3 notes public
  IMR/external-appeal repositories are weak for these tracks; none were
  searched for.
