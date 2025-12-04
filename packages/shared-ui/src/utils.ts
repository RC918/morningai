import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get initials from a name string (e.g., "John Doe" -> "JD")
 * Returns up to 2 characters, uppercase
 * Handles edge cases: empty strings, extra whitespace
 */
export function getInitials(name: string): string {
  if (!name) {
    return "";
  }
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}
