/**
 * AppleButton Adapter for frontend-dashboard
 * 
 * This is an adapter component that wraps the shared-ui AppleButton
 * and injects frontend-dashboard-specific haptic feedback and spring animation behavior.
 * 
 * The visual implementation lives in @morningai/shared-ui, while this adapter
 * provides the application-specific non-UI functionality.
 */

import * as React from "react"
import {
  AppleButton as BaseAppleButton,
  type AppleButtonProps as BaseAppleButtonProps,
  appleButtonVariants,
} from "@morningai/shared-ui"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"

export type AppleButtonProps = BaseAppleButtonProps

export function AppleButton(props: AppleButtonProps) {
  const springConfig = getSpringConfig("snappy")

  return (
    <BaseAppleButton
      {...props}
      springConfig={springConfig}
      onHapticFeedback={(el, type) => triggerHaptic(el, type)}
    />
  )
}

AppleButton.displayName = "AppleButton"

export { appleButtonVariants }
