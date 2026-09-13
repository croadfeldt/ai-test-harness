"""Pipeline stages. Each stage is a function that reads the previous stage's files from the work
directory and writes its own. Stage order: intake, analyze, generate, execute, triage, packet, attest,
assess."""
