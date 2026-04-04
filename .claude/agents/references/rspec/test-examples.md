# RSpec Test Examples

## Model Test

```ruby
# spec/models/user_spec.rb
require 'rails_helper'

RSpec.describe User, type: :model do
  describe 'associations' do
    it { is_expected.to have_many(:items).dependent(:destroy) }
    it { is_expected.to belong_to(:organization) }
  end

  describe 'validations' do
    subject { build(:user) }

    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_length_of(:username).is_at_least(3) }
  end

  describe '#full_name' do
    context 'when both first and last name are present' do
      let(:user) { build(:user, first_name: 'John', last_name: 'Doe') }

      it 'returns the full name' do
        expect(user.full_name).to eq('John Doe')
      end
    end

    context 'when only first name is present' do
      let(:user) { build(:user, first_name: 'John', last_name: nil) }

      it 'returns only the first name' do
        expect(user.full_name).to eq('John')
      end
    end
  end

  describe 'scopes' do
    describe '.active' do
      let!(:active_user) { create(:user, status: 'active') }
      let!(:inactive_user) { create(:user, status: 'inactive') }

      it 'returns only active users' do
        expect(User.active).to contain_exactly(active_user)
      end
    end
  end
end
```

## Service Test

```ruby
# spec/services/user_registration_service_spec.rb
require 'rails_helper'

RSpec.describe UserRegistrationService do
  subject(:service) { described_class.new(params) }

  describe '#call' do
    context 'with valid parameters' do
      let(:params) do
        {
          email: 'user@example.com',
          password: 'SecurePass123!',
          first_name: 'John'
        }
      end

      it 'creates a new user' do
        expect { service.call }.to change(User, :count).by(1)
      end

      it 'sends a welcome email' do
        expect(UserMailer).to receive(:welcome_email).and_call_original
        service.call
      end

      it 'returns success result' do
        result = service.call
        expect(result.success?).to be true
        expect(result.user).to be_a(User)
      end
    end

    context 'with invalid email' do
      let(:params) { { email: 'invalid', password: 'SecurePass123!' } }

      it 'does not create a user' do
        expect { service.call }.not_to change(User, :count)
      end

      it 'returns failure result with errors' do
        result = service.call
        expect(result.success?).to be false
        expect(result.errors).to include(:email)
      end
    end

    context 'when email already exists' do
      let(:params) { { email: existing_user.email, password: 'NewPass123!' } }
      let!(:existing_user) { create(:user) }

      it 'returns failure result' do
        result = service.call
        expect(result.success?).to be false
        expect(result.errors).to include('Email already taken')
      end
    end
  end
end
```

## Request Test (preferred over controller specs)

```ruby
# spec/requests/api/users_spec.rb
require 'rails_helper'

RSpec.describe 'API::Users', type: :request do
  let(:user) { create(:user) }
  let(:headers) { { 'Authorization' => "Bearer #{user.auth_token}" } }

  describe 'GET /api/users/:id' do
    context 'when user exists' do
      it 'returns the user' do
        get "/api/users/#{user.id}", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json_response['id']).to eq(user.id)
        expect(json_response['email']).to eq(user.email)
      end
    end

    context 'when user does not exist' do
      it 'returns 404' do
        get '/api/users/999999', headers: headers

        expect(response).to have_http_status(:not_found)
        expect(json_response['error']).to eq('User not found')
      end
    end

    context 'when not authenticated' do
      it 'returns 401' do
        get "/api/users/#{user.id}"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /api/users' do
    let(:valid_params) do
      {
        user: {
          email: 'newuser@example.com',
          password: 'SecurePass123!',
          first_name: 'Jane'
        }
      }
    end

    context 'with valid parameters' do
      it 'creates a new user' do
        expect {
          post '/api/users', params: valid_params, headers: headers
        }.to change(User, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json_response['email']).to eq('newuser@example.com')
      end
    end

    context 'with invalid parameters' do
      let(:invalid_params) do
        { user: { email: 'invalid' } }
      end

      it 'returns validation errors' do
        post '/api/users', params: invalid_params, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response['errors']).to be_present
      end
    end
  end
end
```

## Inertia Request Test

