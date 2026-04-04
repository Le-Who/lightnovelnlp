// @vitest-environment jsdom
/**
 * Unit tests — Button UI component.
 *
 * Level: Unit (JSDOM, no API calls, no router).
 * Covers:
 *   - Button renders its label text as an accessible button role.
 *   - Button applies the 'bg-destructive' class for the 'destructive' variant.
 *
 * AAA applied: Arrange (component props) → Act (render) → Assert (query+expect).
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Button } from '../../components/ui/Button'

describe('Button', () => {
  it('renders its label as an accessible button element', () => {
    // Arrange
    const label = 'Click me'

    // Act
    render(<Button>{label}</Button>)

    // Assert
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('applies destructive variant CSS class for destructive variant', () => {
    // Arrange
    const variant = 'destructive'
    const label = 'Delete'

    // Act
    render(<Button variant={variant}>{label}</Button>)
    const button = screen.getByRole('button', { name: /delete/i })

    // Assert
    expect(button).toHaveClass('bg-destructive')
  })
})
