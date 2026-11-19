import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const PANE = 'secret-entry'

// Presets fill the file and variable for an MCP token, with the same encoding as ai-config/mcp/set-mcp-secret.sh.
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

// Sets or adds KEY=value and leaves every other line of the file as it is.
const upsert = (text: string, key: string, value: string) => {
  const lines = text.split('\n').filter(line => line !== '')
  const found = lines.some(line => line.startsWith(`${key}=`))
  const next = lines.map(line => (line.startsWith(`${key}=`) ? `${key}=${value}` : line))
  return (found ? next : [...next, `${key}=${value}`]).join('\n') + '\n'
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'secrets',
      description: 'Guardar una variable secreta en un fichero (.env o un token MCP) sin pasarla por el chat',
    })
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
    // Token files live in ai-knowledge's own folder, outside any repo.
    const home = (await $.process.run(['sh', '-c', 'printf %s "$HOME"'])).stdout.trim()
    const dir = `${home}/.config/ai-knowledge/local/mcp`

    const save = async (raw: string) => {
      const value = raw.trim()
      if (file === '' || key === '') return update($, status, () => 'Indica el archivo y la variable antes del valor.')
      if (value === '') return update($, status, () => 'Valor vacío: no se ha guardado nada.')

      // Presets only apply when the file is the MCP token file of that preset.
      const preset = PRESETS.find(p => file === `${dir}/${p.label}.env`)
      let text = ''
      try {
        text = await $.fs.read(file)
      } catch {
        // Missing file: it is created with just this variable.
      }

      let updated = upsert(text, key, preset && 'base64' in preset ? btoa(`:${value}`) : value)
      if (preset && 'extra' in preset) updated = upsert(updated, preset.extra, value)
      if (preset) await $.process.run(['mkdir', '-p', '-m', '700', dir])
      await $.fs.write(file, updated)

      const mode = await $.process.run(['chmod', '600', file])
      if (mode.exitCode !== 0) return update($, status, () => `Guardado, pero no se pudo poner 600: ${file}`)

      update($, status, () => `Guardado ${key} en ${file}.`)
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
        <Input
          key="value"
          label="Valor"
          placeholder="Pega el valor y pulsa Enter"
          submitLabel="Guardar"
          autoFocus
          onSubmit={v => save(v)}
        />
        {message !== '' && <Text dimColor>{message}</Text>}
        <Button role="dismiss" onPress={() => $.ui.close({ id: PANE })}>Cerrar</Button>
      </Box>
    )
  })
}
