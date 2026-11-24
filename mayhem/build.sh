#!/usr/bin/env bash
#
# mayhem/build.sh — build the Apache Airflow Atheris fuzz targets (Python).
#
# Airflow is fuzzed with Atheris against the IN-TREE sources (airflow-core/src, task-sdk/src,
# providers/standard/src; mayhem/af_common.py puts them on sys.path), so an edit to the checkout is
# what runs — no wheel of airflow itself is built. Third-party runtime deps (read from the two
# pyproject.toml files) and atheris come from a binary-only wheelhouse baked on the first (online)
# run and installed with --no-index, so the air-gapped re-run never reaches PyPI (SPEC §6.5).
# Mayhem needs an ELF cmd:, so each harness gets a tiny launcher (mayhem/launcher.c) that execs
# python3 on it. Launchers carry DWARF 3 debug info; no sanitizers (they would only instrument a
# 30-line exec shim — the Python code is instrumented by Atheris).
set -euo pipefail
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH
: "${SANITIZER_FLAGS=-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer}"
: "${DEBUG_FLAGS:=-g -gdwarf-3}"
: "${CC:=clang}"
: "${SRC:=/mayhem}"
: "${MAYHEM_JOBS:=$(nproc)}"
: "${PYTHONUSERBASE:=/opt/toolchains/python}"
export SANITIZER_FLAGS DEBUG_FLAGS CC SRC MAYHEM_JOBS PYTHONUSERBASE

cd "$SRC"
H="$SRC/mayhem"
WH="$H/wheelhouse"
PIP="python3 -m pip"

# 1) Deps: requirements generated from upstream's pyproject.toml (minus apache-airflow-* self refs).
mkdir -p "$WH"
if [ ! -f "$WH/POPULATED" ]; then
  python3 - airflow-core/pyproject.toml task-sdk/pyproject.toml providers/standard/pyproject.toml providers/common/compat/pyproject.toml > "$WH/requirements.txt" <<'PY'
import re, sys, tomllib
out = set()
for p in sys.argv[1:]:
    for r in tomllib.load(open(p, "rb"))["project"]["dependencies"]:
        if not re.split(r"[<>=!~;\[ ]", r, maxsplit=1)[0].lower().startswith("apache-airflow"):
            out.add(r)
out.add("atheris==3.1.0")
print("\n".join(sorted(out)))
PY
  $PIP download --only-binary :all: -d "$WH" -r "$WH/requirements.txt"
  touch "$WH/POPULATED"
fi
$PIP install --no-index --find-links "$WH" --user --break-system-packages -r "$WH/requirements.txt"

# 2) ELF launchers (fuzz target == its own standalone reproducer: Atheris replays a file argument).
for t in dag_fuzz fuzz_dag_serialization fuzz_base_serialization fuzz_serde fuzz_connection \
         fuzz_cron_timetable fuzz_config_parser fuzz_secrets_file \
         fuzz_timezone fuzz_airflowignore fuzz_dag_file_checker fuzz_asset_param \
         fuzz_comms fuzz_api_bodies fuzz_cursor fuzz_jwt fuzz_secrets_masker; do
  $CC $DEBUG_FLAGS -O1 -DSCRIPT_PATH="\"$H/$t.py\"" "$H/launcher.c" -o "$SRC/$t"
  cp -f "$SRC/$t" "$SRC/$t-standalone"
done
$CC $DEBUG_FLAGS -O1 -DORACLE_PATH="\"$H/oracle.py\"" "$H/oracle_launch.c" -o "$SRC/airflow_oracle"

# 3) Fail early if a harnessed API drifted: every harness must import.
cd "$H"
python3 -c "import af_common, atheris, airflow.sdk, airflow.serialization.serialized_objects, airflow.secrets.local_filesystem, airflow.timetables.trigger, airflow.providers.standard.operators.python, airflow.sdk.execution_time.comms, airflow.api_fastapi.core_api.datamodels.dag_run, airflow.api_fastapi.execution_api.datamodels.taskinstance, airflow.api_fastapi.common.cursors, airflow.api_fastapi.auth.tokens, airflow._shared.secrets_masker.secrets_masker"
echo ">> build.sh done"
