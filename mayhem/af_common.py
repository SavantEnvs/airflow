"""Shared setup for the Airflow Atheris harnesses.

Puts the in-tree sources first on sys.path (the image runs Airflow from the checkout, not from an
installed wheel, so a patch to the source is what gets fuzzed) and points AIRFLOW_HOME at a fresh
scratch dir under $TMPDIR, because importing airflow writes airflow.cfg there. Nothing here depends on
the fuzz input.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("providers/common/compat/src", "providers/standard/src", "task-sdk/src", "airflow-core/src"):
    p = os.path.join(ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

if "AIRFLOW_HOME" not in os.environ:
    os.environ["AIRFLOW_HOME"] = tempfile.mkdtemp(prefix="airflow-home-")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "False")
