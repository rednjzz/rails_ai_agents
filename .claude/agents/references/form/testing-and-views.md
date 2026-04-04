# Form Object Testing and View Integration

## RSpec Tests: Basic Form

```ruby
# spec/forms/entity_registration_form_spec.rb
require "rails_helper"

RSpec.describe EntityRegistrationForm do
  describe "#save" do
    subject(:form) { described_class.new(attributes) }

    let(:owner) { create(:user) }
    let(:attributes) do
      {
        name: "Test Entity",
        description: "An excellent test entity",
        address: "123 Main Street",
        phone: "1234567890",
        email: "contact@example.com",
        owner_id: owner.id
      }
    end

    context "with valid attributes" do
      it "is valid" do
        expect(form).to be_valid
      end

      it "creates an entity" do
        expect { form.save }.to change(Entity, :count).by(1)
      end

      it "creates contact information" do
        form.save
        expect(form.entity.contact_info).to be_present
        expect(form.entity.contact_info.email).to eq("contact@example.com")
      end

      it "sends a confirmation email" do
        expect {
          form.save
        }.to have_enqueued_job(ActionMailer::MailDeliveryJob)
      end

      it "returns true" do
        expect(form.save).to be true
      end
    end

    context "with missing name" do
      let(:attributes) { super().merge(name: "") }

      it "is not valid" do
        expect(form).not_to be_valid
      end

      it "does not create an entity" do
        expect { form.save }.not_to change(Entity, :count)
      end

      it "returns false" do
        expect(form.save).to be false
      end

      it "adds an error to name" do
        form.valid?
        expect(form.errors[:name]).to include("can't be blank")
      end
    end

    context "with invalid email" do
      let(:attributes) { super().merge(email: "invalid") }

      it "is not valid" do
        expect(form).not_to be_valid
        expect(form.errors[:email]).to be_present
      end
    end

    context "with non-existent owner_id" do
      let(:attributes) { super().merge(owner_id: 99999) }

      it "is not valid" do
        expect(form).not_to be_valid
        expect(form.errors[:owner_id]).to include("does not exist")
      end
    end
  end
end
```

## RSpec Tests: Nested Associations

```ruby
# spec/forms/entity_with_items_form_spec.rb
require "rails_helper"

RSpec.describe EntityWithItemsForm do
  describe "#save" do
    subject(:form) { described_class.new(attributes) }

    let(:owner) { create(:user) }
    let(:attributes) do
      {
        name: "Test Entity",
        description: "Test description",
        owner_id: owner.id,
        items: [
          { name: "Item One", description: "With details", price: "18.50", category: "category_a" },
          { name: "Item Two", description: "Another one", price: "7.00", category: "category_b" }
        ]
      }
    end

    context "with valid items" do
      it "creates the entity with items" do
        expect { form.save }.to change(Entity, :count).by(1)
                                .and change(Item, :count).by(2)
      end

      it "correctly associates the items" do
        form.save
        expect(form.entity.items.count).to eq(2)
        expect(form.entity.items.pluck(:name)).to contain_exactly(
          "Item One", "Item Two"
        )
      end
    end

    context "with invalid price" do
      let(:attributes) do
        super().merge(
          items: [{ name: "Test", price: "-5", category: "category_a" }]
        )
      end

      it "is not valid" do
        expect(form).not_to be_valid
        expect(form.errors[:base]).to include(/price.*must be positive/)
      end
    end
  end
end
```

## Controller Usage (Inertia)

```ruby
# app/controllers/entities_controller.rb
class EntitiesController < ApplicationController
  def new
    render inertia: 'Entities/New', props: {
      owner_id: current_user.id
    }
  end

  def create
    @form = EntityRegistrationForm.new(registration_params)

    if @form.save
      redirect_to @form.entity, notice: "Entity created successfully"
    else
      render inertia: 'Entities/New', props: {
        owner_id: current_user.id,
        errors: @form.errors.messages
      }, status: :unprocessable_entity
    end
  end

  private

  def registration_params
    params.require(:entity_registration_form).permit(
      :name, :description, :address, :phone, :email, :owner_id
    )
  end
end
```

## React Page: Registration Form with useForm

