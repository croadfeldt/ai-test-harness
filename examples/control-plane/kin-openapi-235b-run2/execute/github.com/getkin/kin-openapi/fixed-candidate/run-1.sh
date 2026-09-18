set -u
mkdir -p /workspace/tmp/harness-go-pod-cqcqim6w/m /workspace/tmp/harness-go-pod-cqcqim6w/gopath && cp /workspace/shared/run/cache/gomod/fixed-github.com_getkin_kin-openapi/go.mod /workspace/shared/run/cache/gomod/fixed-github.com_getkin_kin-openapi/go.sum /workspace/tmp/harness-go-pod-cqcqim6w/m/ && cp /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/*.go /workspace/tmp/harness-go-pod-cqcqim6w/m/
cd /workspace/tmp/harness-go-pod-cqcqim6w/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/fixed-github.com_getkin_kin-openapi/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/fixed-github.com_getkin_kin-openapi/gocache GOPATH=/workspace/tmp/harness-go-pod-cqcqim6w/gopath HOME=/workspace/tmp/harness-go-pod-cqcqim6w
go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/fixed-candidate/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/fixed-candidate/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/fixed-candidate/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/fixed-candidate/build.log ; rc=$?
exit $rc
