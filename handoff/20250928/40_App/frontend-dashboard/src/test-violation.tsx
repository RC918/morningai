// Test file to verify Stage 2 blocking works
import { Button } from '@radix-ui/react-button'
import { Dialog } from '@radix-ui/react-dialog'

export function TestViolation() {
  const buttonText = 'This should be blocked'
  return (
    <Dialog>
      <Button>{buttonText}</Button>
    </Dialog>
  )
}
