# Project Structure

One folder per client project. `cp -r projects/TEMPLATE projects/<name>`
then fill in.

```
projects/<name>/
├── intake_form.md    # what the client asked for (fill from intake)
├── README.md         # project journal: status, decisions, next actions
├── input/            # files the client uploaded
├── analysis/         # cleaned data, notebooks, scripts (runs)
├── evidence/         # evidence_table.py output: verified citations + table
├── report/           # report_generator.py output: report.md + report.html (PDF)
└── deliverable/      # the final handoff (PDF, reference file, summary)
```

## README.md skeleton

```markdown
# <Client> — <Topic>

- Status: new | confirmed | intake | analysis | verification | delivered | review | closed
- Deadline: <date>
- Budget: $<quote> (deposit: $<x> paid)

## Pipeline
1. intake_form.md filled
2. run: python evidence/evidence_table.py --input ... --output evidence/output/
3. run: python reports/report_generator.py --evidence evidence/output/ --output report/
4. review report.md, export report.html -> PDF
5. copy to deliverable/, send, ask for review

## Notes