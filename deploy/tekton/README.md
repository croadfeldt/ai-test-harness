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

**One workspace.** Every task binds one workspace, `shared`, and uses `run/`, `source/`, and `udlm/`
under it. Tekton's coscheduling helper allows a task pod one persistent claim, and binding one claim to
three workspaces left the helper for the second binding uncreated, so the pods never scheduled.

**What differs from the laptop path.** The wheelhouse for the sandbox is downloaded by the networked
stages into the shared workspace; the execute pod installs from it offline. The sandbox's isolation
comes from the pod spec and the network policy rather than from Podman flags, and the records say so
(`isolation.target: pod`). Where the cluster offers a Kata or gVisor RuntimeClass, set it on the
execute task's pod template; without one the record says "default (no Kata or gVisor)". Konflux
supplies the snapshot, Hermeto's graph, and Trusted Artifact Signer; this pipeline resolves the graph
itself and signs with the key the attest task is given.

**Getting the results out.** The run directory lives on the shared claim. Copy it with a pod that
mounts the claim and has `tar` (the harness image does; a minimal base image may not):

```
oc run ws-copy -n ai-test-harness --restart=Never --image=<harness image by digest> \
  --overrides='{"spec":{"volumes":[{"name":"w","persistentVolumeClaim":{"claimName":"harness-shared"}}],
  "containers":[{"name":"p","image":"<harness image by digest>","command":["sleep","1800"],"volumeMounts":[{"name":"w","mountPath":"/w"}]}]}}'
oc exec -n ai-test-harness ws-copy -- sh -c 'cd /w/run && tar cf - --exclude=cache --exclude=scratch .' | tar xf - -C ./run
oc delete pod ws-copy -n ai-test-harness
```

`cache/` holds downloaded wheels and `scratch/` the generator's working copies; both are recreated
by a run. Clear the rest of `run/` before a new run on the same claim, or give the run its own claim.
The committed example PipelineRun has placeholders for the image and the repository.
