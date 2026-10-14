import { clsx, type ClassValue } from 'clsx'

/** Join conditional class names (thin wrapper over clsx). */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}
