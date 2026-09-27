set -u
mkdir -p /workspace/tmp/harness-go-pod-gtwkemlo/m /workspace/tmp/harness-go-pod-gtwkemlo/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-gtwkemlo/m/ && cp /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/*.go /workspace/tmp/harness-go-pod-gtwkemlo/m/
cd /workspace/tmp/harness-go-pod-gtwkemlo/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-gtwkemlo/gopath HOME=/workspace/tmp/harness-go-pod-gtwkemlo
go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/build.log ; rc=$?
exit $rc