```ruby
# spec/requests/users_spec.rb
require 'rails_helper'

RSpec.describe 'Users', type: :request do
  let(:user) { create(:user) }

  before { sign_in(user) }

  describe 'GET /users' do
    let!(:user_a) { create(:user, first_name: 'John', last_name: 'Doe') }

    it 'renders the Users/Index component' do
      get users_path

      expect(response).to have_http_status(:ok)
      expect(inertia.component).to eq('Users/Index')
    end

    it 'includes users in props' do
      get users_path

      expect(inertia.props[:users]).to be_an(Array)
      user_props = inertia.props[:users].find { |u| u[:id] == user_a.id }
      expect(user_props).to include(first_name: 'John', last_name: 'Doe')
    end
  end

  describe 'POST /users' do
    context 'with valid params' do
      let(:valid_params) { { user: { email: 'new@example.com', first_name: 'Jane' } } }

      it 'creates and redirects' do
        expect { post users_path, params: valid_params }
          .to change(User, :count).by(1)

        expect(response).to have_http_status(:redirect)
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { user: { email: '' } } }

      it 'returns validation errors' do
        post users_path, params: invalid_params

        expect(response).to have_http_status(:unprocessable_entity)
        expect(inertia.component).to eq('Users/New')
        expect(inertia.props[:errors]).to include(:email)
      end
    end
  end
end
```

## Query Object Test

```ruby
# spec/queries/active_users_query_spec.rb
require 'rails_helper'

RSpec.describe ActiveUsersQuery do
  subject(:query) { described_class.new(relation) }

  let(:relation) { User.all }

  describe '#call' do
    let!(:active_user) { create(:user, status: 'active', last_sign_in_at: 2.days.ago) }
    let!(:inactive_user) { create(:user, status: 'inactive') }
    let!(:old_active_user) { create(:user, status: 'active', last_sign_in_at: 40.days.ago) }

    it 'returns only active users signed in within 30 days' do
      expect(query.call).to contain_exactly(active_user)
    end

    context 'with custom days threshold' do
      subject(:query) { described_class.new(relation, days: 60) }

      it 'returns users within the specified threshold' do
        expect(query.call).to contain_exactly(active_user, old_active_user)
      end
    end
  end
end
```

## Pundit Policy Test

```ruby
# spec/policies/submission_policy_spec.rb
require 'rails_helper'

RSpec.describe SubmissionPolicy do
  subject { described_class.new(user, submission) }

  let(:submission) { create(:submission, user: author) }
  let(:author) { create(:user) }

  context 'when user is the author' do
    let(:user) { author }

    it { is_expected.to permit_action(:show) }
    it { is_expected.to permit_action(:edit) }
    it { is_expected.to permit_action(:update) }
    it { is_expected.to permit_action(:destroy) }
  end

  context 'when user is not the author' do
    let(:user) { create(:user) }

    it { is_expected.to permit_action(:show) }
    it { is_expected.to forbid_action(:edit) }
    it { is_expected.to forbid_action(:update) }
    it { is_expected.to forbid_action(:destroy) }
  end

  context 'when user is an admin' do
    let(:user) { create(:user, :admin) }

    it { is_expected.to permit_action(:show) }
    it { is_expected.to permit_action(:edit) }
    it { is_expected.to permit_action(:update) }
    it { is_expected.to permit_action(:destroy) }
  end

  context 'when user is not logged in' do
    let(:user) { nil }

    it { is_expected.to permit_action(:show) }
    it { is_expected.to forbid_action(:edit) }
  end
end
```

## System Test (end-to-end)

```ruby
# spec/system/user_authentication_spec.rb
require 'rails_helper'

RSpec.describe 'User Authentication', type: :system do
  let(:user) { create(:user, email: 'user@example.com', password: 'SecurePass123!') }

  describe 'Sign in' do
    before do
      visit new_user_session_path
    end

    context 'with valid credentials' do
      it 'signs in the user successfully' do
        fill_in 'Email', with: user.email
        fill_in 'Password', with: 'SecurePass123!'
        click_button 'Sign in'

        expect(page).to have_content('Signed in successfully')
        expect(page).to have_current_path(root_path)
      end
    end

    context 'with invalid password' do
      it 'shows an error message' do
        fill_in 'Email', with: user.email
        fill_in 'Password', with: 'WrongPassword'
        click_button 'Sign in'

        expect(page).to have_content('Invalid email or password')
        expect(page).to have_current_path(new_user_session_path)
      end
    end

    context 'with Inertia response' do
      it 'renders the correct component after sign in' do
        post '/sessions', params: { email: user.email, password: 'SecurePass123!' }

        expect(response).to redirect_to(root_path)
      end
    end
  end
end
```

## Anti-Pattern to Avoid

```ruby
# Don't do this!
RSpec.describe User do
  it 'works' do
    user = User.new(email: 'test@example.com')
    expect(user.email).to eq('test@example.com')
  end

  # Too vague, no context
  it 'validates' do
    expect(User.new).not_to be_valid
  end

  # Tests multiple things at once
  it 'creates user and sends email' do
    user = User.create(email: 'test@example.com')
    expect(user).to be_persisted
    expect(ActionMailer::Base.deliveries.count).to eq(1)
    expect(user.active?).to be true
  end
end
```
