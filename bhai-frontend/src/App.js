import React, { useState, useEffect } from 'react';
import { Wallet, Moon, Sun, Plus, X, Search, Sparkles, Calendar, Filter, Trash2 } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
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

  useEffect(() => {
    const elements = document.querySelectorAll('.stagger-animation');
    elements.forEach((el, index) => {
      setTimeout(() => {
        el.style.animation = 'fadeInUp 0.5s ease-out forwards';
        el.style.animationDelay = `${index * 0.1}s`;
      }, 100);
    });
  }, [transactions, searchTerm]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:8000/transactions');
      if (!response.ok) {
        throw new Error('Failed to fetch transactions');
      }
      const data = await response.json();
      setTransactions(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setTransactions(generateMockData());
    } finally {
      setLoading(false);
    }
  };

  const formatINR = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset all data? This will delete all transactions permanently.')) {
      return;
    }

    try {
      // Call backend reset endpoint (correct URL)
      const response = await fetch('http://127.0.0.1:8000/reset', {
        method: 'DELETE'
      });

      if (response.ok) {
        const result = await response.json();
        alert('✅ ' + result.message);
        // Clear frontend storage
        localStorage.clear();
        sessionStorage.clear();
        // Reload to show fresh state
        window.location.reload();
      } else {
        const error = await response.json();
        alert('❌ Failed to reset: ' + (error.detail || 'Unknown error'));
      }
    } catch (err) {
      alert('❌ Error: Could not connect to backend! Make sure backend is running on port 8000.');
      console.error(err);
    }
  };

  const handleDelete = async (transactionId) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) {
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/transactions/${transactionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Refresh transactions
        await fetchTransactions();
      } else {
        alert('Failed to delete transaction');
      }
    } catch (err) {
      alert('Error: Could not connect to backend!');
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://127.0.0.1:8000/transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          amount: parseFloat(formData.amount)
        })
      });

      if (response.ok) {
        setShowModal(false);
        setFormData({
          description: '',
          amount: '',
          date: new Date().toISOString().split('T')[0],
          category: 'Food & Dining',
          status: 'completed'
        });
        await fetchTransactions();
      } else {
        const errorData = await response.json();
        alert(`Failed to add transaction: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Error: Backend not running!`);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const generateMockData = () => ({
    summary: {
      totalBalance: 0.00,
      monthlyIncome: 0.00,
      totalExpenses: 0.00,
      balanceTrend: [0, 0, 0, 0],
      incomeTrend: [0, 0, 0, 0],
      expensesTrend: [0, 0, 0, 0]
    },
    categorySpending: [
      { name: 'Food & Dining', value: 0, color: '#10b981' },
      { name: 'Rent', value: 0, color: '#3b82f6' },
      { name: 'Transportation', value: 0, color: '#f59e0b' },
      { name: 'Entertainment', value: 0, color: '#8b5cf6' },
      { name: 'Utilities', value: 0, color: '#ec4899' },
      { name: 'Shopping', value: 0, color: '#06b6d4' }
    ],
    monthlyTrends: [
      { month: 'Jan', income: 0, expenses: 0 },
      { month: 'Feb', income: 0, expenses: 0 },
      { month: 'Mar', income: 0, expenses: 0 },
      { month: 'Apr', income: 0, expenses: 0 }
    ],
    recentTransactions: []
  });

  const data = transactions.summary ? transactions : generateMockData();

  // Calculate actual data from transactions if available
  const actualData = {
    summary: {
      totalBalance: 0,
      monthlyIncome: 0,
      totalExpenses: data.recentTransactions.reduce((sum, t) => sum + (t.amount < 0 ? Math.abs(t.amount) : 0), 0),
      balanceTrend: [0, 0, 0, 0],
      incomeTrend: [0, 0, 0, 0],
      expensesTrend: [0, 0, 0, 0]
    },
    categorySpending: data.categorySpending,
    monthlyTrends: data.monthlyTrends.map(() => ({ month: 'Jan', income: 0, expenses: 0 })),
    recentTransactions: data.recentTransactions
  };

  const displayData = data.recentTransactions.length > 0 ? data : actualData;

  const filteredTransactions = displayData.recentTransactions.filter(transaction => 
    transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.date.includes(searchTerm) ||
    transaction.status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-slate-900' : 'bg-slate-50'}`}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className={`text-lg font-medium ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen relative overflow-hidden ${isDark ? 'bg-slate-900' : 'bg-slate-50'}`}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600;700&display=swap');
        
        * { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Playfair Display', serif; letter-spacing: -0.02em; }
        
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-15px) rotate(3deg); }
        }
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
          33% { transform: translate(30px, -50px) scale(1.1) rotate(120deg); }
          66% { transform: translate(-20px, 20px) scale(0.9) rotate(240deg); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(100px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.4); }
          50% { box-shadow: 0 0 40px rgba(16, 185, 129, 0.7), 0 0 60px rgba(16, 185, 129, 0.3); }
        }
        @keyframes sparkle {
          0%, 100% { opacity: 0.3; transform: scale(0.8) rotate(0deg); }
          50% { opacity: 1; transform: scale(1.2) rotate(180deg); }
        }
        
        .animate-fadeInUp { animation: fadeInUp 0.6s ease-out forwards; }
        .animate-float { animation: float 4s ease-in-out infinite; }
        .animate-blob { animation: blob 10s ease-in-out infinite; }
        .animate-slideUp { animation: slideUp 0.5s ease-out forwards; }
        .animate-glow { animation: glow 2s ease-in-out infinite; }
        .animate-sparkle { animation: sparkle 3s ease-in-out infinite; }
        
        .card-hover {
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .card-hover:hover {
          transform: translateY(-12px) scale(1.02);
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.25);
        }
        .transaction-item {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .transaction-item:hover {
          transform: translateX(10px) scale(1.01);
        }
        .stagger-animation { opacity: 0; }
        
        .glass-effect {
          backdrop-filter: blur(20px) saturate(180%);
          -webkit-backdrop-filter: blur(20px) saturate(180%);
        }
        
        .luxury-border {
          position: relative;
        }
        .luxury-border::before {
          content: '';
          position: absolute;
          inset: -2px;
          border-radius: inherit;
          padding: 2px;
          background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0.05));
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          pointer-events: none;
        }
        
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { 
          background: linear-gradient(180deg, #667eea, #764ba2);
          border-radius: 10px;
        }
      `}</style>
      
      {/* Animated Background Blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className={`absolute top-20 left-1/4 rounded-full blur-3xl opacity-20 animate-blob ${isDark ? 'bg-purple-500' : 'bg-purple-400'}`} style={{width: '400px', height: '400px'}}></div>
        <div className={`absolute top-40 right-1/4 rounded-full blur-3xl opacity-20 animate-blob ${isDark ? 'bg-blue-500' : 'bg-blue-400'}`} style={{width: '350px', height: '350px', animationDelay: '2s'}}></div>
        <div className={`absolute bottom-20 left-1/3 rounded-full blur-3xl opacity-20 animate-blob ${isDark ? 'bg-rose-500' : 'bg-rose-400'}`} style={{width: '300px', height: '300px', animationDelay: '4s'}}></div>
      </div>
      <header className={`sticky top-0 z-50 glass-effect border-b luxury-border ${isDark ? 'bg-slate-900/90 border-slate-800/50' : 'bg-white/90 border-slate-200/50'}`}>
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-purple-500/20 animate-float relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/30 to-transparent blur-xl"></div>
              <Wallet className="w-7 h-7 text-emerald-500 relative z-10" />
            </div>
            <div>
              <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Expenses</h1>
              <p className={`text-xs font-semibold tracking-wider uppercase ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Financial Intelligence System</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleReset}
              className="px-5 py-2.5 rounded-xl font-bold text-sm transition-all hover:scale-105 active:scale-95 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 text-white shadow-lg shadow-rose-500/30"
            >
              <X className="w-4 h-4 inline mr-2" />
              Reset
            </button>

            <button
              onClick={() => setShowModal(true)}
              className="px-5 py-2.5 rounded-xl font-bold text-sm transition-all hover:scale-105 active:scale-95 animate-glow bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/30"
            >
              <Plus className="w-4 h-4 inline mr-2" />
              Add
            </button>
            
            <button
              onClick={() => setIsDark(!isDark)}
              className={`p-3 rounded-xl transition-all hover:scale-110 hover:rotate-180 active:scale-95 ${isDark ? 'bg-slate-800 shadow-lg' : 'bg-white shadow-lg'}`}
            >
              {isDark ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
            </button>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 animate-fadeInUp">
            <p className="text-amber-500 text-sm font-medium">⚠️ Backend unavailable. Showing demo data.</p>
          </div>
        )}

        <div className="max-w-4xl mx-auto mb-8 animate-fadeInUp">
          <div className={`p-10 rounded-3xl card-hover glass-effect relative overflow-hidden luxury-border ${isDark ? 'bg-slate-800/80 border-2 border-slate-700/50 shadow-2xl' : 'bg-white/90 border-2 border-slate-200/50 shadow-2xl'}`}>
            {/* Background Effects */}
            <div className={`absolute inset-0 opacity-10 ${isDark ? 'bg-gradient-to-br from-rose-500/40 via-purple-500/40 to-blue-500/40' : 'bg-gradient-to-br from-rose-300/50 via-purple-300/50 to-blue-300/50'}`}></div>
            <div className={`absolute -top-32 -right-32 rounded-full blur-3xl opacity-30 animate-blob ${isDark ? 'bg-rose-500' : 'bg-rose-400'}`} style={{width: '250px', height: '250px'}}></div>
            <div className={`absolute -bottom-32 -left-32 rounded-full blur-3xl opacity-30 animate-blob ${isDark ? 'bg-purple-500' : 'bg-purple-400'}`} style={{width: '250px', height: '250px', animationDelay: '2s'}}></div>
            <Sparkles className={`absolute top-6 right-6 w-6 h-6 opacity-40 animate-sparkle ${isDark ? 'text-yellow-400' : 'text-yellow-500'}`} />
            <Sparkles className={`absolute bottom-8 left-8 w-4 h-4 opacity-30 animate-sparkle ${isDark ? 'text-purple-400' : 'text-purple-500'}`} style={{animationDelay: '1.5s'}} />
            
            <div className="relative z-10 flex items-start justify-between gap-8">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <p className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Total Expenses</p>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-700 border border-rose-200'}`}>
                    {new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                  </span>
                </div>
                
                <p className={`text-6xl md:text-7xl font-bold mb-3 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {formatINR(displayData.summary.totalExpenses)}
                </p>
                
                <div className="flex items-center gap-3">
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    {displayData.recentTransactions.length} transactions recorded
                  </p>
                  <span className={`px-2 py-1 rounded-md text-xs font-bold ${
                    displayData.summary.totalExpenses < 5000 
                      ? isDark ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-700'
                      : displayData.summary.totalExpenses < 15000
                      ? isDark ? 'bg-amber-500/20 text-amber-400' : 'bg-amber-100 text-amber-700'
                      : isDark ? 'bg-rose-500/20 text-rose-400' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {displayData.summary.totalExpenses < 5000 ? 'Excellent' : displayData.summary.totalExpenses < 15000 ? 'Moderate' : 'High'}
                  </span>
                </div>

                {/* Mini Bar Chart */}
                <div className={`mt-6 p-4 rounded-2xl ${isDark ? 'bg-slate-900/50 backdrop-blur-sm' : 'bg-white/70 backdrop-blur-sm'}`}>
                  <div className="h-20 flex items-end justify-between gap-2">
                    {displayData.summary.expensesTrend.map((value, i) => {
                      const maxValue = Math.max(...displayData.summary.expensesTrend, 1);
                      const height = (value / maxValue) * 100;
                      return (
                        <div 
                          key={i} 
                          className="flex-1 bg-gradient-to-t from-rose-500 to-rose-400 rounded-t-lg transition-all hover:opacity-80 hover:scale-105"
                          style={{ height: `${height}%`, minHeight: '8px' }}
                        ></div>
                      );
                    })}
                  </div>
                </div>
              </div>
              
              {/* Emoji with luxury frame */}
              <div className="relative flex-shrink-0">
                <div className={`absolute inset-0 rounded-3xl blur-2xl animate-pulse ${
                  displayData.summary.totalExpenses === 0 ? 'bg-emerald-500/30' : 
                  displayData.summary.totalExpenses < 5000 ? 'bg-emerald-500/30' : 
                  displayData.summary.totalExpenses < 15000 ? 'bg-amber-500/30' : 'bg-rose-500/30'
                }`}></div>
                
                <div className={`relative p-8 rounded-3xl glass-effect ${isDark ? 'bg-slate-900/60 border-2 border-slate-700/50' : 'bg-white/70 border-2 border-slate-200/50'}`}>
                  <div className="text-7xl animate-float filter drop-shadow-2xl">
                    {displayData.summary.totalExpenses === 0 ? '😊' : 
                     displayData.summary.totalExpenses < 5000 ? '😊' : 
                     displayData.summary.totalExpenses < 15000 ? '😐' : '😢'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className={`p-8 rounded-3xl card-hover glass-effect luxury-border animate-fadeInUp ${isDark ? 'bg-slate-800/80 border-2 border-slate-700/50 shadow-xl' : 'bg-white/90 border-2 border-slate-200/50 shadow-xl'}`} style={{animationDelay: '0.2s'}}>
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Spending by Category</h2>
              <Filter className={`w-5 h-5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={displayData.categorySpending}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {displayData.categorySpending.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatINR(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className={`p-8 rounded-3xl card-hover glass-effect luxury-border animate-fadeInUp ${isDark ? 'bg-slate-800/80 border-2 border-slate-700/50 shadow-xl' : 'bg-white/90 border-2 border-slate-200/50 shadow-xl'}`} style={{animationDelay: '0.3s'}}>
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Monthly Trends</h2>
              <Calendar className={`w-5 h-5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={displayData.monthlyTrends}>
                <XAxis dataKey="month" stroke={isDark ? '#64748b' : '#94a3b8'} />
                <YAxis stroke={isDark ? '#64748b' : '#94a3b8'} />
                <Tooltip formatter={(value) => formatINR(value)} />
                <Bar dataKey="income" fill="#10b981" radius={[8, 8, 0, 0]} />
                <Bar dataKey="expenses" fill="#f43f5e" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={`p-8 rounded-3xl card-hover glass-effect luxury-border animate-fadeInUp ${isDark ? 'bg-slate-800/80 border-2 border-slate-700/50 shadow-xl' : 'bg-white/90 border-2 border-slate-200/50 shadow-xl'}`} style={{animationDelay: '0.4s'}}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Recent Transactions</h2>
              <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Track your financial activity</p>
            </div>
            
            <div className="relative w-full sm:w-72">
              <Search className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full pl-12 pr-4 py-3 rounded-xl border-2 font-medium transition-all ${
                  isDark ? 'bg-slate-900/60 border-slate-700/50 text-white placeholder-slate-400 focus:border-emerald-500' : 'bg-white/80 border-slate-200/50 text-slate-900 placeholder-slate-400 focus:border-emerald-500'
                } focus:outline-none focus:ring-2 focus:ring-emerald-500/30`}
              />
            </div>
          </div>

          {filteredTransactions.length === 0 ? (
            <div className={`text-center py-12 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-lg font-medium">No transactions found</p>
              <p className="text-sm mt-1">Try a different search term</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTransactions.map((transaction, index) => (
                <div
                  key={transaction.id}
                  className={`flex items-center justify-between p-5 rounded-2xl border transaction-item stagger-animation ${
                    isDark ? 'bg-slate-900/50 border-slate-700/30 hover:bg-slate-900/70' : 'bg-white/70 border-slate-200/40 hover:bg-white/90'
                  }`}
                  style={{animationDelay: `${index * 0.05}s`}}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all hover:scale-110 border-2 relative overflow-hidden ${
                      transaction.amount > 0
                        ? isDark ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-emerald-50 border-emerald-200/50'
                        : isDark ? 'bg-rose-500/10 border-rose-500/30' : 'bg-rose-50 border-rose-200/50'
                    }`}>
                      <span className="text-3xl relative z-10">{transaction.amount > 0 ? '😊' : '😢'}</span>
                      <div className={`absolute inset-0 blur-xl opacity-50 ${transaction.amount > 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                    </div>
                    <div>
                      <p className={`font-semibold text-base mb-1 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {transaction.description}
                      </p>
                      <div className="flex items-center gap-2">
                        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                          {transaction.date}
                        </p>
                        <span className={`${isDark ? 'text-slate-600' : 'text-slate-300'}`}>•</span>
                        <p className={`text-sm font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                          {transaction.category}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-4 py-1.5 rounded-xl text-xs font-bold uppercase tracking-wide border ${
                      transaction.status === 'completed'
                        ? isDark ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : isDark ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {transaction.status}
                    </span>
                    <p className={`font-bold text-xl ${transaction.amount > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                      {formatINR(transaction.amount)}
                    </p>
                    <button
                      onClick={() => handleDelete(transaction.id)}
                      className={`p-2 rounded-lg transition-all hover:scale-110 active:scale-95 ${
                        isDark ? 'hover:bg-rose-500/20 text-rose-400' : 'hover:bg-rose-100 text-rose-600'
                      }`}
                      title="Delete transaction"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className={`w-full max-w-lg rounded-3xl p-8 animate-slideUp glass-effect luxury-border relative overflow-hidden ${
            isDark ? 'bg-slate-800/95 border-2 border-slate-700/50 shadow-2xl' : 'bg-white/95 border-2 border-slate-200/50 shadow-2xl'
          }`}>
            {/* Decorative blobs */}
            <div className={`absolute -top-20 -right-20 rounded-full blur-3xl ${isDark ? 'bg-emerald-500/20' : 'bg-emerald-400/30'}`} style={{width: '160px', height: '160px'}}></div>
            <div className={`absolute -bottom-20 -left-20 rounded-full blur-3xl ${isDark ? 'bg-purple-500/20' : 'bg-purple-400/30'}`} style={{width: '160px', height: '160px'}}></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Add Transaction</h2>
                  <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Record your financial activity</p>
                </div>
                <button onClick={() => setShowModal(false)} className={`p-3 rounded-xl transition-all hover:scale-110 hover:rotate-90 ${isDark ? 'hover:bg-slate-700' : 'hover:bg-slate-100'}`}>
                  <X className={`w-6 h-6 ${isDark ? 'text-slate-400' : 'text-slate-600'}`} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className={`block text-sm font-bold mb-2 uppercase tracking-wide ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Description</label>
                  <input
                    type="text"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="e.g., Swiggy Order"
                    required
                    className={`w-full px-5 py-4 rounded-xl border-2 font-medium transition-all ${isDark ? 'bg-slate-900/60 border-slate-700/50 text-white placeholder-slate-400 focus:border-emerald-500' : 'bg-white/80 border-slate-200/50 text-slate-900 placeholder-slate-400 focus:border-emerald-500'} focus:outline-none focus:ring-2 focus:ring-emerald-500/30`}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-bold mb-2 uppercase tracking-wide ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Amount (₹)</label>
                    <input
                      type="number"
                      name="amount"
                      value={formData.amount}
                      onChange={handleChange}
                      placeholder="-500"
                      step="0.01"
                      required
                      className={`w-full px-5 py-4 rounded-xl border-2 font-bold transition-all ${isDark ? 'bg-slate-900/60 border-slate-700/50 text-white placeholder-slate-400 focus:border-emerald-500' : 'bg-white/80 border-slate-200/50 text-slate-900 placeholder-slate-400 focus:border-emerald-500'} focus:outline-none focus:ring-2 focus:ring-emerald-500/30`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-bold mb-2 uppercase tracking-wide ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Date</label>
                    <input
                      type="date"
                      name="date"
                      value={formData.date}
                      onChange={handleChange}
                      required
                      className={`w-full px-5 py-4 rounded-xl border-2 font-medium transition-all ${isDark ? 'bg-slate-900/60 border-slate-700/50 text-white focus:border-emerald-500' : 'bg-white/80 border-slate-200/50 text-slate-900 focus:border-emerald-500'} focus:outline-none focus:ring-2 focus:ring-emerald-500/30`}
                    />
                  </div>
                </div>

                <div>
                  <label className={`block text-sm font-bold mb-2 uppercase tracking-wide ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Category</label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    required
                    className={`w-full px-5 py-4 rounded-xl border-2 font-medium transition-all ${isDark ? 'bg-slate-900/60 border-slate-700/50 text-white focus:border-emerald-500' : 'bg-white/80 border-slate-200/50 text-slate-900 focus:border-emerald-500'} focus:outline-none focus:ring-2 focus:ring-emerald-500/30`}
                  >
                    <option>Food & Dining</option>
                    <option>Rent</option>
                    <option>Transportation</option>
                    <option>Entertainment</option>
                    <option>Utilities</option>
                    <option>Shopping</option>
                    <option>Income</option>
                    <option>Health</option>
                    <option>Education</option>
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-bold mb-3 uppercase tracking-wide ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Status</label>
                  <div className="flex gap-4">
                    <label className={`flex items-center gap-3 px-5 py-3 rounded-xl border-2 flex-1 cursor-pointer transition-all ${
                      formData.status === 'completed' 
                        ? isDark ? 'bg-emerald-500/20 border-emerald-500/50' : 'bg-emerald-50 border-emerald-500' 
                        : isDark ? 'bg-slate-900/30 border-slate-700/30 hover:border-slate-600' : 'bg-white/50 border-slate-200 hover:border-slate-300'
                    }`}>
                      <input type="radio" name="status" value="completed" checked={formData.status === 'completed'} onChange={handleChange} className="w-5 h-5" />
                      <span className={`font-bold ${formData.status === 'completed' ? (isDark ? 'text-emerald-400' : 'text-emerald-700') : (isDark ? 'text-slate-300' : 'text-slate-700')}`}>Completed</span>
                    </label>
                    <label className={`flex items-center gap-3 px-5 py-3 rounded-xl border-2 flex-1 cursor-pointer transition-all ${
                      formData.status === 'pending' 
                        ? isDark ? 'bg-amber-500/20 border-amber-500/50' : 'bg-amber-50 border-amber-500' 
                        : isDark ? 'bg-slate-900/30 border-slate-700/30 hover:border-slate-600' : 'bg-white/50 border-slate-200 hover:border-slate-300'
                    }`}>
                      <input type="radio" name="status" value="pending" checked={formData.status === 'pending'} onChange={handleChange} className="w-5 h-5" />
                      <span className={`font-bold ${formData.status === 'pending' ? (isDark ? 'text-amber-400' : 'text-amber-700') : (isDark ? 'text-slate-300' : 'text-slate-700')}`}>Pending</span>
                    </label>
                  </div>
                </div>

                <div className={`p-4 rounded-xl text-sm font-medium border ${isDark ? 'bg-blue-500/10 text-blue-300 border-blue-500/20' : 'bg-blue-50 text-blue-700 border-blue-200'}`}>
                  💡 Tip: Use negative (-) for expenses, positive (+) for income
                </div>

                <div className="flex gap-4 pt-2">
                  <button type="button" onClick={() => setShowModal(false)} className={`flex-1 px-6 py-4 rounded-xl font-bold transition-all hover:scale-105 active:scale-95 ${isDark ? 'bg-slate-700 hover:bg-slate-600 text-white shadow-lg' : 'bg-slate-200 hover:bg-slate-300 text-slate-900 shadow-lg'}`}>
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 px-6 py-4 rounded-xl font-bold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white transition-all hover:scale-105 active:scale-95 shadow-lg shadow-emerald-500/30">
                    Add Transaction
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
