# Inertia.js Testing with RSpec

## RSpec Request Spec Setup

```ruby
# spec/rails_helper.rb
require 'inertia_rails/rspec'

RSpec.configure do |config|
  # inertia_rails/rspec provides the `inertia` helper automatically
  # for request specs when type: :request
end
```

## Asserting Rendered Component

```ruby
# spec/requests/users_spec.rb
require 'rails_helper'

RSpec.describe 'Users', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'GET /users' do
    it 'renders the Users/Index component' do
      get users_path

      expect(response).to have_http_status(:ok)
      expect(inertia.component).to eq('Users/Index')
    end
  end

  describe 'GET /users/:id' do
    let(:target_user) { create(:user, name: 'Jane Doe') }

    it 'renders the Users/Show component' do
      get user_path(target_user)

      expect(response).to have_http_status(:ok)
      expect(inertia.component).to eq('Users/Show')
    end
  end

  describe 'GET /users/new' do
    it 'renders the Users/New component' do
      get new_user_path

      expect(response).to have_http_status(:ok)
      expect(inertia.component).to eq('Users/New')
    end
  end
end
```

## Asserting Props

```ruby
# spec/requests/users_spec.rb
RSpec.describe 'Users', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'GET /users' do
    let!(:user_a) { create(:user, name: 'Alice') }
    let!(:user_b) { create(:user, name: 'Bob') }

    it 'passes users as props' do
      get users_path

      expect(inertia.props[:users]).to be_an(Array)
      expect(inertia.props[:users].length).to eq(3) # includes signed-in user
    end

    it 'includes expected user attributes in props' do
      get users_path

      user_props = inertia.props[:users].find { |u| u[:name] == 'Alice' }
      expect(user_props).to include(
        id: user_a.id,
        name: 'Alice',
        email: user_a.email
      )
    end
  end

  describe 'GET /users/:id' do
    let(:target_user) { create(:user, name: 'Jane', email: 'jane@example.com') }

    it 'passes the user as props' do
      get user_path(target_user)

      expect(inertia.props[:user]).to include(
        id: target_user.id,
        name: 'Jane',
        email: 'jane@example.com'
      )
    end
  end
end
```

## Testing Shared Data

```ruby
# spec/requests/shared_data_spec.rb
require 'rails_helper'

RSpec.describe 'Shared Inertia Data', type: :request do
  let(:user) { create(:user, name: 'John') }

  describe 'current_user' do
    context 'when signed in' do
      before { sign_in(user) }

      it 'shares current_user in props' do
        get root_path

        expect(inertia.props[:current_user]).to include(
          id: user.id,
          name: 'John'
        )
      end
    end

    context 'when not signed in' do
      it 'shares nil for current_user' do
        get root_path

        expect(inertia.props[:current_user]).to be_nil
      end
    end
  end

  describe 'flash messages' do
    before { sign_in(user) }

    it 'shares flash notice after create' do
      post users_path, params: { user: { name: 'New User', email: 'new@example.com' } }
      follow_redirect!

      expect(inertia.props[:flash]).to include(notice: 'User created successfully.')
    end

    it 'shares flash alert on error' do
      post users_path, params: { user: { name: '', email: '' } }

      # Depending on controller implementation, errors may be in props
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```

## Testing Redirects

```ruby
# spec/requests/users_spec.rb
RSpec.describe 'Users', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'POST /users' do
    let(:valid_params) do
      { user: { name: 'New User', email: 'new@example.com', password: 'SecurePass123!' } }
    end

    context 'with valid params' do
      it 'redirects to the user page' do
        post users_path, params: valid_params

        expect(response).to have_http_status(:redirect)
        expect(response).to redirect_to(user_path(User.last))
      end
    end

    context 'when not authorized' do
      let(:guest) { create(:user, role: :guest) }

      before { sign_in(guest) }

      it 'redirects with an alert' do
        post users_path, params: valid_params

        expect(response).to redirect_to(root_path)
      end
    end
  end

  describe 'DELETE /users/:id' do
    let!(:target_user) { create(:user) }

    it 'redirects to the users index' do
      delete user_path(target_user)

      expect(response).to redirect_to(users_path)
    end
  end
end
```

## Testing Error Responses (Validation Errors)

```ruby
# spec/requests/users_spec.rb
RSpec.describe 'Users', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'POST /users' do
    context 'with invalid params' do
      let(:invalid_params) do
        { user: { name: '', email: 'invalid' } }
      end

      it 'returns unprocessable entity status' do
        post users_path, params: invalid_params

        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'renders the Users/New component with errors' do
        post users_path, params: invalid_params

        expect(inertia.component).to eq('Users/New')
      end

      it 'includes validation errors in props' do
        post users_path, params: invalid_params

        # Errors are available via the Inertia errors bag
        expect(inertia.props[:errors]).to include(:name)
        expect(inertia.props[:errors]).to include(:email)
      end
    end
  end

  describe 'PATCH /users/:id' do
    let(:target_user) { create(:user) }

    context 'with invalid params' do
      it 'returns errors for invalid email' do
        patch user_path(target_user), params: { user: { email: '' } }

        expect(response).to have_http_status(:unprocessable_entity)
        expect(inertia.props[:errors]).to have_key(:email)
      end
    end
  end
end
```

## Full Controller + Test Example

```ruby
# app/controllers/restaurants_controller.rb
class RestaurantsController < ApplicationController
  before_action :authenticate_user!
  before_action :set_restaurant, only: [:show, :edit, :update, :destroy]

  def index
    restaurants = Restaurant.all.order(created_at: :desc)
    authorize restaurants

    render inertia: 'Restaurants/Index', props: {
      restaurants: RestaurantSerializer.new(restaurants)
    }
  end

  def create
    authorize Restaurant

    result = Restaurants::CreateService.call(
      user: current_user,
      params: restaurant_params
    )

    if result.success?
      redirect_to restaurant_path(result.data), notice: 'Restaurant created successfully.'
    else
      render inertia: 'Restaurants/New', props: {
        errors: result.error.messages
      }, status: :unprocessable_entity
    end
  end

  private

  def set_restaurant
    @restaurant = Restaurant.find(params[:id])
  end

  def restaurant_params
    params.require(:restaurant).permit(:name, :description, :address, :phone)
  end
end
```

```ruby
# spec/requests/restaurants_spec.rb
require 'rails_helper'

RSpec.describe 'Restaurants', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'GET /restaurants' do
    let!(:restaurant) { create(:restaurant, name: 'Test Place') }

    it 'renders index with restaurant data' do
      get restaurants_path

      expect(inertia.component).to eq('Restaurants/Index')
      expect(inertia.props[:restaurants]).to be_an(Array)
      expect(inertia.props[:restaurants].first).to include(name: 'Test Place')
    end
  end

  describe 'POST /restaurants' do
    context 'with valid params' do
      let(:params) { { restaurant: { name: 'New Place', description: 'Great food' } } }

      it 'creates and redirects' do
        expect { post restaurants_path, params: params }
          .to change(Restaurant, :count).by(1)

        expect(response).to have_http_status(:redirect)
      end
    end

    context 'with invalid params' do
      let(:params) { { restaurant: { name: '' } } }

      it 'returns errors' do
        post restaurants_path, params: params

        expect(response).to have_http_status(:unprocessable_entity)
        expect(inertia.component).to eq('Restaurants/New')
        expect(inertia.props[:errors]).to have_key(:name)
      end
    end
  end
end
```
