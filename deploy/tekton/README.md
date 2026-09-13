# The harness as a Tekton pipeline

**In plain terms.** The same stages, as one PipelineRun on an OpenShift or Kubernetes cluster with
Tekton. Stage 0 runs first and fails closed. The task that runs generated tests is itself the sandbox:
a deny-all network policy, no service-account token, a read-only root, limits, and a probe that proves
each of those from inside the pod before any generated code runs.

| File | What it is |
|---|---|
| `tasks.yaml` | Three tasks: `harness-selfcheck` (stage 0), `harness-stage` (any networked stage), `harness-execute` (the sandbox pod, with the probe first) |
| `pipeline.yaml` | The pipeline: clone, self-check, intake through assess |
| `networkpolicy.yaml` | Deny everything to and from execute pods, DNS included |
| `pipelinerun.example.yaml`, `secret.example.yaml` | A run and the model Secret to copy and fill; nothing about a machine is committed |

Apply with `oc apply -k deploy/tekton -n <namespace>`, create the model Secret, then `oc create -f`
a filled PipelineRun. The harness image is built from `harness/Containerfile` and referenced by digest.

**What differs from the laptop path.** The wheelhouse for the sandbox is downloaded by the networked
stages into the shared workspace; the execute pod installs from it offline. The sandbox's isolation
comes from the pod spec and the network policy rather than from Podman flags, and the records say so
(`isolation.target: pod`). Where the cluster offers a Kata or gVisor RuntimeClass, set it on the
execute task's pod template; without one the record says "default (no Kata or gVisor)". Konflux
supplies the snapshot, Hermeto's graph, and Trusted Artifact Signer; this pipeline resolves the graph
itself and signs with the key the attest task is given.
