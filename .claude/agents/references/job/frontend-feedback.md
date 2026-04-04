# Background Job Frontend Feedback Patterns

## Decision Guide

| Processing Time | Pattern | Complexity |
|----------------|---------|------------|
| < 2 seconds | **Pattern 3: Flash + Redirect** | Simplest |
| 2-30 seconds | **Pattern 1: Polling** | Simple |
| > 30 seconds or progress needed | **Pattern 2: Action Cable** | Most complex |

---

## Pattern 1: Polling (Simple)

Best for: file exports, report generation, data imports (2-30s).

### Job

```ruby
# app/jobs/export_data_job.rb
class ExportDataJob < ApplicationJob
  queue_as :default

  def perform(export_id)
    export = Export.find(export_id)
    return if export.completed? # idempotent

    export.update!(status: :processing)

    data = ExportQuery.new(export.user, export.params).call
    export.file.attach(io: generate_csv(data), filename: "export.csv")
    export.update!(status: :completed)
  rescue StandardError => e
    export&.update!(status: :failed, error_message: e.message)
    raise # let Solid Queue handle retries
  end
end
```

### Controller

```ruby
# app/controllers/exports_controller.rb
class ExportsController < ApplicationController
  def create
    authorize Export
    export = Export.create!(user: current_user, status: :pending, params: export_params)
    ExportDataJob.perform_later(export.id)

    redirect_to export_path(export), notice: "Export started."
  end

  # Polling endpoint
  def show
    export = current_user.exports.find(params[:id])
    authorize export

    render inertia: 'Exports/Show', props: {
      export: {
        id: export.id,
        status: export.status,
        download_url: export.completed? ? rails_blob_url(export.file) : nil,
        error_message: export.error_message
      }
    }
  end
end
```

### React Hook

```tsx
// app/frontend/hooks/useJobStatus.ts
import { router } from '@inertiajs/react'
import { useEffect, useRef } from 'react'

export function useJobStatus(status: string, intervalMs = 2000) {
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    if (status === 'pending' || status === 'processing') {
      timerRef.current = setInterval(() => {
        router.reload({ only: ['export'] })
      }, intervalMs)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [status, intervalMs])
}
```

### Page Component

```tsx
// app/frontend/pages/Exports/Show.tsx
import { useJobStatus } from '@/hooks/useJobStatus'

interface Props {
  export: {
    id: number
    status: 'pending' | 'processing' | 'completed' | 'failed'
    download_url: string | null
    error_message: string | null
  }
}

export default function Show({ export: exp }: Props) {
  useJobStatus(exp.status)

  return (
    <div>
      {(exp.status === 'pending' || exp.status === 'processing') && (
        <div className="flex items-center gap-2">
          <Spinner /> Processing your export...
        </div>
      )}

      {exp.status === 'completed' && exp.download_url && (
        <a href={exp.download_url} className="btn-primary">Download Export</a>
      )}

      {exp.status === 'failed' && (
        <p className="text-red-600">Export failed: {exp.error_message}</p>
      )}
    </div>
  )
}
```

---

## Pattern 2: Action Cable (Real-time)

Best for: long-running operations, progress bars, real-time notifications (>30s).

### Channel

```ruby
# app/channels/job_status_channel.rb
class JobStatusChannel < ApplicationCable::Channel
  def subscribed
    stream_for current_user
  end
end
```

### Job with Broadcasting

```ruby
# app/jobs/bulk_import_job.rb
class BulkImportJob < ApplicationJob
  queue_as :default

  def perform(import_id)
    import = Import.find(import_id)
    records = parse_file(import.file)
    total = records.count

    records.each_with_index do |record, index|
      process_record(record)

      # Broadcast progress every 10 records
      if (index + 1) % 10 == 0
        broadcast_progress(import.user, import.id, index + 1, total)
      end
    end

    import.update!(status: :completed)
    broadcast_complete(import.user, import.id)
  end

  private

  def broadcast_progress(user, import_id, current, total)
    JobStatusChannel.broadcast_to(user, {
      type: 'progress',
      import_id: import_id,
      current: current,
      total: total,
      percentage: ((current.to_f / total) * 100).round
    })
  end

  def broadcast_complete(user, import_id)
    JobStatusChannel.broadcast_to(user, {
      type: 'complete',
      import_id: import_id
    })
  end
end
```

### React Hook

```tsx
// app/frontend/hooks/useJobProgress.ts
import { useState, useEffect } from 'react'
import { createConsumer } from '@rails/actioncable'

const cable = createConsumer()

interface JobProgress {
  type: 'progress' | 'complete'
  import_id: number
  current?: number
  total?: number
  percentage?: number
}

export function useJobProgress(importId: number) {
  const [progress, setProgress] = useState<JobProgress | null>(null)

  useEffect(() => {
    const subscription = cable.subscriptions.create('JobStatusChannel', {
      received(data: JobProgress) {
        if (data.import_id === importId) {
          setProgress(data)
        }
      },
    })

    return () => subscription.unsubscribe()
  }, [importId])

  return progress
}
```

---

## Pattern 3: Flash + Redirect (Simplest)

Best for: very short jobs (<2s) where the user can wait.

```ruby
# app/controllers/reports_controller.rb
def create
  authorize Report

  # Process synchronously for short operations
  result = Reports::GenerateService.call(user: current_user, params: report_params)

  if result.success?
    redirect_to report_path(result.data), notice: "Report generated."
  else
    redirect_back fallback_location: reports_path, alert: result.error
  end
end
```

For borderline cases (1-3s), you can use `perform_now` to keep it synchronous:

```ruby
def create
  authorize Export
  export = Export.create!(user: current_user, status: :pending)
  ExportDataJob.perform_now(export.id) # blocks until done
  redirect_to export_path(export), notice: "Export ready."
end
```

---

## Combining Patterns

Start with the simplest pattern and upgrade as needed:

1. **Start with Pattern 3** (synchronous) during development
2. **Upgrade to Pattern 1** (polling) when response times exceed 2s
3. **Upgrade to Pattern 2** (Action Cable) when you need progress bars or real-time updates
