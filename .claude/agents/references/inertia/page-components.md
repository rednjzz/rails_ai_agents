# Inertia.js Page Components

## Controller Rendering

```ruby
# app/controllers/users_controller.rb
class UsersController < ApplicationController
  def index
    users = User.all.order(created_at: :desc)
    authorize users

    render inertia: 'Users/Index', props: {
      users: users.map { |u| UserPresenter.new(u).to_props }
    }
  end

  def show
    user = User.find(params[:id])
    authorize user

    render inertia: 'Users/Show', props: {
      user: UserPresenter.new(user).to_props
    }
  end

  def edit
    user = User.find(params[:id])
    authorize user

    render inertia: 'Users/Edit', props: {
      user: UserPresenter.new(user).to_props
    }
  end
end
```

## Page Component TypeScript Structure

```tsx
// app/frontend/pages/Users/Index.tsx
import { Head, Link } from '@inertiajs/react'

interface User {
  id: number
  name: string
  email: string
  created_at: string
}

interface Props {
  users: User[]
}

export default function Index({ users }: Props) {
  return (
    <>
      <Head title="Users" />

      <h1 className="text-2xl font-bold mb-6">Users</h1>

      <ul className="space-y-4">
        {users.map((user) => (
          <li key={user.id}>
            <Link href={`/users/${user.id}`} className="text-blue-600 hover:underline">
              {user.name}
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}
```

## Shared Data via InertiaRails.share

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  include Pundit::Authorization

  inertia_share do
    {
      current_user: current_user ? UserPresenter.new(current_user).to_props : nil,
      flash: {
        notice: flash[:notice],
        alert: flash[:alert]
      }
    }
  end
end
```

Accessing shared data in components:

```tsx
import { usePage } from '@inertiajs/react'

interface SharedProps {
  current_user: { id: number; name: string; email: string } | null
  flash: { notice: string | null; alert: string | null }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { current_user, flash } = usePage<{ props: SharedProps }>().props

  return (
    <div>
      {flash.notice && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4" role="alert">
          {flash.notice}
        </div>
      )}
      {flash.alert && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
          {flash.alert}
        </div>
      )}

      {current_user ? (
        <nav>Logged in as {current_user.name}</nav>
      ) : (
        <nav><Link href="/login">Sign in</Link></nav>
      )}

      <main>{children}</main>
    </div>
  )
}
```

## Lazy Loading Props

```ruby
# app/controllers/users_controller.rb
def show
  user = User.find(params[:id])
  authorize user

  render inertia: 'Users/Show', props: {
    user: UserPresenter.new(user).to_props,
    # Lazy props are only loaded when the component requests them
    activity_log: InertiaRails.lazy { ActivityLog.for_user(user).recent.as_json }
  }
end
```

## Deferred Props

```ruby
# app/controllers/dashboard_controller.rb
def show
  render inertia: 'Dashboard/Show', props: {
    # Loaded immediately
    user: UserPresenter.new(current_user).to_props,
    # Deferred: loaded in a separate request after page render
    stats: InertiaRails.defer { DashboardStatsQuery.new(current_user).call },
    notifications: InertiaRails.defer { current_user.notifications.unread.as_json }
  }
end
```

Using deferred props in the component:

```tsx
import { Deferred } from '@inertiajs/react'

interface Props {
  user: User
  stats?: DashboardStats
  notifications?: Notification[]
}

export default function Show({ user, stats, notifications }: Props) {
  return (
    <>
      <Head title="Dashboard" />
      <h1>Welcome, {user.name}</h1>

      <Deferred data="stats" fallback={<SkeletonLoader />}>
        <StatsPanel stats={stats!} />
      </Deferred>

      <Deferred data="notifications" fallback={<Spinner />}>
        <NotificationList notifications={notifications!} />
      </Deferred>
    </>
  )
}
```

## Persistent Layouts

```tsx
// app/frontend/pages/Users/Index.tsx
import Layout from '@/layouts/AppLayout'

function Index({ users }: Props) {
  return (
    <>
      <Head title="Users" />
      <h1>Users</h1>
      {/* page content */}
    </>
  )
}

// Persistent layout -- not remounted between page visits
Index.layout = (page: React.ReactNode) => <Layout>{page}</Layout>

export default Index
```

Nested persistent layouts:

```tsx
import AppLayout from '@/layouts/AppLayout'
import SettingsLayout from '@/layouts/SettingsLayout'

function ProfileSettings({ user }: Props) {
  return (
    <>
      <Head title="Profile Settings" />
      {/* settings content */}
    </>
  )
}

ProfileSettings.layout = (page: React.ReactNode) => (
  <AppLayout>
    <SettingsLayout>{page}</SettingsLayout>
  </AppLayout>
)

export default ProfileSettings
```

## Scroll Management and preserveState

```tsx
import { router, Link } from '@inertiajs/react'

// Preserve scroll position on page visit
router.visit('/users', { preserveScroll: true })

// Preserve component state (e.g., form input values) on page visit
router.visit('/users?page=2', { preserveState: true })

// Link component with scroll and state preservation
<Link href="/users?page=2" preserveScroll preserveState>
  Next Page
</Link>

// Reset scroll only for specific elements
router.visit('/users', {
  preserveScroll: (page) => page.url.includes('page=')
})
```

## Head Management

```tsx
import { Head } from '@inertiajs/react'

export default function Show({ user }: Props) {
  return (
    <>
      <Head>
        <title>{user.name} - My App</title>
        <meta name="description" content={`Profile for ${user.name}`} />
        <meta property="og:title" content={user.name} />
        <meta property="og:image" content={user.avatar_url} />
      </Head>

      <h1>{user.name}</h1>
    </>
  )
}

// Simple title-only usage
<Head title={`${user.name} - My App`} />
```
