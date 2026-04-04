# Tailwind Component Patterns

## Button Variants

```tsx
{/* Primary Button */}
<button
  type="submit"
  className="
    bg-blue-600 hover:bg-blue-700 active:bg-blue-800
    text-white font-semibold
    px-4 py-2 rounded-md
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
    transition-colors duration-200
  "
>
  Create
</button>

{/* Secondary Button (Link) */}
<Link
  href="/back"
  className="
    bg-gray-100 hover:bg-gray-200 active:bg-gray-300
    text-gray-700 font-semibold
    px-4 py-2 rounded-md border border-gray-300
    focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
    transition-colors duration-200
  "
>
  Cancel
</Link>

{/* Danger Button */}
<button
  type="button"
  onClick={() => { if (confirm('Are you sure?')) destroy(`/items/${id}`) }}
  className="
    bg-red-600 hover:bg-red-700 active:bg-red-800
    text-white font-semibold
    px-4 py-2 rounded-md
    focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
    transition-colors duration-200
  "
>
  Delete
</button>

{/* Icon Button */}
<button
  type="button"
  aria-label="Close"
  className="
    p-2 rounded-full
    text-gray-400 hover:text-gray-600 hover:bg-gray-100
    focus:outline-none focus:ring-2 focus:ring-gray-500
    transition-colors duration-200
  "
>
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
  </svg>
</button>
```

## Form Fields

```tsx
{/* Text Input */}
<div className="space-y-1">
  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
  <input
    id="name"
    type="text"
    value={data.name}
    onChange={(e) => setData('name', e.target.value)}
    className="
      w-full px-3 py-2 rounded-md
      border border-gray-300
      focus:border-blue-500 focus:ring-2 focus:ring-blue-500
      placeholder:text-gray-400
      transition-colors duration-200
    "
    placeholder="Enter name..."
  />
</div>

{/* Select Dropdown */}
<div className="space-y-1">
  <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
  <select
    id="status"
    value={data.status}
    onChange={(e) => setData('status', e.target.value)}
    className="
      w-full px-3 py-2 rounded-md
      border border-gray-300
      focus:border-blue-500 focus:ring-2 focus:ring-blue-500
      transition-colors duration-200
    "
  >
    <option value="">Select status</option>
    <option value="active">Active</option>
    <option value="inactive">Inactive</option>
  </select>
</div>

{/* Textarea */}
<div className="space-y-1">
  <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
  <textarea
    id="description"
    rows={4}
    value={data.description}
    onChange={(e) => setData('description', e.target.value)}
    className="
      w-full px-3 py-2 rounded-md
      border border-gray-300
      focus:border-blue-500 focus:ring-2 focus:ring-blue-500
      placeholder:text-gray-400
      transition-colors duration-200
    "
    placeholder="Enter description..."
  />
</div>

{/* Checkbox */}
<div className="flex items-center gap-2">
  <input
    id="terms"
    type="checkbox"
    checked={data.terms}
    onChange={(e) => setData('terms', e.target.checked)}
    className="
      w-4 h-4 rounded
      text-blue-600 border-gray-300
      focus:ring-2 focus:ring-blue-500
    "
  />
  <label htmlFor="terms" className="text-sm text-gray-700">
    I agree to the terms and conditions
  </label>
</div>
```

## Cards

```tsx
{/* Basic Card */}
<div className="bg-white rounded-lg shadow-md p-6">
  <h3 className="text-xl font-semibold text-gray-800 mb-2">Card Title</h3>
  <p className="text-gray-600">Card content goes here.</p>
</div>

{/* Card with Header and Footer */}
<div className="bg-white rounded-lg shadow-md overflow-hidden">
  <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
    <h3 className="text-lg font-semibold text-gray-800">Card Header</h3>
  </div>

  <div className="p-6">
    <p className="text-gray-600">Card body content.</p>
  </div>

  <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
    <Link href="#" className="text-gray-600 hover:text-gray-800">Cancel</Link>
    <Link href="#" className="text-blue-600 hover:text-blue-800 font-semibold">Save</Link>
  </div>
</div>

{/* Hoverable Card (e.g., for lists) */}
<Link href={`/items/${item.id}`} className="block">
  <div className="
    bg-white rounded-lg shadow-md p-6
    hover:shadow-xl hover:-translate-y-1
    transition-all duration-300
  ">
    <h3 className="text-xl font-semibold text-gray-800 mb-2">{item.title}</h3>
    <p className="text-gray-600">{item.description}</p>
  </div>
</Link>
```

## Alerts and Notifications

