module.exports = {
  app: {
    input: 'src/lib/openapi.yaml',
    output: {
      target: 'src/lib/api-client.js',
      client: 'fetch'
    }
  }
}
