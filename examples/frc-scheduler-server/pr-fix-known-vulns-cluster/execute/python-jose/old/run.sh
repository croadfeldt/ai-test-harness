set -u
python -m venv /workspace/tmp/harness-pod-za79yvw3/venv >/dev/null
/workspace/tmp/harness-pod-za79yvw3/venv/bin/pip install --quiet --no-index --find-links /workspace/shared/run/cache/wheelhouse/old -r /workspace/shared/run/execute/python-jose/old/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /workspace/tmp/harness-pod-za79yvw3
cp -r /workspace/shared/run/generate/python-jose/tests /workspace/tmp/harness-pod-za79yvw3/tests
if [ -d "/nonexistent" ]; then cp -r /nonexistent/. /workspace/tmp/harness-pod-za79yvw3/venv/lib/python3.12/site-packages/; fi
/workspace/tmp/harness-pod-za79yvw3/venv/bin/python -m coverage run --branch --source=jose,jose -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/workspace/shared/run/execute/python-jose/old/junit.xml -o junit_family=xunit2 /workspace/tmp/harness-pod-za79yvw3/tests ; rc=$?
/workspace/tmp/harness-pod-za79yvw3/venv/bin/python -m coverage json -o /workspace/shared/run/execute/python-jose/old/coverage.json >/dev/null 2>&1 || true
exit $rc
