import React, { useState, useEffect } from 'react';
import { Wallet, Moon, Sun, Plus, X, Search, Sparkles, Calendar, Filter, Trash2 } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  // ✅ Vercel friendly URL
  const API_URL = "/api"; 

  const [isDark, setIsDark] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    category: 'Food & Dining',
    status: 'completed'
  });

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/transactions`);
      if (!response.ok) throw new Error('Backend error');
      const data = await response.json();
      setTransactions(data);
      setError(null);
    } catch (err) {
      setError("Backend Unavailable");
      setTransactions(generateMockData());
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = () => ({
    summary: { totalBalance: 0, monthlyIncome: 0, totalExpenses: 0, balanceTrend: [0,0,0,0], incomeTrend: [0,0,0,0], expensesTrend: [0,0,0,0] },
    categorySpending: [], monthlyTrends: [], recentTransactions: []
  });

  const displayData = transactions.summary ? transactions : generateMockData();

  const filteredTransactions = (displayData.recentTransactions || []).filter(t => 
    t.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatINR = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, amount: parseFloat(formData.amount) })
      });
      if (response.ok) {
        setShowModal(false);
        fetchTransactions();
      }
    } catch (err) { alert('❌ Push Failed!'); }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  return (
    <div className={`min-h-screen relative overflow-hidden ${isDark ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-900'}`}>
      
      {/* Header */}
      <header className="p-6 flex justify-between items-center border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Wallet className="text-emerald-500 w-8 h-8" />
          <h1 className="text-2xl font-bold">Bhai Expenses</h1>
        </div>
        <div className="flex gap-4">
          <button onClick={() => setShowModal(true)} className="bg-emerald-500 px-4 py-2 rounded-xl font-bold text-white flex items-center gap-2">
            <Plus size={20}/> Add Transaction
          </button>
          <button onClick={() => setIsDark(!isDark)} className="p-2 bg-slate-800 rounded-xl">
            {isDark ? <Sun /> : <Moon />}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Status Banner */}
        {error && (
          <div className="mb-6 p-4 bg-rose-500/20 border border-rose-500 rounded-xl text-rose-500 text-center">
            ⚠️ Backend Unavailable (Check MongoDB Connection or Vercel Logs)
          </div>
        )}

        {/* Total Summary Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="p-8 rounded-3xl bg-slate-800 border border-slate-700 shadow-xl">
            <p className="text-slate-400 font-bold uppercase text-xs mb-2">Total Expenses</p>
            <h2 className="text-4xl font-bold text-rose-500">{formatINR(displayData.summary.totalExpenses)}</h2>
          </div>
          <div className="p-8 rounded-3xl bg-slate-800 border border-slate-700 shadow-xl">
            <p className="text-slate-400 font-bold uppercase text-xs mb-2">Monthly Income</p>
            <h2 className="text-4xl font-bold text-emerald-500">{formatINR(displayData.summary.monthlyIncome)}</h2>
          </div>
          <div className="p-8 rounded-3xl bg-slate-800 border border-slate-700 shadow-xl">
            <p className="text-slate-400 font-bold uppercase text-xs mb-2">Total Balance</p>
            <h2 className="text-4xl font-bold text-blue-500">{formatINR(displayData.summary.totalBalance)}</h2>
          </div>
        </div>

        {/* Transactions List */}
        <div className="bg-slate-800 rounded-3xl p-6 border border-slate-700">
           <div className="flex justify-between items-center mb-6">
             <h2 className="text-xl font-bold">Recent Activity</h2>
             <div className="relative">
                <Search className="absolute left-3 top-2.5 text-slate-500" size={18}/>
                <input 
                  type="text" 
                  placeholder="Search description..." 
                  className="bg-slate-900 border border-slate-700 pl-10 pr-4 py-2 rounded-xl focus:outline-none focus:border-emerald-500"
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
             </div>
           </div>

           <div className="space-y-4">
             {filteredTransactions.map((t) => (
               <div key={t.id} className="flex justify-between items-center p-4 bg-slate-900/50 rounded-2xl border border-slate-700/50">
                  <div className="flex gap-4 items-center">
                    <div className={`p-3 rounded-xl ${t.amount > 0 ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                      {t.amount > 0 ? '💰' : '💸'}
                    </div>
                    <div>
                      <p className="font-bold">{t.description}</p>
                      <p className="text-sm text-slate-500">{t.date} • {t.category}</p>
                    </div>
                  </div>
                  <p className={`text-lg font-bold ${t.amount > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    {formatINR(t.amount)}
                  </p>
               </div>
             ))}
             {filteredTransactions.length === 0 && <p className="text-center text-slate-500 py-10">No transactions found.</p>}
           </div>
        </div>
      </main>

      {/* Modal logic yahan bhi kaam karega... */}
    </div>
  );
}

export default App;