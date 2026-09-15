set -u
mkdir -p /workspace/tmp/harness-go-pod-mvpmkkdj/m /workspace/tmp/harness-go-pod-mvpmkkdj/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-mvpmkkdj/m/ && cp /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/tests/*.go /workspace/tmp/harness-go-pod-mvpmkkdj/m/
cd /workspace/tmp/harness-go-pod-mvpmkkdj/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-mvpmkkdj/gopath HOME=/workspace/tmp/harness-go-pod-mvpmkkdj
src=$(go list -m -f '{{.Dir}}' github.com/getkin/kin-openapi) || { echo "MODULE_NOT_IN_CACHE"; exit 96; }
mkdir -p /workspace/tmp/harness-go-pod-mvpmkkdj/mutant && cp -r "$src"/. /workspace/tmp/harness-go-pod-mvpmkkdj/mutant/ && chmod -R u+w /workspace/tmp/harness-go-pod-mvpmkkdj/mutant
(cd /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m013 && find . -type f ! -name overlay.json | while read f; do cp "$f" "/workspace/tmp/harness-go-pod-mvpmkkdj/mutant/$f"; done)
go mod edit -replace github.com/getkin/kin-openapi=/workspace/tmp/harness-go-pod-mvpmkkdj/mutant

go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m013/out/vet.log 2>&1 || true
go test -json -count=1 -timeout 240s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m013/out/cover.out -coverpkg=. . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m013/out/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/mutation/mutants/m013/out/build.log ; rc=$?
exit $rc
