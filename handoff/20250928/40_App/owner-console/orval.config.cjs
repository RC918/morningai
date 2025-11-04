module.exports = {
  'agent-registry': {
    input: '../../30_API/openapi/agent-registry-v1.yaml',
    output: {
      target: 'src/lib/generated/agent-registry-api.ts',
      client: 'fetch',
      mode: 'tags-split',
      override: {
        mutator: {
          path: 'src/lib/api-client.ts',
          name: 'apiClient'
        }
      }
    }
  },
  'owner-console': {
    input: 'src/lib/openapi.yaml',
    output: {
      target: 'src/lib/generated/owner-console-api.ts',
      client: 'fetch',
      mode: 'tags-split',
      override: {
        mutator: {
          path: 'src/lib/lib/api-client.ts',
          name: 'apiClient'
        }
      }
    }
  }
}
