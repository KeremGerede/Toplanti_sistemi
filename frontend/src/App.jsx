import { useState } from 'react'

// Saniye → mm:ss.mmm (bir saat ve üzeri için h:mm:ss.mmm)
function formatTime(seconds) {
  const ms = Math.round(seconds * 1000)
  const h = Math.floor(ms / 3600000)
  const m = String(Math.floor((ms % 3600000) / 60000)).padStart(2, '0')
  const s = String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')
  const rest = String(ms % 1000).padStart(3, '0')
  return h > 0 ? `${h}:${m}:${s}.${rest}` : `${m}:${s}.${rest}`
}

function errorMessage(status, data) {
  if (typeof data?.detail === 'string') return data.detail
  if (status >= 500) return `Backend'e ulaşılamadı veya sunucu hatası oluştu (HTTP ${status}).`
  return `İstek başarısız oldu (HTTP ${status}).`
}

export default function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function selectFile(event) {
    setFile(event.target.files[0] ?? null)
    setResult(null)
    setError('')
  }

  async function analyze() {
    setLoading(true)
    setResult(null)
    setError('')
    const body = new FormData()
    body.append('file', file)
    try {
      const response = await fetch('/diarize', { method: 'POST', body })
      const data = await response.json().catch(() => null)
      if (response.ok && data) setResult(data)
      else setError(errorMessage(response.status, data))
    } catch {
      setError("Backend'e ulaşılamadı.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>Toplantı Sistemi</h1>

      <section className="panel">
        <input type="file" accept=".wav,.flac" onChange={selectFile} disabled={loading} />
        <p className="file-name">{file ? file.name : 'Dosya seçilmedi (WAV veya FLAC)'}</p>
        <button onClick={analyze} disabled={!file || loading}>
          {loading ? 'Analiz ediliyor...' : 'Analiz Et'}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <section>
          <div className="summary">
            <p><strong>Dosya adı:</strong> {result.source_file}</p>
            <p><strong>Konuşmacı sayısı:</strong> {result.speaker_count}</p>
          </div>
          <ol className="segments">
            {result.segments.map((segment, index) => (
              <li key={index} className="segment">
                <div className="speaker">{segment.speaker}</div>
                <div className="time">{formatTime(segment.start)} - {formatTime(segment.end)}</div>
                {segment.text ? <p className="text">{segment.text}</p> : <p className="text empty">(metin yok)</p>}
              </li>
            ))}
          </ol>
        </section>
      )}
    </main>
  )
}
