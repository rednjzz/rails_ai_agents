# Authorization Props for Inertia.js

## Overview

Authorization is ALWAYS enforced server-side via Pundit. Frontend permissions are for **UI display only** -- hiding buttons, disabling actions. Never trust client-side permission checks for security.

## Controller Helper

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  include Pundit::Authorization

  private

  # Serialize Pundit permissions as props for Inertia
  def policy_props(record, actions: %i[edit update destroy])
    pol = policy(record)
    actions.each_with_object({}) do |action, hash|
      hash[:"can_#{action}"] = pol.public_send(:"#{action}?")
    end
  end
end
```

## Usage in Controllers

```ruby
class UsersController < ApplicationController
  def show
    user = User.find(params[:id])
    authorize user

    render inertia: 'Users/Show', props: {
      user: UserPresenter.new(user).to_props,
      permissions: policy_props(user, actions: %i[edit destroy])
      # => { can_edit: true, can_destroy: false }
    }
  end

  def index
    users = policy_scope(User).order(:name)
    authorize User

    render inertia: 'Users/Index', props: {
      users: users.map { |u|
        UserPresenter.new(u).to_props.merge(
          permissions: policy_props(u, actions: %i[edit destroy])
        )
      },
      can_create: policy(User).create?
    }
  end
end
```

## TypeScript Interfaces

```tsx
// app/frontend/types/shared.ts
interface Permissions {
  can_edit?: boolean
  can_update?: boolean
  can_destroy?: boolean
  [key: `can_${string}`]: boolean | undefined
}

interface UserWithPermissions extends User {
  permissions: Permissions
}
```

## React Component Usage

```tsx
// app/frontend/pages/Users/Show.tsx
import { Link, Head } from '@inertiajs/react'

interface Props {
  user: User
  permissions: {
    can_edit: boolean
    can_destroy: boolean
  }
}

export default function Show({ user, permissions }: Props) {
  return (
    <>
      <Head title={user.name} />
      <h1>{user.name}</h1>
      <p>{user.email}</p>

      {permissions.can_edit && (
        <Link href={`/users/${user.id}/edit`} className="btn-primary">
          Edit
        </Link>
      )}

      {permissions.can_destroy && (
        <DeleteButton userId={user.id} />
      )}
    </>
  )
}
```

## Index with Per-Record Permissions

```tsx
interface Props {
  users: (User & { permissions: { can_edit: boolean; can_destroy: boolean } })[]
  can_create: boolean
}

export default function Index({ users, can_create }: Props) {
  return (
    <>
      <Head title="Users" />

      {can_create && (
        <Link href="/users/new" className="btn-primary">New User</Link>
      )}

      <ul>
        {users.map((user) => (
          <li key={user.id}>
            {user.name}
            {user.permissions.can_edit && (
              <Link href={`/users/${user.id}/edit`}>Edit</Link>
            )}
          </li>
        ))}
      </ul>
    </>
  )
}
```

## Important Notes

- **Server-side is the source of truth.** Even if a user bypasses the UI, Pundit will deny unauthorized actions.
- Use `policy_props` only for actions the page actually needs. Don't serialize every possible permission.
- For shared permissions (e.g., admin status), use `inertia_share` in ApplicationController:

```ruby
inertia_share do
  {
    current_user: current_user && UserPresenter.new(current_user).to_props,
    is_admin: current_user&.admin? || false
  }
end
```
