// Test file to verify Stage 3 blocking functionality
// This file intentionally contains a violation to test enforcement

import { Dialog } from '@radix-ui/react-dialog';

export function TestComponent() {
  return <Dialog />;
}
