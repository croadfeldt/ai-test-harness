set -u
python -m venv /workspace/tmp/harness-pod-dfsjat03/venv >/dev/null
/workspace/tmp/harness-pod-dfsjat03/venv/bin/pip install --quiet --no-index --find-links /workspace/shared/run/cache/wheelhouse/new -r /workspace/shared/run/execute/python-jose/mutation/mutants/m008/out/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /workspace/tmp/harness-pod-dfsjat03
cp -r /workspace/shared/run/execute/python-jose/mutation/tests /workspace/tmp/harness-pod-dfsjat03/tests
if [ -d "/workspace/shared/run/execute/python-jose/mutation/mutants/m008" ]; then cp -r /workspace/shared/run/execute/python-jose/mutation/mutants/m008/. /workspace/tmp/harness-pod-dfsjat03/venv/lib/python3.12/site-packages/; fi
/workspace/tmp/harness-pod-dfsjat03/venv/bin/python -m coverage run --branch --source=. -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/workspace/shared/run/execute/python-jose/mutation/mutants/m008/out/junit.xml -o junit_family=xunit2 /workspace/tmp/harness-pod-dfsjat03/tests ; rc=$?
/workspace/tmp/harness-pod-dfsjat03/venv/bin/python -m coverage json -o /workspace/shared/run/execute/python-jose/mutation/mutants/m008/out/coverage.json >/dev/null 2>&1 || true
exit $rc
