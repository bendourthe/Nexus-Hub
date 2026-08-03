type Command = (...args: unknown[]) => unknown;

const commandMap = new Map<string, Command>();
const configuration = new Map<string, unknown>();
const inputs: Array<string | undefined> = [];

export const messages = {
  information: [] as string[],
  errors: [] as string[]
};

export const commands = {
  registerCommand(name: string, command: Command): { dispose(): void } {
    commandMap.set(name, command);
    return { dispose: () => commandMap.delete(name) };
  }
};

export const workspace = {
  getConfiguration(section: string): { get<T>(key: string, defaultValue: T): T } {
    return {
      get<T>(key: string, defaultValue: T): T {
        return (configuration.get(`${section}.${key}`) as T | undefined) ?? defaultValue;
      }
    };
  }
};

export const window = {
  async showInputBox(): Promise<string | undefined> {
    return inputs.shift();
  },
  async showInformationMessage(message: string): Promise<string | undefined> {
    messages.information.push(message);
    return undefined;
  },
  async showErrorMessage(message: string): Promise<string | undefined> {
    messages.errors.push(message);
    return undefined;
  }
};

export function setConfiguration(key: string, value: unknown): void {
  configuration.set(key, value);
}

export function queueInput(value: string | undefined): void {
  inputs.push(value);
}

export async function runCommand(name: string): Promise<unknown> {
  const command = commandMap.get(name);
  if (command === undefined) {
    throw new Error(`Command not registered: ${name}`);
  }
  return command();
}

export function resetVscodeStub(): void {
  commandMap.clear();
  configuration.clear();
  inputs.length = 0;
  messages.information.length = 0;
  messages.errors.length = 0;
}
