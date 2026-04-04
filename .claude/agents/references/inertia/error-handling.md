# Inertia.js Error Handling and Serialization

## Inertia Error Bag Format

Inertia.js expects errors as a flat hash of `{ field_name: "message" }`. The `useForm` hook
automatically populates its `errors` object from this format. All error sources must be
normalized to this shape before passing to Inertia.

```ruby
# Target format -- flat hash, string keys or symbol keys, single message per field
{ name: "can't be blank", email: "has already been taken" }
```

## Converting Error Sources

### ActiveModel::Errors to Inertia Errors

ActiveModel stores multiple messages per field. Inertia expects one string per field.
Use `.messages` and take the first error for each field.

```ruby
# user.errors.messages
# => { name: ["can't be blank", "is too short"], email: ["is invalid"] }

# Convert to Inertia format (first error per field)
user.errors.messages.transform_values(&:first)
# => { name: "can't be blank", email: "is invalid" }
```

For full messages joined per field:

```ruby
user.errors.messages.transform_values { |msgs| msgs.join(", ") }
# => { name: "can't be blank, is too short", email: "is invalid" }
```

### Service Result Errors to Inertia Errors

Services return Result objects. The `error` field can be a string (general error)
or an ActiveModel::Errors object (field-level errors).

**When the service returns a string error:**

```ruby
# Service returns: failure("User not authorized")
# Map to a :base key or flash alert

if result.failure?
  redirect_back fallback_location: fallback_path,
                inertia: { errors: { base: result.error } }
end
```

**When the service returns an ActiveModel::Errors object:**

```ruby
# Service returns: failure(entity.errors)
# Convert using .messages

if result.failure?
  errors = result.error.messages.transform_values(&:first)
  redirect_back fallback_location: fallback_path,
                inertia: { errors: errors }
end
```

**Recommended: normalize in the service itself:**

```ruby
# app/services/entities/create_service.rb
module Entities
  class CreateService < ApplicationService
    def initialize(user:, params:)
      @user = user
      @params = params
    end

    def call
      return failure("User not authorized") unless @user.present?

      entity = @user.entities.build(@params)

      if entity.save
        success(entity)
      else
        # Return the errors object so the controller can serialize it
        failure(entity.errors)
      end
    end
  end
end
```

### Form Object Errors to Inertia Errors

Form objects that include `ActiveModel::Validations` produce `ActiveModel::Errors`,
so the same conversion applies.

```ruby
# app/forms/entity_registration_form.rb
class EntityRegistrationForm
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :name, :string
  attribute :email, :string
  attribute :company_name, :string

  validates :name, :email, :company_name, presence: true
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }
end
```

```ruby
# In the controller
form = EntityRegistrationForm.new(form_params)

unless form.valid?
  errors = form.errors.messages.transform_values(&:first)
  redirect_back fallback_location: new_registration_path,
                inertia: { errors: errors }
  return
end

result = Registrations::CreateService.call(form: form, user: current_user)
# ...
```

## Standard Controller Error Handling Pattern

### With redirect_back (POST/PATCH/DELETE)

Use `redirect_back` with `inertia: { errors: ... }` after failed form submissions.
Inertia automatically shares these errors back to the originating page component.

```ruby
class EntitiesController < ApplicationController
  def create
    authorize Entity
    result = Entities::CreateService.call(user: current_user, params: entity_params)

    if result.success?
      redirect_to result.data, notice: "Entity created successfully."
    else
      redirect_back_with_errors(result, fallback: new_entity_path)
    end
  end

  def update
    authorize @entity
    result = Entities::UpdateService.call(entity: @entity, params: entity_params)

    if result.success?
      redirect_to result.data, notice: "Entity updated successfully."
    else
      redirect_back_with_errors(result, fallback: edit_entity_path(@entity))
    end
  end

  private

  def redirect_back_with_errors(result, fallback:)
    errors = normalize_errors(result.error)
    redirect_back fallback_location: fallback,
                  inertia: { errors: errors }
  end

  def normalize_errors(error)
    case error
    when ActiveModel::Errors
      error.messages.transform_values(&:first)
    when Hash
      error.transform_values { |v| v.is_a?(Array) ? v.first : v }
    when String
      { base: error }
    else
      { base: error.to_s }
    end
  end
end
```

