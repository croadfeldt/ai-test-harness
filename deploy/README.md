# Deploying and triggering the harness

| Directory | What it is |
|---|---|
| `tekton/` | The pipeline on OpenShift Pipelines: one task per stage, the execute pod as the sealed sandbox |
| `tekton/triggers/` | A GitHub webhook and a weekly schedule that create PipelineRuns of that pipeline |
| `github-actions/` | A complete workflow for a repository on GitHub: pull requests, pushes to the default branch, a schedule, by hand |
| `gitlab-ci/` | The same for GitLab: merge requests, pushes, pipeline schedules |
| `jenkins/` | A declarative Jenkinsfile for multibranch and pull request jobs |
| `azure-pipelines/` | The same for Azure Pipelines: pull requests, pushes, schedules |
| `generic/` | `run-and-propose.sh`: the five steps every engine performs, for any engine that can run a shell step |

Every path ends in `harness run` or the pipeline's stages on two refs of a repository given by URL, then
`harness propose` to open the test pull request, and every path produces the same run directory: the
story, the packet, the pull request text, the records.
[Document 13](../docs/13-running-on-real-repositories.md) explains which refs to pass for which event.
