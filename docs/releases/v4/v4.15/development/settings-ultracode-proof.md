# Settings Ultracode Proof

This record covers the correction from Nexus Ultra to Claude's native Ultracode mode. The mode is a separate workflow setting, while its effort value remains valid for the native effort enum.

| ID | Write | Status | Observation |
|---|---|---|---|
| W37 | Claude `ultracode` and existing project mode overrides | proven | Bundled Claude 2.1.318 reports `Current effort level: xhigh ... Ultracode on`; CLI mapping, readback and reset regressions cover the engine writes |

## Native Consumer

The installed VS Code Claude binary 2.1.318 was run with `/effort status`, a disposable settings file containing `ultracode: true` and `env.CLAUDE_CODE_EFFORT_LEVEL: xhigh`, isolated configuration paths and a local-only API destination. It returned success, `Ultracode on`, zero model turns, zero API duration and zero cost. The result is retained at Documents `nx-ultracode-031/native-result.json`.

Nexus Max remains Claude `max` with Ultracode off. Selecting any lower level disables the mode; selecting Ultra enables it and uses `xhigh`, matching the native `--effort ultracode` behavior. Existing project mode keys are synchronized without introducing new project keys; reset restores the recorded originals.

The [official model configuration documentation](https://code.claude.com/docs/en/model-config) names `ultracode: true`, distinguishes it from effort levels, and confirms that the environment effort variable does not accept `ultracode`. Organization limits, unsupported models and disabled workflows can still restrict native availability.
