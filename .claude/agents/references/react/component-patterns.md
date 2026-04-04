# React Component Patterns

## Functional Component with TypeScript Props Interface

```tsx
// app/frontend/components/UserProfile.tsx
interface UserProfileProps {
  user: {
    id: number
    name: string
    email: string
    avatar_url: string | null
  }
  editable?: boolean
  onEdit?: () => void
}

export default function UserProfile({ user, editable = false, onEdit }: UserProfileProps) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
      {user.avatar_url ? (
        <img
          src={user.avatar_url}
          alt={`${user.name}'s avatar`}
          className="w-12 h-12 rounded-full object-cover"
        />
      ) : (
        <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
          <span className="text-gray-500 text-lg font-semibold">
            {user.name.charAt(0).toUpperCase()}
          </span>
        </div>
      )}

      <div>
        <h3 className="font-semibold text-gray-900">{user.name}</h3>
        <p className="text-sm text-gray-500">{user.email}</p>
      </div>

      {editable && (
        <button onClick={onEdit} className="ml-auto text-blue-600 hover:text-blue-800">
          Edit
        </button>
      )}
    </div>
  )
}
```

## Reusable UI Components

### Button

```tsx
// app/frontend/components/ui/Button.tsx (React 19 — ref as prop, no forwardRef)

type ButtonVariant = 'primary' | 'secondary' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  ref?: React.Ref<HTMLButtonElement>
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white',
  secondary: 'bg-gray-100 hover:bg-gray-200 active:bg-gray-300 text-gray-700 border border-gray-300',
  danger: 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
}

export default function Button({
  ref,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        font-semibold rounded-md
        focus:outline-none focus:ring-2 focus:ring-offset-2
        transition-colors duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  )
}
```

### Card

```tsx
// app/frontend/components/ui/Card.tsx
interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-md overflow-hidden ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-gray-50 px-6 py-4 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  )
}

export function CardBody({ children, className = '' }: CardProps) {
  return <div className={`p-6 ${className}`}>{children}</div>
}

