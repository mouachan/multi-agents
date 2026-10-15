/** OpenShell sandbox: one run_python execution and the policy in force. */

export interface SandboxDenial {
  type: 'network' | 'filesystem' | string
  verdict: string
  detail: string
}

export interface SandboxExecution {
  /** Code executed (tools that build it themselves, e.g. compute_payout) */
  code?: string
  success?: boolean
  exit_code?: number
  stdout?: string
  stderr?: string
  denials?: SandboxDenial[]
  error?: string
  sandbox?: {
    name?: string
    image?: string
    policy?: string
    reused?: boolean
    ready_ms?: number
    duration_ms?: number
  }
}

/** OpenShell policy file (YAML schema of the OpenShell gateway) */
export interface SandboxPolicy {
  version?: number
  filesystem_policy?: { include_workdir?: boolean; read_only?: string[]; read_write?: string[] }
  landlock?: { compatibility?: string }
  process?: { run_as_user?: string; run_as_group?: string }
  network_policies?: Record<string, unknown>
}

export interface SandboxInfo {
  policy: SandboxPolicy
  policy_yaml: string
  image: string
  gateway: string
  workspace: string
  python: string
  reuse: boolean
  warm_sandbox?: string | null
  max_exec_timeout_s?: number
  openshell?: { status?: string; endpoint?: string; version?: string; error?: string }
}

export type SandboxScenario = 'compute' | 'identity' | 'network' | 'write_system' | 'read_outside'

export interface SandboxDemoResult extends SandboxExecution {
  scenario: SandboxScenario
  expect: 'allowed' | 'denied'
  code: string
}

/** Code passed to run_python, from the tool-call arguments ({"code": "...", "timeout_s": 20}) */
export function sandboxCode(args?: string): string {
  if (!args) return ''
  try {
    const parsed = JSON.parse(args)
    return typeof parsed?.code === 'string' ? parsed.code : args
  } catch {
    return args
  }
}
