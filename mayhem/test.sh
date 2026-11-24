#!/usr/bin/env bash
#
# mayhem/test.sh — RUN the airflow behavioral oracle that mayhem/build.sh produced.
#
# It runs the known-answer self-test via the /mayhem/airflow_oracle launcher (a NON-system ELF, so
# the verify-repo §6.3 sabotage neuter can trip it) and asserts that airflow parsed, walked, and
# round-tripped a known calendar to specific values. A no-op / exit(0) PATCH FAILS this (the expected
# SELFTEST_PASS marker + values are absent). Emits a CTRF (https://ctrf.io) summary. It never builds.
set -uo pipefail
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH
: "${SRC:=/mayhem}"
cd "$SRC"

ORACLE="$SRC/airflow_oracle"

# emit_ctrf <tool> <passed> <failed> [skipped] [pending] [other]
emit_ctrf() {
  local tool="$1" passed="$2" failed="$3" skipped="${4:-0}" pending="${5:-0}" other="${6:-0}"
  local tests=$(( passed + failed + skipped + pending + other ))
  cat > "${CTRF_REPORT:-$SRC/ctrf-report.json}" <<JSON
{
  "results": {
    "tool": { "name": "$tool" },
    "summary": {
      "tests": $tests,
      "passed": $passed,
      "failed": $failed,
      "pending": $pending,
      "skipped": $skipped,
      "other": $other
    }
  }
}
JSON
  printf 'CTRF {"results":{"tool":{"name":"%s"},"summary":{"tests":%d,"passed":%d,"failed":%d,"pending":%d,"skipped":%d,"other":%d}}}\n' \
    "$tool" "$tests" "$passed" "$failed" "$pending" "$skipped" "$other"
  [ "$failed" -eq 0 ]
}

if [ ! -x "$ORACLE" ]; then
  echo "FAIL: $ORACLE missing — mayhem/build.sh did not build the oracle launcher" >&2
  emit_ctrf "airflow-knownanswer" 0 1
  exit 1
fi

# The oracle prints one PASS/FAIL line per known-answer check; count them. A neutered launcher
# prints nothing, so every expected check is counted as failed.
EXPECTED=7
out="$("$ORACLE" 2>&1)"; rc=$?
echo "$out"
passed=$(printf '%s\n' "$out" | grep -c '^PASS ' || true)
grep -q '^PASS connection host=db.example.com port=5432$' <<<"$out" || passed=0
failed=$(( EXPECTED - passed ))
[ "$rc" -eq 0 ] || [ "$failed" -gt 0 ] || failed=1
emit_ctrf "airflow-knownanswer" "$passed" "$failed"