export function CardFooter({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3 ${className}`}>
      {children}
    </div>
  )
}
```

### Modal

```tsx
// app/frontend/components/ui/Modal.tsx
import { useEffect, useRef } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

export default function Modal({ open, onClose, title, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (open) {
      dialog.showModal()
    } else {
      dialog.close()
    }
  }, [open])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!open) return null

  return (
    <dialog
      ref={dialogRef}
      className="
        fixed inset-0 z-50
        bg-transparent backdrop:bg-black/50
        p-0 m-auto
        rounded-lg shadow-xl
        max-w-lg w-full
      "
      onClose={onClose}
    >
      <div className="bg-white rounded-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <div className="px-6 py-4">{children}</div>
      </div>
    </dialog>
  )
}
```

### Form Input

```tsx
// app/frontend/components/ui/FormInput.tsx (React 19 — ref as prop, no forwardRef)

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  ref?: React.Ref<HTMLInputElement>
  label: string
  error?: string
}

export default function FormInput({ ref, label, error, id, className = '', ...props }: FormInputProps) {
  const inputId = id || label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        className={`
          w-full px-3 py-2 rounded-md
          border ${error ? 'border-red-500' : 'border-gray-300'}
          focus:border-blue-500 focus:ring-2 focus:ring-blue-500
          placeholder:text-gray-400
          transition-colors duration-200
          ${className}
        `}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-red-600 text-sm" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
```

## Custom Hooks

### useDebounce

```tsx
// app/frontend/hooks/useDebounce.ts
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}
```

### useActionCable

```tsx
// app/frontend/hooks/useActionCable.ts
import { useEffect, useRef } from 'react'
import { createConsumer } from '@rails/actioncable'

interface UseActionCableOptions {
  channel: string
  params?: Record<string, unknown>
  onReceived: (data: unknown) => void
  onConnected?: () => void
  onDisconnected?: () => void
}

export function useActionCable({
  channel,
  params = {},
  onReceived,
  onConnected,
  onDisconnected,
}: UseActionCableOptions) {
  const subscriptionRef = useRef<ReturnType<ReturnType<typeof createConsumer>['subscriptions']['create']> | null>(null)

  useEffect(() => {
    const consumer = createConsumer()

    subscriptionRef.current = consumer.subscriptions.create(
      { channel, ...params },
      {
        received: onReceived,
        connected: onConnected,
        disconnected: onDisconnected,
      }
    )

    return () => {
      subscriptionRef.current?.unsubscribe()
    }
  }, [channel, JSON.stringify(params)])

  return subscriptionRef
}
```

### useClickOutside

```tsx
// app/frontend/hooks/useClickOutside.ts
import { useEffect, useRef } from 'react'

export function useClickOutside<T extends HTMLElement>(
  handler: () => void
): React.RefObject<T | null> {
  const ref = useRef<T | null>(null)

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler()
      }
    }

    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [handler])

  return ref
}
```

## Component Composition Patterns

### Children Pattern

```tsx
interface PanelProps {
  title: string
  children: React.ReactNode
}

function Panel({ title, children }: PanelProps) {
  return (
    <section className="border border-gray-200 rounded-lg">
      <h2 className="px-4 py-3 bg-gray-50 font-semibold border-b border-gray-200">
        {title}
      </h2>
      <div className="p-4">{children}</div>
    </section>
  )
}

// Usage
<Panel title="User Details">
  <UserProfile user={user} />
</Panel>
```

### Render Props

```tsx
interface DataLoaderProps<T> {
  url: string
  children: (data: T, loading: boolean) => React.ReactNode
}

function DataLoader<T>({ url, children }: DataLoaderProps<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(url)
      .then((res) => res.json())
      .then((json) => { setData(json); setLoading(false) })
  }, [url])

  return <>{data !== null ? children(data, loading) : <Spinner />}</>
}

// Usage
<DataLoader<User[]> url="/api/users">
  {(users, loading) => loading ? <Spinner /> : <UserList users={users} />}
</DataLoader>
```

### Compound Components

```tsx
// React 19 — use() instead of useContext()
import { createContext, use, useState } from 'react'

interface TabsContextType {
  activeTab: string
  setActiveTab: (tab: string) => void
}

const TabsContext = createContext<TabsContextType | null>(null)

function useTabs() {
  const context = use(TabsContext)
  if (!context) throw new Error('Tabs compound components must be used within <Tabs>')
  return context
}

function Tabs({ defaultTab, children }: { defaultTab: string; children: React.ReactNode }) {
  const [activeTab, setActiveTab] = useState(defaultTab)

  return (
    <TabsContext value={{ activeTab, setActiveTab }}>
      <div>{children}</div>
    </TabsContext>
  )
}

function TabList({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex border-b border-gray-200" role="tablist">
      {children}
    </div>
  )
}

function Tab({ value, children }: { value: string; children: React.ReactNode }) {
  const { activeTab, setActiveTab } = useTabs()
  const isActive = activeTab === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => setActiveTab(value)}
      className={`px-4 py-2 font-medium ${
        isActive
          ? 'border-b-2 border-blue-600 text-blue-600'
          : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      {children}
    </button>
  )
}

function TabPanel({ value, children }: { value: string; children: React.ReactNode }) {
  const { activeTab } = useTabs()
  if (activeTab !== value) return null

  return (
    <div role="tabpanel" className="py-4">
      {children}
    </div>
  )
}

Tabs.List = TabList
Tabs.Tab = Tab
Tabs.Panel = TabPanel

export default Tabs

// Usage
<Tabs defaultTab="profile">
  <Tabs.List>
    <Tabs.Tab value="profile">Profile</Tabs.Tab>
    <Tabs.Tab value="settings">Settings</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="profile"><ProfileForm user={user} /></Tabs.Panel>
  <Tabs.Panel value="settings"><SettingsForm user={user} /></Tabs.Panel>
</Tabs>
```

## Accessibility Patterns

```tsx
// ARIA attributes and keyboard navigation
interface DropdownMenuProps {
  label: string
  items: { label: string; onClick: () => void }[]
}

function DropdownMenu({ label, items }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useClickOutside<HTMLDivElement>(() => setIsOpen(false))
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([])

  function handleKeyDown(e: React.KeyboardEvent) {
    const currentIndex = itemRefs.current.findIndex((el) => el === document.activeElement)

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        if (!isOpen) {
          setIsOpen(true)
        } else {
          const nextIndex = Math.min(currentIndex + 1, items.length - 1)
          itemRefs.current[nextIndex]?.focus()
        }
        break
      case 'ArrowUp':
        e.preventDefault()
        const prevIndex = Math.max(currentIndex - 1, 0)
        itemRefs.current[prevIndex]?.focus()
        break
      case 'Escape':
        setIsOpen(false)
        break
    }
  }

  return (
    <div ref={menuRef} className="relative" onKeyDown={handleKeyDown}>
      <button
        aria-haspopup="true"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-white border border-gray-300 rounded-md"
      >
        {label}
      </button>

      {isOpen && (
        <div role="menu" className="absolute mt-1 bg-white border border-gray-200 rounded-md shadow-lg">
          {items.map((item, index) => (
            <button
              key={item.label}
              ref={(el) => { itemRefs.current[index] = el }}
              role="menuitem"
              tabIndex={-1}
              onClick={() => { item.onClick(); setIsOpen(false) }}
              className="block w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

## Directory Organization

```
app/frontend/
  pages/                    # Inertia page components (one per route)
    Users/
      Index.tsx
      Show.tsx
      New.tsx
      Edit.tsx
    Dashboard/
      Show.tsx
  components/               # Shared reusable components
    ui/                     # Primitive UI components
      Button.tsx
      Card.tsx
      Modal.tsx
      FormInput.tsx
      Select.tsx
      Badge.tsx
    UserProfile.tsx         # Domain-specific shared components
    RestaurantCard.tsx
  layouts/                  # Persistent layout components
    AppLayout.tsx
    AuthLayout.tsx
    SettingsLayout.tsx
  hooks/                    # Custom React hooks
    useDebounce.ts
    useActionCable.ts
    useClickOutside.ts
  types/                    # Shared TypeScript interfaces
    index.ts                # Re-exports all types
    user.ts
    restaurant.ts
  lib/                      # Utilities and helpers
    formatDate.ts
    classNames.ts
```
