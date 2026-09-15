set -u
mkdir -p /workspace/tmp/harness-go-pod-34kyegng/m /workspace/tmp/harness-go-pod-34kyegng/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-34kyegng/m/ && cp /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/*.go /workspace/tmp/harness-go-pod-34kyegng/m/
cd /workspace/tmp/harness-go-pod-34kyegng/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-34kyegng/gopath HOME=/workspace/tmp/harness-go-pod-34kyegng
go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/new/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/build.log ; rc=$?
exit $rc
