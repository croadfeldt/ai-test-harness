set -u
mkdir -p /workspace/tmp/harness-go-pod-u3x91to2/m /workspace/tmp/harness-go-pod-u3x91to2/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-u3x91to2/m/ && cp /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/*.go /workspace/tmp/harness-go-pod-u3x91to2/m/
cd /workspace/tmp/harness-go-pod-u3x91to2/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-u3x91to2/gopath HOME=/workspace/tmp/harness-go-pod-u3x91to2
go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/new/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/new/build.log ; rc=$?
exit $rc
