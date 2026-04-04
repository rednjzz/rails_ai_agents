# Inertia.js Forms and Validation

## useForm Hook: Basic Usage

```tsx
import { useForm } from '@inertiajs/react'

interface UserFormData {
  name: string
  email: string
  role: string
}

export default function New() {
  const { data, setData, post, processing, errors, reset } = useForm<UserFormData>({
    name: '',
    email: '',
    role: 'member',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    post('/users')
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Name</label>
        <input
          id="name"
          type="text"
          value={data.name}
          onChange={(e) => setData('name', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
        {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
        {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
      </div>

      <button type="submit" disabled={processing}>
        {processing ? 'Creating...' : 'Create User'}
      </button>
    </form>
  )
}
```

## HTTP Methods: post, put, patch, delete

```tsx
// Create
const { post } = useForm({ name: '', email: '' })
post('/users')

// Update (full replacement)
const { put } = useForm({ name: 'Updated', email: 'new@example.com' })
put(`/users/${userId}`)

// Update (partial)
const { patch } = useForm({ name: 'Updated' })
patch(`/users/${userId}`)

// Delete (with confirmation)
const { delete: destroy } = useForm({})

function handleDelete() {
  if (confirm('Are you sure?')) {
    destroy(`/users/${userId}`)
  }
}
```

## Server-Side Validation Error Display

Rails controller returns validation errors automatically via Inertia:

```ruby
# app/controllers/users_controller.rb
def create
  authorize User

  result = Users::CreateService.call(
    user: current_user,
    params: user_params
  )

  if result.success?
    redirect_to result.data, notice: "User created successfully."
  else
    # Inertia shares errors back to the form automatically
    redirect_back fallback_location: new_user_path,
                  inertia: { errors: result.error.messages }
  end
end
```

Display errors in the component:

```tsx
interface Props {
  errors: Record<string, string>
}

export default function New({ errors }: Props) {
  const form = useForm({ name: '', email: '' })

  return (
    <form onSubmit={(e) => { e.preventDefault(); form.post('/users') }}>
      <div>
        <input
          value={form.data.name}
          onChange={(e) => form.setData('name', e.target.value)}
        />
        {form.errors.name && (
          <p className="text-red-600 text-sm mt-1">{form.errors.name}</p>
        )}
      </div>
    </form>
  )
}
```

## Form State: processing, isDirty, reset, clearErrors

```tsx
export default function Edit({ user }: Props) {
  const form = useForm({
    name: user.name,
    email: user.email,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    form.patch(`/users/${user.id}`, {
      onSuccess: () => form.reset(),
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}

      <div className="flex items-center gap-4">
        <button type="submit" disabled={form.processing}>
          {form.processing ? 'Saving...' : 'Save Changes'}
        </button>

        {form.isDirty && (
          <button type="button" onClick={() => form.reset()}>
            Discard Changes
          </button>
        )}

        <button type="button" onClick={() => form.clearErrors()}>
          Clear Errors
        </button>

        {/* Reset specific fields */}
        <button type="button" onClick={() => form.reset('name')}>
          Reset Name
        </button>
      </div>
    </form>
  )
}
```

## File Uploads with Progress

```tsx
export default function AvatarUpload({ user }: Props) {
  const form = useForm<{ avatar: File | null }>({
    avatar: null,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    form.post(`/users/${user.id}/avatar`, {
      forceFormData: true,
      onProgress: (progress) => {
        // progress.percentage is 0-100
        console.log(`Upload progress: ${progress.percentage}%`)
      },
      onSuccess: () => form.reset(),
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          if (e.target.files?.[0]) {
            form.setData('avatar', e.target.files[0])
          }
        }}
      />

      {form.progress && (
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${form.progress.percentage}%` }}
          />
        </div>
      )}

      <button type="submit" disabled={form.processing}>
        {form.processing ? 'Uploading...' : 'Upload Avatar'}
      </button>
    </form>
  )
}
```

## Multi-Step Form Pattern

```tsx
import { useForm } from '@inertiajs/react'
import { useState } from 'react'

