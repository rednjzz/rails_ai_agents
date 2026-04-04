# React Testing

## Vitest Setup with vite_rails

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import ViteRails from 'vite-plugin-rails'

export default defineConfig({
  plugins: [
    react(),
    ViteRails(),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./app/frontend/test/setup.ts'],
    include: ['app/frontend/**/*.{test,spec}.{ts,tsx}'],
  },
  resolve: {
    alias: {
      '@': '/app/frontend',
    },
  },
})
```

```ts
// app/frontend/test/setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

## React Testing Library Patterns

### Basic Component Testing

```tsx
// app/frontend/components/ui/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import Button from './Button'

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<Button onClick={handleClick}>Click me</Button>)
    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('is disabled when loading', () => {
    render(<Button loading>Save</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('applies variant classes', () => {
    render(<Button variant="danger">Delete</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-red-600')
  })

  it('does not call onClick when disabled', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<Button disabled onClick={handleClick}>Click me</Button>)
    await user.click(screen.getByRole('button'))

    expect(handleClick).not.toHaveBeenCalled()
  })
})
```

### Testing Form Interactions

```tsx
// app/frontend/components/ui/FormInput.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import FormInput from './FormInput'

describe('FormInput', () => {
  it('renders label and input', () => {
    render(<FormInput label="Email" type="email" />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('accepts user input', async () => {
    const user = userEvent.setup()
    render(<FormInput label="Email" type="email" />)

    const input = screen.getByLabelText('Email')
    await user.type(input, 'test@example.com')

    expect(input).toHaveValue('test@example.com')
  })

  it('displays error message', () => {
    render(<FormInput label="Email" error="is required" />)

    expect(screen.getByRole('alert')).toHaveTextContent('is required')
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
  })

  it('does not display error when none provided', () => {
    render(<FormInput label="Email" />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
```

## Testing Components with Inertia Hooks

### Mocking useForm

```tsx
// app/frontend/pages/Users/New.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import New from './New'

// Mock the Inertia useForm hook
const mockPost = vi.fn()
const mockSetData = vi.fn()
const mockReset = vi.fn()

vi.mock('@inertiajs/react', () => ({
  useForm: () => ({
    data: { name: '', email: '' },
    setData: mockSetData,
    post: mockPost,
    processing: false,
    errors: {},
    reset: mockReset,
  }),
  Head: ({ children, title }: { children?: React.ReactNode; title?: string }) => (
    <>{children || title}</>
  ),
}))

describe('Users/New', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form', () => {
    render(<New />)

    expect(screen.getByLabelText('Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
  })

  it('calls setData when inputs change', async () => {
    const user = userEvent.setup()
    render(<New />)

    await user.type(screen.getByLabelText('Name'), 'Jane')

    expect(mockSetData).toHaveBeenCalled()
  })

  it('submits the form via post', async () => {
    const user = userEvent.setup()
    render(<New />)

    await user.click(screen.getByRole('button', { name: /create/i }))

    expect(mockPost).toHaveBeenCalledWith('/users')
  })
})
```

### Mocking useForm with Errors

```tsx
vi.mock('@inertiajs/react', () => ({
  useForm: () => ({
    data: { name: '', email: '' },
    setData: vi.fn(),
    post: vi.fn(),
    processing: false,
    errors: { name: "can't be blank", email: 'is invalid' },
    reset: vi.fn(),
  }),
  Head: ({ title }: { title?: string }) => <>{title}</>,
}))

describe('Users/New with errors', () => {
  it('displays validation errors', () => {
    render(<New />)

    expect(screen.getByText("can't be blank")).toBeInTheDocument()
    expect(screen.getByText('is invalid')).toBeInTheDocument()
  })
})
```

### Mocking usePage

```tsx
// app/frontend/layouts/AppLayout.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import AppLayout from './AppLayout'

vi.mock('@inertiajs/react', () => ({
  usePage: () => ({
    props: {
      current_user: { id: 1, name: 'John Doe', email: 'john@example.com' },
      flash: { notice: null, alert: null },
    },
  }),
  Link: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}))

describe('AppLayout', () => {
  it('displays the current user name', () => {
    render(<AppLayout><div>Page content</div></AppLayout>)

    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })

  it('renders children', () => {
    render(<AppLayout><div>Page content</div></AppLayout>)

    expect(screen.getByText('Page content')).toBeInTheDocument()
  })
})
```

### Testing with Flash Messages

```tsx
vi.mock('@inertiajs/react', () => ({
  usePage: () => ({
    props: {
      current_user: { id: 1, name: 'John' },
      flash: { notice: 'User created successfully.', alert: null },
    },
  }),
  Link: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}))

describe('AppLayout with flash', () => {
  it('displays flash notice', () => {
    render(<AppLayout><div /></AppLayout>)

    expect(screen.getByText('User created successfully.')).toBeInTheDocument()
  })
})
```

## Testing Custom Hooks with renderHook

```tsx
// app/frontend/hooks/useDebounce.test.ts
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500))
    expect(result.current).toBe('hello')
  })

  it('debounces value updates', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    )

    // Update the value
    rerender({ value: 'world', delay: 500 })

    // Value should not have changed yet
    expect(result.current).toBe('hello')

    // Fast forward time
    act(() => {
      vi.advanceTimersByTime(500)
    })

    // Now it should be updated
    expect(result.current).toBe('world')
  })

  it('cancels previous timeout on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 500 } }
    )

    rerender({ value: 'ab', delay: 500 })
    act(() => { vi.advanceTimersByTime(200) })

    rerender({ value: 'abc', delay: 500 })
    act(() => { vi.advanceTimersByTime(200) })

    // Still the initial value because neither timeout completed
    expect(result.current).toBe('a')

    act(() => { vi.advanceTimersByTime(300) })

    // Now the last value should be set
    expect(result.current).toBe('abc')
  })
})
```

## Mocking Inertia Router for Navigation Tests

```tsx
// app/frontend/components/NavigationMenu.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import NavigationMenu from './NavigationMenu'

const mockVisit = vi.fn()

vi.mock('@inertiajs/react', () => ({
  router: {
    visit: (...args: unknown[]) => mockVisit(...args),
    post: vi.fn(),
    delete: vi.fn(),
  },
  Link: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>{children}</a>
  ),
  usePage: () => ({
    props: { current_user: { id: 1, name: 'John' } },
    url: '/dashboard',
  }),
}))

describe('NavigationMenu', () => {
  it('renders navigation links', () => {
    render(<NavigationMenu />)

    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard')
    expect(screen.getByRole('link', { name: 'Users' })).toHaveAttribute('href', '/users')
  })

  it('navigates via router on logout', async () => {
    const user = userEvent.setup()
    render(<NavigationMenu />)

    await user.click(screen.getByRole('button', { name: /log out/i }))

    expect(mockVisit).toHaveBeenCalledWith('/logout', expect.objectContaining({ method: 'delete' }))
  })
})
```

## Running Tests

```bash
# Run all frontend tests
npx vitest run

# Run in watch mode
npx vitest

# Run a specific test file
npx vitest run app/frontend/components/ui/Button.test.tsx

# Run tests matching a pattern
npx vitest run --grep "Button"

# With coverage
npx vitest run --coverage
```