```tsx
{/* Success Alert */}
<div className="bg-green-50 border border-green-200 rounded-md p-4" role="alert">
  <div className="flex gap-3">
    <div className="flex-shrink-0">
      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
      </svg>
    </div>
    <div>
      <h4 className="text-sm font-medium text-green-800">Success!</h4>
      <p className="text-sm text-green-700 mt-1">Your changes have been saved.</p>
    </div>
  </div>
</div>

{/* Error Alert */}
<div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
  <div className="flex gap-3">
    <div className="flex-shrink-0">
      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
      </svg>
    </div>
    <div>
      <h4 className="text-sm font-medium text-red-800">Error</h4>
      <p className="text-sm text-red-700 mt-1">Something went wrong. Please try again.</p>
    </div>
  </div>
</div>

{/* Dismissible Alert */}
function DismissibleAlert({ message }: { message: string }) {
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-md p-4" role="alert">
      <div className="flex justify-between gap-3">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="text-sm text-blue-700">{message}</p>
        </div>
        <button
          onClick={() => setVisible(false)}
          aria-label="Dismiss"
          className="
            flex-shrink-0 text-blue-400 hover:text-blue-600
            focus:outline-none focus:ring-2 focus:ring-blue-500 rounded
          "
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    </div>
  )
}
```

## Badges

```tsx
{/* Status Badges */}
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
  Active
</span>

<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
  Inactive
</span>

<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
  Deleted
</span>

<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
  Pending
</span>
```

## Loading States

```tsx
{/* Spinner */}
<div className="flex items-center justify-center p-4">
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
</div>

{/* Skeleton Loader */}
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
</div>

{/* Button with Loading State */}
<button
  type="submit"
  disabled={processing}
  className="btn-primary flex items-center gap-2"
>
  {processing && (
    <svg
      className="animate-spin h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  )}
  {processing ? 'Saving...' : 'Save'}
</button>
```

## Performance: Extract Repeated Patterns

```tsx
// app/frontend/components/ui/Button.tsx
interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary'
  href?: string
  onClick?: () => void
  type?: 'button' | 'submit'
  className?: string
}

function buttonClasses(variant: string) {
  const base = 'font-semibold py-2 px-4 rounded-lg transition-colors'
  switch (variant) {
    case 'primary':
      return `${base} bg-blue-600 hover:bg-blue-700 text-white`
    case 'secondary':
      return `${base} bg-gray-100 hover:bg-gray-200 text-gray-700`
    default:
      return base
  }
}

export default function Button({ children, variant = 'primary', href, onClick, type = 'button', className = '' }: ButtonProps) {
  const classes = `${buttonClasses(variant)} ${className}`

  if (href) {
    return <Link href={href} className={classes}>{children}</Link>
  }

  return <button type={type} onClick={onClick} className={classes}>{children}</button>
}

// Usage
<Button href="/path">Action</Button>
<Button href="/path2" variant="secondary">Cancel</Button>
```

## Custom Utilities (use sparingly)

```css
/* app/assets/tailwind/application.css */
@import "tailwindcss";

/* Only add custom utilities when absolutely necessary */
@utility btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md transition-colors;
}

@utility input-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:border-blue-500 focus:ring-2 focus:ring-blue-500;
}
```

## Real-World: Restaurant Card Component

```tsx
// app/frontend/components/RestaurantCard.tsx
import { Link } from '@inertiajs/react'

interface RestaurantCardProps {
  restaurant: {
    id: number
    name: string
    description: string | null
    rating: number
  }
  className?: string
}

export default function RestaurantCard({ restaurant, className = '' }: RestaurantCardProps) {
  return (
    <div className={className}>
      <Link href={`/restaurants/${restaurant.id}`} className="block">
        <div className="mb-3">
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {restaurant.name}
          </h3>

          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg font-semibold">
              {'*'.repeat(Math.round(restaurant.rating))}
            </span>
            <span className="text-gray-600 text-sm">
              {restaurant.rating.toFixed(1)}
            </span>
          </div>
        </div>

        {restaurant.description && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {restaurant.description.length > 150
              ? `${restaurant.description.slice(0, 150)}...`
              : restaurant.description}
          </p>
        )}
      </Link>
    </div>
  )
}
```

## Real-World: Index Page with Responsive Grid

```tsx
// app/frontend/pages/Restaurants/Index.tsx
import { Head, Link, usePage } from '@inertiajs/react'
import RestaurantCard from '@/components/RestaurantCard'

interface Props {
  restaurants: Restaurant[]
}

export default function Index({ restaurants }: Props) {
  const { current_user } = usePage().props as { current_user: { id: number } | null }

  return (
    <>
      <Head title="Restaurants" />

      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Restaurants</h1>

          {current_user && (
            <Link
              href="/restaurants/new"
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Add Restaurant
            </Link>
          )}
        </div>

        {restaurants.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {restaurants.map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">No restaurants found.</p>
          </div>
        )}
      </div>
    </>
  )
}
```
