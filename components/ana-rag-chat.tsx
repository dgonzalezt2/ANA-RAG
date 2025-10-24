"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Loader2, Send, Brain, BarChart3, CheckCircle2, AlertCircle } from "lucide-react"

interface ApiResponse {
  answer: string
  success: boolean
  message?: string
}

export function AnaRagChat() {
  const [question, setQuestion] = useState("")
  const [response, setResponse] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!question.trim()) {
      setError("Por favor ingresa una pregunta")
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: question.trim() }),
      })

      if (!res.ok) {
        throw new Error("Error en la solicitud")
      }

      const data: ApiResponse = await res.json()
      setResponse(data)
      setQuestion("")
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No pude generar una respuesta con el modelo remoto. Intenta nuevamente.",
      )
      setResponse({
        answer: "No pude generar una respuesta con el modelo remoto. Intenta nuevamente.",
        success: false,
        message: "Error de conexión",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen px-4 py-8">
      <div className="w-full max-w-3xl">
        {/* Header with Icon */}
        <div className="mb-10 text-center animate-slide-up">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-xl shadow-lg">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
              ANA-RAG
            </h1>
          </div>
          <h2 className="text-2xl font-semibold text-slate-800 mb-3">Asistente Generativo de Analítica</h2>
          <p className="text-lg text-slate-600 mb-4">
            Haz preguntas sobre tus datos de producción y obtén análisis generados por IA
          </p>
          <p className="text-sm text-slate-500 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 inline-block">
            ANA-RAG utiliza una arquitectura de Recuperación Aumentada por Generación (RAG) para analizar información
            contextual y ofrecer respuestas fundamentadas.
          </p>
        </div>

        {/* Input Section */}
        <Card className="p-8 mb-6 border-slate-200 shadow-xl bg-white/80 backdrop-blur-sm animate-slide-up transition-all hover:shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <label htmlFor="question" className="block text-sm font-semibold text-slate-700">
                Escribe tu pregunta para ANA
              </label>
              <div className="flex gap-2">
                <Input
                  id="question"
                  type="text"
                  placeholder="Ej: ¿Por qué bajó la producción en octubre?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                  className="flex-1 border-slate-300 bg-slate-50 focus:bg-white transition-colors"
                />
                <Button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white px-6 shadow-lg transition-all hover:shadow-xl disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="ml-2 hidden sm:inline">Analizando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span className="ml-2 hidden sm:inline">Enviar</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
            {loading && (
              <div className="flex items-center gap-2 text-sm text-blue-600 animate-pulse">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
                <span>ANA está analizando tus datos…</span>
              </div>
            )}
          </form>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="p-4 mb-6 border-red-200 bg-red-50 shadow-lg animate-slide-up transition-all">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </Card>
        )}

        {/* Response Section */}
        {response && (
          <Card className="p-8 border-slate-200 shadow-xl bg-white/80 backdrop-blur-sm space-y-6 animate-slide-up transition-all">
            {/* Status Indicator */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-200">
              {response.success ? (
                <>
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-700">Análisis completado exitosamente</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-6 h-6 text-red-500" />
                  <span className="text-sm font-semibold text-red-700">Error en el análisis</span>
                </>
              )}
            </div>

            {/* Answer */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h3 className="text-sm font-semibold text-slate-700">Análisis</h3>
              </div>
              <div className="bg-gradient-to-br from-slate-50 to-blue-50 border border-slate-200 rounded-lg p-5 text-slate-800 leading-relaxed text-base">
                {response.answer || "No se recibió respuesta"}
              </div>
            </div>

            {/* Message */}
            {response.message && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Información adicional</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-blue-800 text-sm">
                  {response.message}
                </div>
              </div>
            )}

            {/* JSON Response with Syntax Highlighting */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-700">Respuesta JSON</h3>
              <div className="bg-slate-900 text-slate-100 p-5 rounded-lg overflow-x-auto shadow-inner">
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                  <code>
                    {JSON.stringify(response, null, 2)
                      .split("\n")
                      .map((line, i) => (
                        <div key={i} className="hover:bg-slate-800 transition-colors px-2">
                          <span className="text-slate-500">{String(i + 1).padStart(2, " ")}</span>
                          <span className="ml-4">{line}</span>
                        </div>
                      ))}
                  </code>
                </pre>
              </div>
            </div>
          </Card>
        )}

        {/* Empty State */}
        {!response && !error && !loading && (
          <Card className="p-12 text-center border-slate-200 bg-white/50 backdrop-blur-sm shadow-lg animate-slide-up">
            <div className="mb-4 flex justify-center">
              <div className="p-3 bg-slate-100 rounded-full">
                <Brain className="w-8 h-8 text-slate-400" />
              </div>
            </div>
            <p className="text-slate-600 text-lg font-medium mb-2">Comienza tu análisis</p>
            <p className="text-slate-500">
              Haz una pregunta sobre tus datos de producción. ANA analizará la información y te proporcionará un
              análisis fundamentado.
            </p>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-slate-500 animate-fade-in">
          <p>Powered by Evergreen · ANA-RAG</p>
        </div>
      </div>
    </div>
  )
}
