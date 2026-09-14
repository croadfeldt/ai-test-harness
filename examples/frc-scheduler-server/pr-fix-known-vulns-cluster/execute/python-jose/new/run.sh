set -u
python -m venv /workspace/tmp/harness-pod-ui5roqsb/venv >/dev/null
/workspace/tmp/harness-pod-ui5roqsb/venv/bin/pip install --quiet --no-index --find-links /workspace/shared/run/cache/wheelhouse/new -r /workspace/shared/run/execute/python-jose/new/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /workspace/tmp/harness-pod-ui5roqsb
cp -r /workspace/shared/run/generate/python-jose/tests /workspace/tmp/harness-pod-ui5roqsb/tests
if [ -d "/nonexistent" ]; then cp -r /nonexistent/. /workspace/tmp/harness-pod-ui5roqsb/venv/lib/python3.12/site-packages/; fi
/workspace/tmp/harness-pod-ui5roqsb/venv/bin/python -m coverage run --branch --source=jose,jose -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/workspace/shared/run/execute/python-jose/new/junit.xml -o junit_family=xunit2 /workspace/tmp/harness-pod-ui5roqsb/tests ; rc=$?
/workspace/tmp/harness-pod-ui5roqsb/venv/bin/python -m coverage json -o /workspace/shared/run/execute/python-jose/new/coverage.json >/dev/null 2>&1 || true
exit $rc
