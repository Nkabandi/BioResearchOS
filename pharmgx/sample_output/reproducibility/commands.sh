#!/usr/bin/env bash
# Reproduce this ClawBio PharmGx report.
# Input file: demo_patient.txt
# Input SHA-256: ffe44b340edfbb21abf648f00c2ce68715f5c9453a590caef753bc25e316c5cc
set -euo pipefail

python pharmgx_reporter.py --input demo_patient.txt --output report
