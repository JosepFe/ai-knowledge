declare module 'claude-code' {
  interface PluginState {
    'secret-entry': {
      target: Shaped<string>
      name: Shaped<string>
      status: Shaped<string>
      home: Shaped<string>
    }
  }
}
