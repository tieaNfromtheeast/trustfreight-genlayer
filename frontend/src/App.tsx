import { useState, useEffect } from 'react'
import { createClient } from 'genlayer-js'
import { studionet } from 'genlayer-js/chains'
import { AlertCircle, FileText, CheckCircle2, Truck, Navigation, Lock } from 'lucide-react'

function App() {
  const [account, setAccount] = useState<string>('')
  const [client, setClient] = useState<any>(null)
  
  // App state
  const [caseDetails, setCaseDetails] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [resolving, setResolving] = useState(false)
  const [error, setError] = useState('')
  
  const contractAddress = import.meta.env.VITE_CONTRACT_ADDRESS

  useEffect(() => {
    if (account) {
      const c = createClient({
        chain: studionet,
        account: account as `0x${string}`,
        provider: (window as any).ethereum
      })
      setClient(c)
    } else {
      const c = createClient({ chain: studionet })
      setClient(c)
    }
  }, [account])

  useEffect(() => {
    if (client && contractAddress) {
      fetchCaseDetails()
    }
  }, [client])

  const connectWallet = async () => {
    if ((window as any).ethereum) {
      try {
        const accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' })
        setAccount(accounts[0])
      } catch (err: any) {
        setError(err.message)
      }
    } else {
      setError("Please install MetaMask")
    }
  }

  const fetchCaseDetails = async () => {
    try {
      if (!contractAddress || contractAddress.includes('your_contract_address')) return;
      setLoading(true)
      const details = await client.readContract({
        address: contractAddress,
        functionName: 'get_details',
        args: []
      })
      setCaseDetails(details)
      setLoading(false)
    } catch (err: any) {
      console.error(err)
      setLoading(false)
    }
  }

  const submitEvidence = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!client || !account) return setError("Connect wallet first")
    
    const formData = new FormData(e.target as HTMLFormElement)
    try {
      setLoading(true)
      await client.connect("studionet")
      await client.writeContract({
        address: contractAddress,
        functionName: 'submit_evidence',
        args: [
          formData.get('tracking_url'),
          formData.get('weather_loc'),
          formData.get('incident'),
          formData.get('image')
        ],
        value: 0n
      })
      await fetchCaseDetails()
    } catch (err: any) {
      setError(err.message)
      setLoading(false)
    }
  }

  const resolveCase = async () => {
    if (!client || !account) return setError("Connect wallet first")
    try {
      setResolving(true)
      setError('')
      await client.connect("studionet")
      await client.writeContract({
        address: contractAddress,
        functionName: 'resolve',
        args: [],
        value: 0n
      })
      await fetchCaseDetails()
      setResolving(false)
    } catch (err: any) {
      setError(err.message)
      setResolving(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-slate-900 rounded-2xl border border-slate-800 shadow-xl">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <Truck className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">TrustFreight</h1>
              <p className="text-slate-400 text-sm">Intelligent Logistics Dispute Resolution on GenLayer</p>
            </div>
          </div>
          <div>
            {!account ? (
              <button onClick={connectWallet} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-all">
                Connect Wallet
              </button>
            ) : (
              <div className="px-4 py-2 bg-slate-800 rounded-xl border border-slate-700 text-sm font-mono text-slate-300">
                {account.slice(0,6)}...{account.slice(-4)}
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400 flex items-center space-x-3">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {!contractAddress || contractAddress.includes('your_contract') ? (
          <div className="p-8 bg-slate-900 rounded-2xl border border-slate-800 text-center space-y-4">
            <FileText className="w-12 h-12 text-slate-600 mx-auto" />
            <h2 className="text-xl font-semibold">Contract Not Configured</h2>
            <p className="text-slate-400">Please deploy the contract on GenLayer Studio and set VITE_CONTRACT_ADDRESS in .env</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Case Info Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center"><Navigation className="w-5 h-5 mr-2 text-indigo-400"/> Case Details</h3>
                {loading && !caseDetails ? (
                  <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-slate-800 rounded w-3/4"></div>
                    <div className="h-4 bg-slate-800 rounded w-1/2"></div>
                  </div>
                ) : caseDetails ? (
                  <div className="space-y-4 text-sm">
                    <div className="flex justify-between border-b border-slate-800 pb-2">
                      <span className="text-slate-500">Status</span>
                      <span className={`font-semibold ${caseDetails.status === 'RESOLVED' ? 'text-green-400' : 'text-amber-400'}`}>{caseDetails.status}</span>
                    </div>
                    <div className="flex justify-between border-b border-slate-800 pb-2">
                      <span className="text-slate-500">Goods</span>
                      <span className="text-slate-300 text-right max-w-[150px] truncate">{caseDetails.goods}</span>
                    </div>
                    <div className="flex justify-between border-b border-slate-800 pb-2">
                      <span className="text-slate-500">Value (GEN)</span>
                      <span className="text-slate-300 font-mono">{caseDetails.value.toString()}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">Failed to load case</p>
                )}
              </div>
            </div>

            {/* Main Action Area */}
            <div className="lg:col-span-2 space-y-6">
              {caseDetails?.status === 'OPEN' && (
                <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <h3 className="text-xl font-semibold mb-6 flex items-center"><FileText className="w-6 h-6 mr-3 text-blue-400"/> Submit Evidence</h3>
                  <form onSubmit={submitEvidence} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm text-slate-400">Tracking Log URL</label>
                        <input name="tracking_url" type="url" required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors" placeholder="https://..." />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm text-slate-400">Weather Location (Lat,Lon)</label>
                        <input name="weather_loc" type="text" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors" placeholder="e.g. 22.5,114.0" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm text-slate-400">Incident Description</label>
                      <textarea name="incident" required rows={3} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors" placeholder="Describe what happened..."></textarea>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm text-slate-400">Image Evidence URL</label>
                      <input name="image" type="url" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors" placeholder="https://..." />
                    </div>
                    <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-xl transition-all">
                      {loading ? 'Submitting...' : 'Submit Evidence'}
                    </button>
                  </form>
                </div>
              )}

              {caseDetails?.status === 'DISPUTED' && (
                <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8 text-center space-y-6">
                  <div className="mx-auto w-16 h-16 bg-indigo-500/20 rounded-full flex items-center justify-center">
                    <Lock className="w-8 h-8 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-semibold mb-2">Evidence Locked</h3>
                    <p className="text-slate-400 max-w-md mx-auto">Both parties have submitted their claims. The AI Validator network is ready to adjudicate the dispute.</p>
                  </div>
                  
                  {resolving && (
                     <div className="p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
                       <p className="text-indigo-400 font-medium flex items-center justify-center">
                         <span className="animate-spin mr-3">🌀</span>
                         Waiting for AI validator consensus, this takes longer than a normal transaction...
                       </p>
                     </div>
                  )}

                  <button 
                    onClick={resolveCase} 
                    disabled={resolving}
                    className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-xl transition-all w-full max-w-md"
                  >
                    Trigger AI Resolution
                  </button>
                </div>
              )}

              {caseDetails?.status === 'RESOLVED' && (
                <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8 space-y-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-teal-400"></div>
                  <div className="flex items-center space-x-4 mb-6">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                    <h3 className="text-2xl font-semibold">Case Resolved</h3>
                  </div>
                  
                  <div className="p-6 bg-slate-950 rounded-xl border border-slate-800 space-y-4">
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider">AI Validator Reason</h4>
                    <p className="text-slate-300 italic leading-relaxed border-l-2 border-emerald-500 pl-4">
                      "{caseDetails.reason || 'Funds have been disbursed based on AI consensus.'}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
