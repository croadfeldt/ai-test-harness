# Tekton Triggers for the harness pipeline

A GitHub webhook to the EventListener creates a PipelineRun of `ai-test-harness` (see `../pipeline.yaml`)
with `repo-url`, `base` and `head` taken from the event: a pull request maps its base branch and
`refs/pull/<number>/head`; a push to the default branch maps the commit before and after. The
interceptor checks the webhook secret and filters the event types. A scheduled rescan is the CronJob
in `cronjob-rescan.yaml`, which creates a PipelineRun with `head` alone.

```
oc apply -k deploy/tekton/triggers/
oc -n ai-test-harness get route el-ai-test-harness   # the webhook URL for the repository's settings
```

Secrets: `github-webhook` (the shared secret), and `harness-model` as for any run. Nothing merges.
