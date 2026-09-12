set -u
python -m venv /work/venv >/dev/null
/work/venv/bin/pip install --quiet --no-index --find-links /wheelhouse -r /out/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /work
cp -r /tests /work/tests
/work/venv/bin/python -m coverage run --branch --source=jose,jose -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/out/junit.xml -o junit_family=xunit2 /work/tests ; rc=$?
/work/venv/bin/python -m coverage json -o /out/coverage.json >/dev/null 2>&1 || true
exit $rc