interface RegistrationData {
  // Step 1
  name: string
  email: string
  // Step 2
  company: string
  role: string
  // Step 3
  plan: string
  agree_to_terms: boolean
}

export default function Registration() {
  const [step, setStep] = useState(1)

  const form = useForm<RegistrationData>({
    name: '',
    email: '',
    company: '',
    role: '',
    plan: 'free',
    agree_to_terms: false,
  })

  function nextStep() {
    setStep((s) => Math.min(s + 1, 3))
  }

  function prevStep() {
    setStep((s) => Math.max(s - 1, 1))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    form.post('/registrations')
  }

  return (
    <form onSubmit={handleSubmit}>
      {step === 1 && (
        <div>
          <h2>Personal Info</h2>
          <input
            value={form.data.name}
            onChange={(e) => form.setData('name', e.target.value)}
            placeholder="Name"
          />
          {form.errors.name && <p className="text-red-600 text-sm">{form.errors.name}</p>}

          <input
            value={form.data.email}
            onChange={(e) => form.setData('email', e.target.value)}
            placeholder="Email"
          />
          {form.errors.email && <p className="text-red-600 text-sm">{form.errors.email}</p>}

          <button type="button" onClick={nextStep}>Next</button>
        </div>
      )}

      {step === 2 && (
        <div>
          <h2>Company Info</h2>
          <input
            value={form.data.company}
            onChange={(e) => form.setData('company', e.target.value)}
            placeholder="Company"
          />
          <input
            value={form.data.role}
            onChange={(e) => form.setData('role', e.target.value)}
            placeholder="Role"
          />
          <button type="button" onClick={prevStep}>Back</button>
          <button type="button" onClick={nextStep}>Next</button>
        </div>
      )}

      {step === 3 && (
        <div>
          <h2>Plan Selection</h2>
          <select
            value={form.data.plan}
            onChange={(e) => form.setData('plan', e.target.value)}
          >
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>

          <label>
            <input
              type="checkbox"
              checked={form.data.agree_to_terms}
              onChange={(e) => form.setData('agree_to_terms', e.target.checked)}
            />
            I agree to the terms
          </label>

          <button type="button" onClick={prevStep}>Back</button>
          <button type="submit" disabled={form.processing}>
            {form.processing ? 'Submitting...' : 'Complete Registration'}
          </button>
        </div>
      )}
    </form>
  )
}
```

## Inline Validation Pattern

```tsx
import { useForm, router } from '@inertiajs/react'
import { useCallback } from 'react'

export default function UserForm() {
  const form = useForm({
    email: '',
    username: '',
  })

  // Validate a single field by submitting to a validation endpoint
  const validateField = useCallback(
    (field: string, value: string) => {
      router.post(
        '/users/validate',
        { field, value },
        {
          preserveState: true,
          preserveScroll: true,
          // Only update errors, do not navigate
          onSuccess: (page) => {
            // Errors are automatically merged
          },
        }
      )
    },
    []
  )

  return (
    <form onSubmit={(e) => { e.preventDefault(); form.post('/users') }}>
      <input
        value={form.data.email}
        onChange={(e) => form.setData('email', e.target.value)}
        onBlur={(e) => validateField('email', e.target.value)}
      />
      {form.errors.email && (
        <p className="text-red-600 text-sm mt-1">{form.errors.email}</p>
      )}

      <input
        value={form.data.username}
        onChange={(e) => form.setData('username', e.target.value)}
        onBlur={(e) => validateField('username', e.target.value)}
      />
      {form.errors.username && (
        <p className="text-red-600 text-sm mt-1">{form.errors.username}</p>
      )}

      <button type="submit" disabled={form.processing}>Submit</button>
    </form>
  )
}
```

Rails controller for inline validation:

```ruby
# app/controllers/users_controller.rb
def validate
  user = User.new(validate_params)
  user.valid?

  field = params[:field].to_sym
  if user.errors[field].any?
    redirect_back fallback_location: new_user_path,
                  inertia: { errors: { field => user.errors[field].first } }
  else
    redirect_back fallback_location: new_user_path
  end
end
```
