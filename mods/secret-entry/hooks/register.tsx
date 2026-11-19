import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const PANE = 'secret-entry'
// Where the native dialog script lives: the ai-knowledge repo. Change it if the repo is cloned elsewhere.
const SECRET_DIALOG = '/mnt/c/Repos/josep-repos/ai-knowledge/scripts/secret_dialog.py'

// What each MCP token is for, shown in the secure dialog. Keep it factual; scopes depend on the token you created.
const INFO: Record<string, string> = {
  gitlab: 'GitLab: MCP de repositorios, merge requests y pipelines. Token de acceso personal de GitLab.',
  'grafana-dev': 'Grafana dev: MCP de métricas, logs y trazas del entorno de desarrollo. Token de service account.',
  'grafana-prod': 'Grafana prod: MCP de métricas, logs y trazas de producción. Token de service account.',
  jfrog: 'JFrog: MCP de artefactos. Token de acceso de JFrog.',
  ado: 'Azure DevOps: MCP de work items y repos. Token personal.',
  vsphere: 'vSphere: MCP de inventario de máquinas virtuales. Contraseña del usuario.',
}

// Presets fill the file and variable for an MCP token. The dialog applies the same encoding as ai-config/mcp/set-mcp-secret.sh.
const PRESETS = [
  { label: 'gitlab', name: 'GITLAB_PERSONAL_ACCESS_TOKEN' },
  { label: 'ado', name: 'PERSONAL_ACCESS_TOKEN', base64: true },
  { label: 'grafana-dev', name: 'GRAFANA_SERVICE_ACCOUNT_TOKEN' },
  { label: 'grafana-prod', name: 'GRAFANA_SERVICE_ACCOUNT_TOKEN' },
  { label: 'jfrog', name: 'JFROG_ACCESS_TOKEN' },
  { label: 'vsphere', name: 'GOVC_PASSWORD', extra: 'MCP_VSPHERE_PASSWORD' },
] as const

const target = atom({ plugin: 'secret-entry', key: 'target' } as const, '', { shape: 'target-1' })
const name = atom({ plugin: 'secret-entry', key: 'name' } as const, '', { shape: 'name-1' })
const status = atom({ plugin: 'secret-entry', key: 'status' } as const, '', { shape: 'status-1' })
// Home folder, read once when the session starts: rendering must not run processes.
const home = atom({ plugin: 'secret-entry', key: 'home' } as const, '', { shape: 'home-1' })

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'secrets',
      description: 'Guardar un secreto en un fichero (token de MCP o variable de un .env) en una ventana segura',
    })
    const found = await $.process.run(['printenv', 'HOME'])
    await update($, home, () => found.stdout.trim())
    void $.ui.open({ id: PANE, title: 'Secretos' })

    return next(e)
  })

  on('command.run', { command: 'secrets' }, async $ => {
    await $.ui.open({ id: PANE, title: 'Secretos' })

    return { text: 'Panel de secretos abierto.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Input, Text } = $.ui.resolve(e)
    const file = await read($, target)
    const key = await read($, name)
    const message = await read($, status)
    const dir = `${await read($, home)}/.config/ai-knowledge/local/mcp`

    // The value is never typed in the panel: it is always asked in the secure dialog.
    const askWithDialog = async () => {
      if (file === '' || key === '') return update($, status, () => 'Indica el archivo y la variable antes.')
      const preset = PRESETS.find(p => file === `${dir}/${p.label}.env`)
      const service = preset ? INFO[preset.label] : 'Variable de un fichero de entorno.'
      const label = `${service}\nArchivo: ${file}\nVariable: ${key}\nPega el valor y pulsa Guardar.`
      const args = ['python3', SECRET_DIALOG, '--detach', '--file', file, '--key', key, '--label', label]
      if (preset && 'base64' in preset) args.push('--base64-user')
      if (preset && 'extra' in preset) args.push('--also', preset.extra)
      const run = await $.process.run(args)
      update($, status, () => (run.exitCode === 0 ? run.stdout.trim() : `No se guardó: ${run.stderr.trim() || 'cancelado'}`))
    }

    return (
      <Box flexDirection="column">
        <Text>Preajustes MCP (rellenan archivo y variable):</Text>
        <Box flexDirection="row">
          {PRESETS.map(p => (
            <Button
              key={p.label}
              onPress={() => {
                update($, target, () => `${dir}/${p.label}.env`)
                update($, name, () => p.name)
              }}
            >
              {p.label}
            </Button>
          ))}
        </Box>
        <Input
          key="target"
          label="Archivo"
          value={file}
          placeholder="ruta absoluta, p. ej. /mnt/c/Repos/mi-proyecto/.env"
          onSubmit={v => update($, target, () => v.trim())}
        />
        <Input
          key="name"
          label="Variable"
          value={key}
          placeholder="NOMBRE_DE_LA_VARIABLE"
          onSubmit={v => update($, name, () => v.trim())}
        />
        <Button variant="primary" onPress={() => askWithDialog()}>Pedir el valor en ventana segura</Button>
        {message !== '' && <Text dimColor>{message}</Text>}
        <Button role="dismiss" onPress={() => $.ui.close({ id: PANE })}>Cerrar</Button>
      </Box>
    )
  })
}
