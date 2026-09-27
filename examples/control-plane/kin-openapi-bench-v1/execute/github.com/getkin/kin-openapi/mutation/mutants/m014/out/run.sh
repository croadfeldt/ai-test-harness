set -u
mkdir -p /work/m /work/gopath && cp /mod/go.mod /mod/go.sum /work/m/ && cp /tests/*.go /work/m/
cd /work/m
export GOMODCACHE=/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/gocache GOPATH=/work/gopath HOME=/work
src=$(go list -m -f '{{.Dir}}' github.com/getkin/kin-openapi) || { echo "MODULE_NOT_IN_CACHE"; exit 96; }
mkdir -p /work/mutant && cp -r "$src"/. /work/mutant/ && chmod -R u+w /work/mutant
(cd /mutant && find . -path ./out -prune -o -type f ! -name overlay.json ! -name mutant.patch -print | while read f; do cp "$f" "/work/mutant/$f"; done)
go mod edit -replace github.com/getkin/kin-openapi=/work/mutant

go vet . > /out/vet.log 2>&1 || true
go test -json -count=1 -timeout 240s -coverprofile=/out/cover.out -coverpkg=. . > /out/test.json 2> /out/build.log ; rc=$?
exit $rc
