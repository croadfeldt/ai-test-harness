set -u
mkdir -p /work/m && cp /mod/go.mod /mod/go.sum /work/m/ && cp /tests/*.go /work/m/
cd /work/m
export GOMODCACHE=/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/gocache GOPATH=/work/gopath HOME=/work
go vet . > /out/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/out/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /out/test.json 2> /out/build.log ; rc=$?
exit $rc
