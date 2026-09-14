set -u
python -m venv /workspace/tmp/harness-pod-mkq37tee/venv >/dev/null
/workspace/tmp/harness-pod-mkq37tee/venv/bin/pip install --quiet --no-index --find-links /workspace/shared/run/cache/wheelhouse/new -r /workspace/shared/run/execute/python-jose/mutation/mutants/m013/out/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /workspace/tmp/harness-pod-mkq37tee
cp -r /workspace/shared/run/execute/python-jose/mutation/tests /workspace/tmp/harness-pod-mkq37tee/tests
if [ -d "/workspace/shared/run/execute/python-jose/mutation/mutants/m013" ]; then cp -r /workspace/shared/run/execute/python-jose/mutation/mutants/m013/. /workspace/tmp/harness-pod-mkq37tee/venv/lib/python3.12/site-packages/; fi
/workspace/tmp/harness-pod-mkq37tee/venv/bin/python -m coverage run --branch --source=. -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/workspace/shared/run/execute/python-jose/mutation/mutants/m013/out/junit.xml -o junit_family=xunit2 /workspace/tmp/harness-pod-mkq37tee/tests ; rc=$?
/workspace/tmp/harness-pod-mkq37tee/venv/bin/python -m coverage json -o /workspace/shared/run/execute/python-jose/mutation/mutants/m013/out/coverage.json >/dev/null 2>&1 || true
exit $rc
