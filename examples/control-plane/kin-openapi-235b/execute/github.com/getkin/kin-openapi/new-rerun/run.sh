set -u
mkdir -p /workspace/tmp/harness-go-pod-azp1_sg1/m /workspace/tmp/harness-go-pod-azp1_sg1/gopath && cp /workspace/shared/run/cache/gomod/new/go.mod /workspace/shared/run/cache/gomod/new/go.sum /workspace/tmp/harness-go-pod-azp1_sg1/m/ && cp /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/kin_openapi_cve_cve_2026_73501_test.go /workspace/shared/run/generate/github.com/getkin/kin-openapi/tests/kin_openapi_cve_cve_2026_77354_test.go /workspace/tmp/harness-go-pod-azp1_sg1/m/
cd /workspace/tmp/harness-go-pod-azp1_sg1/m
export GOMODCACHE=/workspace/shared/run/cache/gomod/new/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/workspace/shared/run/cache/gomod/new/gocache GOPATH=/workspace/tmp/harness-go-pod-azp1_sg1/gopath HOME=/workspace/tmp/harness-go-pod-azp1_sg1
go vet . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/vet.log 2>&1 || true
go test -json -count=1 -timeout 1140s -coverprofile=/workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/cover.out -coverpkg=github.com/getkin/kin-openapi/... . > /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/test.json 2> /workspace/shared/run/execute/github.com/getkin/kin-openapi/new-rerun/build.log ; rc=$?
exit $rc
