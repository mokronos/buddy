import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:10001/openapi.json',
  output: 'app/src/buddy-client',
});
