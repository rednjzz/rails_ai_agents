---
paths:
  - "app/frontend/**/*.tsx"
  - "app/frontend/**/*.ts"
  - "app/frontend/**/*.jsx"
  - "app/views/**/*.erb"
  - "app/presenters/**/*.rb"
  - "spec/presenters/**/*.rb"
---

# View & Component Conventions

- Use React page components in `app/frontend/pages/` for all Inertia pages
- Use React components in `app/frontend/components/` for reusable UI elements
- Use `useForm()` from `@inertiajs/react` for form handling
- Use `<Link>` from `@inertiajs/react` for SPA-like navigation
- Use presenters (`app/presenters/`) with SimpleDelegator for formatting props data
- No business logic in components -- use presenters or services for data formatting
- Tailwind CSS 4 utility classes for styling
- Always include ARIA attributes for accessibility (WCAG 2.1 AA)
- ERB views only for ActionMailer templates
