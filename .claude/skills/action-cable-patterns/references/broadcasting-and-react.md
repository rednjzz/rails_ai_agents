# Broadcasting and React Integration

## Broadcasting from Services

```ruby
# app/services/events/update_service.rb
module Events
  class UpdateService
    def call(event, params)
      event.update!(params)

      # Broadcast to all viewers
      EventsChannel.broadcast_update(event)

      # Update dashboard stats
      DashboardChannel.broadcast_stats(event.account)

      success(event)
    end
  end
end
```

## Broadcasting from Models

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :event
  belongs_to :user

  after_create_commit :broadcast_to_channel

  private

  def broadcast_to_channel
    EventsChannel.broadcast_comment(event, self)
  end
end
```

## React Hook for Action Cable Subscriptions

```typescript
// app/frontend/hooks/useActionCable.ts
import { useEffect, useRef, useCallback, useState } from 'react'
import { createConsumer, Subscription } from '@rails/actioncable'

const consumer = createConsumer()

interface UseActionCableOptions<T> {
  channel: string
  params?: Record<string, unknown>
  onReceived: (data: T) => void
  onConnected?: () => void
  onDisconnected?: () => void
}

export function useActionCable<T>({
  channel,
  params = {},
  onReceived,
  onConnected,
  onDisconnected,
}: UseActionCableOptions<T>) {
  const subscriptionRef = useRef<Subscription | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    subscriptionRef.current = consumer.subscriptions.create(
      { channel, ...params },
      {
        received: onReceived,
        connected: () => {
          setConnected(true)
          onConnected?.()
        },
        disconnected: () => {
          setConnected(false)
          onDisconnected?.()
        },
      }
    )

    return () => {
      subscriptionRef.current?.unsubscribe()
    }
  }, [channel, JSON.stringify(params)])

  const perform = useCallback(
    (action: string, data?: Record<string, unknown>) => {
      subscriptionRef.current?.perform(action, data)
    },
    []
  )

  return { connected, perform }
}
```

## React Component Using Action Cable

```tsx
// app/frontend/components/ChatRoom.tsx
import { useState, useRef, useEffect } from 'react'
import { useActionCable } from '../hooks/useActionCable'

interface Message {
  id: number
  body: string
  user_name: string
  created_at: string
}

interface ChatRoomProps {
  roomId: number
  initialMessages: Message[]
}

export default function ChatRoom({ roomId, initialMessages }: ChatRoomProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { connected, perform } = useActionCable<{ type: string; message: Message }>({
    channel: 'ChatChannel',
    params: { room_id: roomId },
    onReceived: (data) => {
      if (data.type === 'message') {
        setMessages((prev) => [...prev, data.message])
      }
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      perform('speak', { body: input })
      setInput('')
    }
  }

  return (
    <div className={connected ? '' : 'opacity-50'}>
      <div className="overflow-y-auto max-h-96">
        {messages.map((msg) => (
          <div key={msg.id} className="p-2">
            <strong>{msg.user_name}:</strong> {msg.body}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-2 mt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 border rounded px-3 py-2"
          placeholder="Type a message..."
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
          Send
        </button>
      </form>
    </div>
  )
}
```

## Performance Considerations

### Connection Limits

```ruby
# config/initializers/action_cable.rb
Rails.application.config.action_cable.max_connections_per_server = 1000
```

### Selective Broadcasting

```ruby
# Only broadcast to connected users
def self.broadcast_if_subscribed(user, data)
  return unless ActionCable.server.connections.any? { |c| c.current_user == user }
  broadcast_to(user, data)
end
```

### Debouncing Broadcasts

```ruby
# app/services/broadcast_service.rb
class BroadcastService
  def self.debounced_broadcast(key, data, wait: 1.second)
    Rails.cache.fetch("broadcast:#{key}", expires_in: wait) do
      yield
      true
    end
  end
end
```
