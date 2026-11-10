# Role-doc pre-flight checklist

Run before committing a new or refreshed role doc. Every item exists because it was missed once.

## Grounding
- [ ] Grounding note names the repos scanned AND today's date.
- [ ] Every file path in the doc was opened (or returned by a scan) this session.
- [ ] Every version/count/status was read from its source of truth this session — never from a
      sibling role doc (three docs once disagreed on two version numbers).
- [ ] Known gaps are named as gaps, not omitted; absent controls stated as absent.

## Opening gap list
- [ ] Dated, numbered, each item cites file:line and a severity.
- [ ] The doc instructs: keep it versioned, report session-over-session deltas, closed items need
      proof (merged PR, passing probe, rendered screenshot).

## Skills wiring
- [ ] Every id verified to resolve — session listing OR on-disk path. Both failure modes are real.
- [ ] Each skill bullet says WHEN, not just that it exists.
- [ ] The obvious ones for the lane are present (schema work → your database/migration skill; customer prose → a
      prose-editing skill; browser acceptance → a browser-driving skill; dashboards → a charting skill).

## Boundaries
- [ ] Reports to the steward; sticky; draft-PR discipline; Conventional Commit examples match the lane.
- [ ] Bordering human gates named as facts about the tools. Read-only owners state fix-routing.
- [ ] Isolation stated where the lane touches deployed instances (separate environments or customer instances never mix, even read-only).
- [ ] Handoffs name real sibling owners both directions.
- [ ] Model pin matches the profile; wrapper frontmatter and roster row agree.
- [ ] Adjacent scope-fence items restated as never-relitigate rules.

## Style
- [ ] First person, senior voice, no evangelism; Decision Test applied with real examples where the lane's product makes model calls.
- [ ] ~150–220 lines; every section earns its length.
