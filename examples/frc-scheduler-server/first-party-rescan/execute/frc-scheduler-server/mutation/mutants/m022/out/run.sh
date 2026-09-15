set -u
python -m venv /work/venv >/dev/null
/work/venv/bin/pip install --quiet --no-index --find-links /wheelhouse -r /out/requirements.txt || { echo "INSTALL_FAILED"; exit 97; }
cd /work
cp -r /tests /work/tests
# A first-party target: the application's own tree, mounted read-only, copied so a mutant can be laid over it.
if [ -d /src ]; then cp -r /src /work/src; export PYTHONPATH=/work/src; fi
if [ -d /mutant ]; then cp -r /mutant/. /work/src/; fi
/work/venv/bin/python -m coverage run --branch --source=. -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    --junitxml=/out/junit.xml -o junit_family=xunit2 /work/tests ; rc=$?
/work/venv/bin/python -m coverage json -o /out/coverage.json >/dev/null 2>&1 || true
exit $rc
