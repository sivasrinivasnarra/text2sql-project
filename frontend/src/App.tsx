import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Upload, Database, Search, FileText, AlertCircle, CheckCircle } from 'lucide-react'

interface QueryResult {
  sql: string
  results: Record<string, any>[]
  success: boolean
  error?: string
}

interface TableInfo {
  name: string
  columns: { name: string; type: string }[]
  sample_data: Record<string, any>[]
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [tables, setTables] = useState<TableInfo[]>([])
  const [sampleQueries, setSampleQueries] = useState<string[]>([])
  const [uploadStatus, setUploadStatus] = useState<string>('')

  useEffect(() => {
    fetchTables()
    fetchSampleQueries()
  }, [])

  const fetchTables = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tables`)
      const data = await response.json()
      setTables(data)
    } catch (error) {
      console.error('Error fetching tables:', error)
    }
  }

  const fetchSampleQueries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sample-queries`)
      const data = await response.json()
      setSampleQueries(data.queries)
    } catch (error) {
      console.error('Error fetching sample queries:', error)
    }
  }

  const executeQuery = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })
      const result = await response.json()
      setQueryResult(result)
    } catch (error) {
      setQueryResult({
        sql: '',
        results: [],
        success: false,
        error: 'Failed to connect to the server',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setUploadStatus('Uploading...')
      const response = await fetch(`${API_BASE_URL}/upload-csv`, {
        method: 'POST',
        body: formData,
      })
      const result = await response.json()
      
      if (response.ok) {
        setUploadStatus(`Successfully uploaded: ${result.table_name}`)
        fetchTables() // Refresh tables list
      } else {
        setUploadStatus(`Error: ${result.detail}`)
      }
    } catch (error) {
      setUploadStatus('Upload failed')
    }

    event.target.value = ''
  }

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Text2SQL Banking Application
          </h1>
          <p className="text-lg text-gray-600">
            Query your banking data using natural language
          </p>
        </div>

        <Tabs defaultValue="query" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="query" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Query Data
            </TabsTrigger>
            <TabsTrigger value="schema" className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              Database Schema
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Upload Data
            </TabsTrigger>
          </TabsList>

          <TabsContent value="query" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Natural Language Query</CardTitle>
                <CardDescription>
                  Enter your question in plain English and we'll convert it to SQL
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="e.g., Show all customers from New York with balance over $10000"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && executeQuery()}
                    className="flex-1"
                  />
                  <Button onClick={executeQuery} disabled={loading || !query.trim()}>
                    {loading ? 'Processing...' : 'Execute Query'}
                  </Button>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Sample Queries:</h4>
                  <div className="flex flex-wrap gap-2">
                    {sampleQueries.map((sample, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="cursor-pointer hover:bg-blue-100"
                        onClick={() => handleSampleQuery(sample)}
                      >
                        {sample}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {queryResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {queryResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    Query Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Generated SQL:</h4>
                    <div className="bg-gray-100 p-3 rounded-md font-mono text-sm">
                      {queryResult.sql}
                    </div>
                  </div>

                  {queryResult.success ? (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Results ({queryResult.results.length} rows):
                      </h4>
                      {queryResult.results.length > 0 ? (
                        <div className="border rounded-md overflow-auto max-h-96">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                {Object.keys(queryResult.results[0]).map((key) => (
                                  <TableHead key={key} className="font-medium">
                                    {key}
                                  </TableHead>
                                ))}
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {queryResult.results.map((row, index) => (
                                <TableRow key={index}>
                                  {Object.values(row).map((value, cellIndex) => (
                                    <TableCell key={cellIndex}>
                                      {value?.toString() || 'N/A'}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      ) : (
                        <p className="text-gray-500 italic">No results found</p>
                      )}
                    </div>
                  ) : (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {queryResult.error || 'Query execution failed'}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="schema" className="space-y-6">
            <div className="grid gap-6">
              {tables.map((table) => (
                <Card key={table.name}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Database className="w-5 h-5" />
                      {table.name}
                    </CardTitle>
                    <CardDescription>
                      Table structure and sample data
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Columns:</h4>
                      <div className="flex flex-wrap gap-2">
                        {table.columns.map((column) => (
                          <Badge key={column.name} variant="outline">
                            {column.name} ({column.type})
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {table.sample_data.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Sample Data:</h4>
                        <div className="border rounded-md overflow-auto">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                {Object.keys(table.sample_data[0]).map((key) => (
                                  <TableHead key={key} className="font-medium">
                                    {key}
                                  </TableHead>
                                ))}
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {table.sample_data.slice(0, 3).map((row, index) => (
                                <TableRow key={index}>
                                  {Object.values(row).map((value, cellIndex) => (
                                    <TableCell key={cellIndex}>
                                      {value?.toString() || 'N/A'}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="upload" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload CSV File
                </CardTitle>
                <CardDescription>
                  Upload a CSV file to create a new table in the database
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-lg font-medium text-gray-700">
                      Click to upload CSV file
                    </span>
                    <input
                      id="file-upload"
                      type="file"
                      accept=".csv"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                  <p className="text-sm text-gray-500 mt-2">
                    CSV files will be automatically converted to database tables
                  </p>
                </div>

                {uploadStatus && (
                  <Alert className={uploadStatus.includes('Error') ? 'border-red-200' : 'border-green-200'}>
                    <AlertDescription>{uploadStatus}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App