### With render inertia: (re-render the form page)

When you need to preserve form data without a redirect, render the page directly.
Pass errors as a prop.

```ruby
def create
  authorize Entity
  result = Entities::CreateService.call(user: current_user, params: entity_params)

  if result.success?
    redirect_to result.data, notice: "Entity created successfully."
  else
    render inertia: 'Entities/New', props: {
      entity: entity_params.to_h,
      errors: normalize_errors(result.error)
    }, status: :unprocessable_entity
  end
end
```

### Extracting to ApplicationController

If multiple controllers need error normalization, extract the helper.

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  private

  def normalize_errors(error)
    case error
    when ActiveModel::Errors
      error.messages.transform_values(&:first)
    when Hash
      error.transform_values { |v| v.is_a?(Array) ? v.first : v }
    when String
      { base: error }
    else
      { base: error.to_s }
    end
  end

  def redirect_back_with_errors(result, fallback:)
    errors = normalize_errors(result.error)
    redirect_back fallback_location: fallback,
                  inertia: { errors: errors }
  end
end
```

## React: Consuming Errors with useForm

### Field-Level Errors

`useForm().errors` is automatically populated from the Inertia error bag.

```tsx
import { useForm } from '@inertiajs/react'

export default function New() {
  const { data, setData, post, processing, errors } = useForm({
    name: '',
    email: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    post('/entities')
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Name</label>
        <input
          id="name"
          value={data.name}
          onChange={(e) => setData('name', e.target.value)}
          className={errors.name ? 'border-red-500' : 'border-gray-300'}
        />
        {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          className={errors.email ? 'border-red-500' : 'border-gray-300'}
        />
        {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
      </div>

      <button type="submit" disabled={processing}>
        {processing ? 'Creating...' : 'Create'}
      </button>
    </form>
  )
}
```

### Base (Non-Field) Errors

General errors not tied to a specific field use the `base` key.

```tsx
export default function New() {
  const { data, setData, post, processing, errors } = useForm({
    name: '',
    email: '',
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); post('/entities') }}>
      {errors.base && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {errors.base}
        </div>
      )}

      {/* field inputs... */}
    </form>
  )
}
```

### Reusable FormError Component

```tsx
// app/frontend/components/FormError.tsx
interface FormErrorProps {
  message?: string
}

export function FormError({ message }: FormErrorProps) {
  if (!message) return null
  return <p className="text-red-600 text-sm mt-1">{message}</p>
}

// Usage
<FormError message={errors.name} />
```

## Flash Messages via Shared Data

Flash messages are shared globally through `inertia_share` and displayed in the layout.

### Rails: Share Flash Data

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  inertia_share do
    {
      flash: {
        notice: flash[:notice],
        alert: flash[:alert]
      }
    }
  end
end
```

### React: Display Flash in Layout

```tsx
// app/frontend/layouts/AppLayout.tsx
import { usePage } from '@inertiajs/react'
import { useEffect, useState } from 'react'

interface SharedProps {
  flash: {
    notice?: string
    alert?: string
  }
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { flash } = usePage<{ props: SharedProps }>().props as unknown as SharedProps
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (flash.notice || flash.alert) {
      setVisible(true)
      const timer = setTimeout(() => setVisible(false), 5000)
      return () => clearTimeout(timer)
    }
  }, [flash])

  return (
    <div>
      {visible && flash.notice && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {flash.notice}
        </div>
      )}

      {visible && flash.alert && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {flash.alert}
        </div>
      )}

      <main>{children}</main>
    </div>
  )
}
```

### When to Use Flash vs Errors

| Scenario | Mechanism | Example |
|----------|-----------|---------|
| Validation failure (field-level) | `inertia: { errors: { ... } }` | "Name can't be blank" |
| Business logic failure (general) | `inertia: { errors: { base: "..." } }` | "Insufficient permissions" |
| Success notification | `flash[:notice]` via `redirect_to` | "Entity created successfully." |
| Destructive action warning | `flash[:alert]` via `redirect_to` | "Entity was deleted." |
| Server error (500) | Inertia error page | Custom error page component |
