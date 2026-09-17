import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const SLOW_REQUEST_MS = 1500

interface IdentifyResult {
  food_name: string
  translated_name: string | null
  target_language: string | null
  food_visual_description: string
  match_explanation: string
  confidence: string
  image_url: string | null
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [result, setResult] = useState<IdentifyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showLoader, setShowLoader] = useState(false)

  useEffect(() => {
    if (!loading) {
      setShowLoader(false)
      return
    }
    const timer = setTimeout(() => setShowLoader(true), SLOW_REQUEST_MS)
    return () => clearTimeout(timer)
  }, [loading])

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    setResult(null)
    setError(null)
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null)
  }

  async function submitPhoto(photoFile: File) {
    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('photo', photoFile)

    try {
      const res = await fetch(`${API_URL}/api/identify`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed (${res.status})`)
      }
      setResult(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    await submitPhoto(file)
  }

  async function handleFunExample() {
    setError(null)
    try {
      const res = await fetch('/fun-example.png')
      const blob = await res.blob()
      const exampleFile = new File([blob], 'fun-example.png', { type: blob.type || 'image/png' })
      setFile(exampleFile)
      setPreviewUrl(URL.createObjectURL(exampleFile))
      await submitPhoto(exampleFile)
    } catch {
      setError('Could not load the example image.')
    }
  }

  return (
    <main className="page">
      <h1 className="logo">Foodify</h1>
      <p className="tagline">Every photo hides a food twin.</p>

      <form onSubmit={handleSubmit} className="form">
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          onChange={handleFileChange}
        />

        {previewUrl && !result && <img src={previewUrl} alt="Preview" className="preview" />}

        {showLoader && (
          <div className="hourglass-loader" role="status" aria-label="Still working on it">
            <span aria-hidden="true">⏳</span>
          </div>
        )}

        <div className="button-row">
          <button type="submit" className="match-button match-button--compact" disabled={!file || loading}>
            {loading ? 'Finding…' : '🥐 Find my food match'}
          </button>
          <button
            type="button"
            className="match-button match-button--compact"
            onClick={handleFunExample}
            disabled={loading}
          >
            🎲 Fun example
          </button>
        </div>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="result-grid">
          <div className="result-col">
            {previewUrl && (
              <div className="result-image">
                <img src={previewUrl} alt="Original upload" />
              </div>
            )}
            <p className="col-label">Original</p>
          </div>
          <div className="result-col">
            {result.image_url && (
              <div className="result-image">
                <img src={result.image_url} alt={result.food_name} />
              </div>
            )}
            <h2>{result.food_name}</h2>
            {result.translated_name && (
              <p className="translated-name">
                {result.translated_name}
                {result.target_language ? ` (${result.target_language})` : ''}
              </p>
            )}
          </div>
        </section>
      )}
    </main>
  )
}

export default App
