set -u
python -m venv /workspace/tmp/harness-pod-xfeeg9ms/venv >/dev/null
/workspace/tmp/harness-pod-xfeeg9ms/venv/bin/pip install --quiet --no-index --find-links /workspace/shared/run/cache/wheelhouse/new -r /workspace/shared/run/execute/python-jose/mutation/mutants/m022/out/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /workspace/tmp/harness-pod-xfeeg9ms
cp -r /workspace/shared/run/execute/python-jose/mutation/tests /workspace/tmp/harness-pod-xfeeg9ms/tests
if [ -d "/workspace/shared/run/execute/python-jose/mutation/mutants/m022" ]; then cp -r /workspace/shared/run/execute/python-jose/mutation/mutants/m022/. /workspace/tmp/harness-pod-xfeeg9ms/venv/lib/python3.12/site-packages/; fi
/workspace/tmp/harness-pod-xfeeg9ms/venv/bin/python -m coverage run --branch --source=. -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/workspace/shared/run/execute/python-jose/mutation/mutants/m022/out/junit.xml -o junit_family=xunit2 /workspace/tmp/harness-pod-xfeeg9ms/tests ; rc=$?
/workspace/tmp/harness-pod-xfeeg9ms/venv/bin/python -m coverage json -o /workspace/shared/run/execute/python-jose/mutation/mutants/m022/out/coverage.json >/dev/null 2>&1 || true
exit $rc
