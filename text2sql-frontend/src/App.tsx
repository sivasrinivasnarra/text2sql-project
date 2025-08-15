import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, Database, Upload, Play, Code } from 'lucide-react'

interface QueryResult {
  sql: string | null
  results: any[] | null
  explanation: string
  success: boolean
  error?: string
}

interface SampleQuery {
  queries: string[]
  success: boolean
}

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [sampleQueries, setSampleQueries] = useState<string[]>([])
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchSampleQueries()
  }, [])

  const fetchSampleQueries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sample-queries`)
      const data: SampleQuery = await response.json()
      if (data.success) {
        setSampleQueries(data.queries)
      }
    } catch (error) {
      console.error('Failed to fetch sample queries:', error)
    }
  }

  const handleQuery = async () => {
    if (!query.trim()) return

    setLoading(true)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      const data: QueryResult = await response.json()
      setResult(data)
    } catch (error) {
      setResult({
        sql: null,
        results: null,
        explanation: `Network error: ${error}`,
        success: false,
        error: String(error)
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadFile) return

    setUploadLoading(true)
    const formData = new FormData()
    formData.append('file', uploadFile)

    try {
      const response = await fetch(`${API_BASE_URL}/upload-csv`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (data.success) {
        alert('File uploaded successfully!')
        setUploadFile(null)
      } else {
        alert('Upload failed: ' + data.detail)
      }
    } catch (error) {
      alert('Upload failed: ' + error)
    } finally {
      setUploadLoading(false)
    }
  }

  const useSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900 flex items-center justify-center gap-2">
            <Database className="h-8 w-8 text-blue-600" />
            Text2SQL
          </h1>
          <p className="text-gray-600">Convert natural language to SQL queries</p>
        </div>

        {/* File Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Data
            </CardTitle>
            <CardDescription>
              Upload CSV files to add new data tables to the database
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Input
                type="file"
                accept=".csv"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="flex-1"
              />
              <Button 
                onClick={handleFileUpload} 
                disabled={!uploadFile || uploadLoading}
                className="flex items-center gap-2"
              >
                {uploadLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
                Upload
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Query Input Section */}
        <Card>
          <CardHeader>
            <CardTitle>Natural Language Query</CardTitle>
            <CardDescription>
              Enter your question in plain English and we'll convert it to SQL
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Show me all employees hired after 2018 making over $80k"
                className="flex-1"
                onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              />
              <Button 
                onClick={handleQuery} 
                disabled={loading || !query.trim()}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Query
              </Button>
            </div>

            {/* Sample Queries */}
            {sampleQueries.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Sample queries:</p>
                <div className="flex flex-wrap gap-2">
                  {sampleQueries.map((sampleQuery, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => useSampleQuery(sampleQuery)}
                    >
                      {sampleQuery}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <div className="space-y-4">
            {/* Status Alert */}
            <Alert className={result.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
              <AlertDescription className={result.success ? "text-green-800" : "text-red-800"}>
                {result.explanation}
              </AlertDescription>
            </Alert>

            {/* Generated SQL */}
            {result.sql && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Code className="h-5 w-5" />
                    Generated SQL
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{result.sql}</code>
                  </pre>
                </CardContent>
              </Card>
            )}

            {/* Query Results */}
            {result.results && result.results.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Results ({result.results.length} rows)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border border-gray-300">
                      <thead>
                        <tr className="bg-gray-100">
                          {Object.keys(result.results[0]).map((column) => (
                            <th key={column} className="border border-gray-300 px-4 py-2 text-left font-medium">
                              {column}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.results.map((row, index) => (
                          <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                            {Object.values(row).map((value, cellIndex) => (
                              <td key={cellIndex} className="border border-gray-300 px-4 py-2">
                                {String(value)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* No Results */}
            {result.results && result.results.length === 0 && (
              <Card>
                <CardContent className="text-center py-8 text-gray-500">
                  No results found for this query.
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
