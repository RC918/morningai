import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

process.env.VITE_API_BASE_URL = 'http://test.local';

afterEach(() => {
  cleanup();
});