```tsx
// app/frontend/pages/Entities/New.tsx
import { Head } from '@inertiajs/react'
import { useForm } from '@inertiajs/react'
import FormInput from '@/components/ui/FormInput'

interface Props {
  owner_id: number
}

export default function New({ owner_id }: Props) {
  const form = useForm({
    name: '',
    description: '',
    address: '',
    phone: '',
    email: '',
    owner_id: owner_id,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    form.post('/entities')
  }

  return (
    <>
      <Head title="New Entity" />

      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <FormInput
          label="Name"
          value={form.data.name}
          onChange={(e) => form.setData('name', e.target.value)}
          error={form.errors.name}
        />

        <div className="space-y-1">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <textarea
            id="description"
            value={form.data.description}
            onChange={(e) => form.setData('description', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            rows={4}
          />
          {form.errors.description && (
            <p className="text-red-600 text-sm">{form.errors.description}</p>
          )}
        </div>

        <FormInput
          label="Address"
          value={form.data.address}
          onChange={(e) => form.setData('address', e.target.value)}
          error={form.errors.address}
        />

        <FormInput
          label="Phone"
          type="tel"
          value={form.data.phone}
          onChange={(e) => form.setData('phone', e.target.value)}
          error={form.errors.phone}
        />

        <FormInput
          label="Email"
          type="email"
          value={form.data.email}
          onChange={(e) => form.setData('email', e.target.value)}
          error={form.errors.email}
        />

        <button
          type="submit"
          disabled={form.processing}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md"
        >
          {form.processing ? 'Creating...' : 'Create Entity'}
        </button>
      </form>
    </>
  )
}
```

## React Page: Nested Form with Dynamic Items

```tsx
// app/frontend/pages/Entities/NewWithItems.tsx
import { Head, useForm } from '@inertiajs/react'
import { useState } from 'react'

interface ItemData {
  name: string
  description: string
  price: string
  category: string
}

interface FormData {
  name: string
  description: string
  owner_id: number
  items: ItemData[]
}

export default function NewWithItems({ owner_id }: { owner_id: number }) {
  const form = useForm<FormData>({
    name: '',
    description: '',
    owner_id: owner_id,
    items: [],
  })

  function addItem() {
    form.setData('items', [
      ...form.data.items,
      { name: '', description: '', price: '', category: 'category_a' },
    ])
  }

  function removeItem(index: number) {
    form.setData(
      'items',
      form.data.items.filter((_, i) => i !== index)
    )
  }

  function updateItem(index: number, field: keyof ItemData, value: string) {
    const updated = [...form.data.items]
    updated[index] = { ...updated[index], [field]: value }
    form.setData('items', updated)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    form.post('/entities')
  }

  return (
    <>
      <Head title="New Entity with Items" />

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        <input
          type="text"
          value={form.data.name}
          onChange={(e) => form.setData('name', e.target.value)}
          placeholder="Entity name"
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />

        <textarea
          value={form.data.description}
          onChange={(e) => form.setData('description', e.target.value)}
          placeholder="Description"
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />

        <div>
          <h3 className="text-lg font-semibold mb-2">Items</h3>

          {form.data.items.map((item, index) => (
            <div key={index} className="flex gap-2 mb-2 items-start">
              <input
                type="text"
                value={item.name}
                onChange={(e) => updateItem(index, 'name', e.target.value)}
                placeholder="Item name"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <input
                type="text"
                value={item.description}
                onChange={(e) => updateItem(index, 'description', e.target.value)}
                placeholder="Description"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <input
                type="number"
                step="0.01"
                value={item.price}
                onChange={(e) => updateItem(index, 'price', e.target.value)}
                placeholder="Price"
                className="w-24 px-3 py-2 border border-gray-300 rounded-md"
              />
              <select
                value={item.category}
                onChange={(e) => updateItem(index, 'category', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="category_a">Category A</option>
                <option value="category_b">Category B</option>
                <option value="category_c">Category C</option>
                <option value="category_d">Category D</option>
              </select>
              <button
                type="button"
                onClick={() => removeItem(index)}
                className="text-red-600 hover:text-red-800 px-2 py-2"
              >
                Remove
              </button>
            </div>
          ))}

          <button
            type="button"
            onClick={addItem}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Add Item
          </button>
        </div>

        <button
          type="submit"
          disabled={form.processing}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md"
        >
          {form.processing ? 'Creating...' : 'Create'}
        </button>
      </form>
    </>
  )
}
```
