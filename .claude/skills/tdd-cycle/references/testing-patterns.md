# TDD Testing Patterns Reference

## Workflow Checklist

Copy and track progress:

```
TDD Progress:
- [ ] Step 1: Understand the requirement
- [ ] Step 2: Choose test type (unit/request/system)
- [ ] Step 3: Write failing spec (RED)
- [ ] Step 4: Verify spec fails correctly
- [ ] Step 5: Implement minimal code (GREEN)
- [ ] Step 6: Verify spec passes
- [ ] Step 7: Refactor if needed
- [ ] Step 8: Verify specs still pass
```

## Spec Structure Template

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ClassName, type: :spec_type do
  describe '#method_name' do
    subject { described_class.new(args) }

    context 'when condition is met' do
      let(:dependency) { create(:factory) }

      it 'behaves as expected' do
        expect(subject.method_name).to eq(expected_value)
      end
    end

    context 'when edge case' do
      it 'handles gracefully' do
        expect { subject.method_name }.to raise_error(SpecificError)
      end
    end
  end
end
```

## Common Patterns

### Testing Validations

```ruby
describe 'validations' do
  it { is_expected.to validate_presence_of(:email) }
  it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
  it { is_expected.to validate_length_of(:name).is_at_most(100) }
end
```

### Testing Associations

```ruby
describe 'associations' do
  it { is_expected.to belong_to(:organization) }
  it { is_expected.to have_many(:posts).dependent(:destroy) }
end
```

### Testing Scopes

```ruby
describe '.active' do
  let!(:active_user) { create(:user, status: :active) }
  let!(:inactive_user) { create(:user, status: :inactive) }

  it 'returns only active users' do
    expect(User.active).to contain_exactly(active_user)
  end
end
```

### Testing Service Objects

```ruby
describe '#call' do
  subject(:result) { described_class.new.call(params) }

  context 'with valid params' do
    let(:params) { { email: 'test@example.com' } }

    it 'returns success' do
      expect(result).to be_success
    end

    it 'creates a user' do
      expect { result }.to change(User, :count).by(1)
    end
  end

  context 'with invalid params' do
    let(:params) { { email: '' } }

    it 'returns failure' do
      expect(result).to be_failure
    end
  end
end
```

## Anti-Patterns to Avoid

1. **Testing implementation, not behavior**: Test what it does, not how
2. **Too many assertions**: Split into separate examples
3. **Brittle tests**: Don't test exact error messages or timestamps
4. **Slow tests**: Use `build` over `create`, mock external services
5. **Mystery guests**: Make test data explicit, not hidden in factories
