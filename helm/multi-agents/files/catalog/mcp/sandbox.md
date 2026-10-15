# Sandboxed Code Interpreter MCP Server

**MCP Server Summary:**
`run_python` executes Python code in an **OpenShell sandbox**: exact computations for the agents
(e.g. a claim payout) without giving the code access to the cluster, the network or the data.

## Sandbox policy
- **Filesystem (Landlock, hard requirement):** read-only `/usr /lib /lib64 /etc /proc`,
  read-write `/sandbox /tmp` only
- **Network:** denied (no egress policy)
- **Process:** runs as the unprivileged `sandbox` user
- Denials (network, filesystem) are reported with the result and shown in the application

## Demonstration
The *Sandbox* page of the application shows the policy in force and runs five scenarios against it:
a computation (allowed), the identity of the process, a network call, a write outside the workspace
and a read of a protected path (denied).

## Used by
Claims Processing Agent: `compute_payout` (Claims records server) runs its computation here, and
`run_python` is available to the agent in the chat.
