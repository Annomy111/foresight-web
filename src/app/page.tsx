'use client';

import { useState } from 'react';
import { AVAILABLE_MODELS } from '@/lib/types';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

export default function Home() {
  const [question, setQuestion] = useState('');
  const [definition, setDefinition] = useState('');
  const [timeframe, setTimeframe] = useState('2026');
  const [iterations, setIterations] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);


  const startForecast = async () => {
    if (!question) {
      toast.error('Please enter a question');
      return;
    }

    setIsLoading(true);
    setResult(null);
    try {
      const response = await fetch('/.netlify/functions/forecast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          definition,
          timeframe,
          iterations
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setResult(data);
      toast.success('Forecast completed!');
    } catch (error) {
      toast.error('Failed to generate forecast');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-white">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto px-6 py-12"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mb-6">
            <div className="w-8 h-8 mx-auto bg-black rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">F</span>
            </div>
          </div>
          <h1 className="text-2xl font-medium text-black mb-2">
            Foresight Analyzer
          </h1>
          <p className="text-gray-600 text-sm">
            AI-powered probabilistic forecasting
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
          {!result ? (
            <>
              {/* Forecast Form */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Forecast Question
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-black focus:border-transparent resize-none"
                    rows={3}
                    placeholder="e.g., Will there be a ceasefire agreement between Russia and Ukraine by March 31, 2026?"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Definition (Optional)
                  </label>
                  <textarea
                    value={definition}
                    onChange={(e) => setDefinition(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-black focus:border-transparent resize-none"
                    rows={2}
                    placeholder="Clarify what counts as resolution..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timeframe
                    </label>
                    <input
                      type="text"
                      value={timeframe}
                      onChange={(e) => setTimeframe(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-black focus:border-transparent"
                      placeholder="2026"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Iterations: {iterations}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={iterations}
                      onChange={(e) => setIterations(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                </div>


                <button
                  onClick={startForecast}
                  disabled={isLoading || !question}
                  className="w-full py-3 bg-black text-white rounded-md hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Generating forecast...' : 'Generate Forecast'}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Forecast Results */}
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-black">Forecast Result</h2>
                  <div className="flex gap-3">
                    <button
                      onClick={async () => {
                        try {
                          // Call the backend Excel export endpoint
                          const response = await fetch(`https://foresight-backend-api.onrender.com/api/forecast/${result.result.forecast_id || 'current'}/excel`);

                          if (response.ok) {
                            // Create blob from response
                            const blob = await response.blob();

                            // Create download link
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `foresight_analysis_${new Date().toISOString().split('T')[0]}.xlsx`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            window.URL.revokeObjectURL(url);

                            toast.success('Excel report downloaded!');
                          } else {
                            toast.error('Failed to generate Excel report');
                          }
                        } catch (error) {
                          console.error('Download error:', error);
                          toast.error('Error downloading Excel report');
                        }
                      }}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                    >
                      Download Excel
                    </button>
                    <button
                      onClick={() => setResult(null)}
                      className="text-sm text-gray-500 hover:text-black"
                    >
                      New Forecast
                    </button>
                  </div>
                </div>

                {result.success && result.result && (
                  <div className="space-y-4">
                    <div className="text-center p-6 bg-gray-50 rounded-lg">
                      <div className="text-3xl font-semibold text-black mb-2">
                        {result.result.ensemble_probability?.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">
                        Ensemble Probability
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Models Used:</span>{' '}
                        <span className="text-black">{result.result.statistics?.models_used?.length || 0}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Successful Queries:</span>{' '}
                        <span className="text-black">{result.result.statistics?.successful_queries || 0}</span>
                      </div>
                    </div>

                    {result.result.statistics?.model_stats && (
                      <div className="mt-6">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">Model Breakdown</h3>
                        <div className="space-y-2">
                          {Object.entries(result.result.statistics.model_stats).map(([model, stats]: [string, any]) => (
                            <div key={model} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded text-sm">
                              <span className="text-gray-700">{model.split('/').pop()}</span>
                              <span className="text-black font-medium">{stats.mean?.toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {!result.success && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 text-sm">{result.error || 'Failed to generate forecast'}</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-xs text-gray-400">
          <p>Powered by ensemble forecasting with multiple AI models</p>
        </div>
      </motion.div>
    </div>
  );
}