set -u
mkdir -p /workspace/tmp/harness-go-pod-1mv_ubrc/m /workspace/tmp/harness-go-pod-1mv_ubrc/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-1mv_ubrc/m/ && cp /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/tests/*.go /workspace/tmp/harness-go-pod-1mv_ubrc/m/
cd /workspace/tmp/harness-go-pod-1mv_ubrc/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-1mv_ubrc/gopath HOME=/workspace/tmp/harness-go-pod-1mv_ubrc
src=$(go list -m -f '{{.Dir}}' github.com/getkin/kin-openapi) || { echo "MODULE_NOT_IN_CACHE"; exit 96; }
mkdir -p /workspace/tmp/harness-go-pod-1mv_ubrc/mutant && cp -r "$src"/. /workspace/tmp/harness-go-pod-1mv_ubrc/mutant/ && chmod -R u+w /workspace/tmp/harness-go-pod-1mv_ubrc/mutant
(cd /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m021 && find . -type f ! -name overlay.json | while read f; do cp "$f" "/workspace/tmp/harness-go-pod-1mv_ubrc/mutant/$f"; done)
go mod edit -replace github.com/getkin/kin-openapi=/workspace/tmp/harness-go-pod-1mv_ubrc/mutant

go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m021/out/vet.log 2>&1 || true
go test -json -count=1 -timeout 240s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m021/out/cover.out -coverpkg=. . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m021/out/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m021/out/build.log ; rc=$?
exit $rc
