import { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface IdentifyResult {
  dish_name: string
  translated_name: string | null
  target_language: string | null
  description: string
  likely_ingredients: string[]
  confidence: string
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [targetLanguage, setTargetLanguage] = useState('English')
  const [result, setResult] = useState<IdentifyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    setResult(null)
    setError(null)
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('photo', file)
    formData.append('target_language', targetLanguage)

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

  return (
    <main className="page">
      <h1>Food Translator</h1>
      <p>Take or upload a photo of anything, and we'll find the food it most resembles.</p>

      <form onSubmit={handleSubmit} className="form">
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          onChange={handleFileChange}
        />

        <label className="language-field">
          Translate to
          <input
            type="text"
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            placeholder="English"
          />
        </label>

        {previewUrl && <img src={previewUrl} alt="Preview" className="preview" />}

        <button type="submit" disabled={!file || loading}>
          {loading ? 'Finding a match…' : 'Find my food match'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="result">
          <h2>{result.dish_name}</h2>
          {result.translated_name && (
            <p className="translated-name">
              {result.translated_name}
              {result.target_language ? ` (${result.target_language})` : ''}
            </p>
          )}
          <p>{result.description}</p>
          {result.likely_ingredients.length > 0 && (
            <ul>
              {result.likely_ingredients.map((ingredient) => (
                <li key={ingredient}>{ingredient}</li>
              ))}
            </ul>
          )}
          <p className="confidence">Confidence: {result.confidence}</p>
        </section>
      )}
    </main>
  )
}

export default App
