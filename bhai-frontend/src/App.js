import React, { useState, useEffect } from 'react';
import { Wallet, Moon, Sun, Plus, X, Search, Sparkles, Calendar, Filter, Trash2 } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  // ✅ FIXED: Vercel par relative path use karna zaroori hai
  // Ye apne aap Vercel ke /api/index.py ko call karega
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
      // ✅ FIXED: Fetching from Vercel Backend
      const response = await fetch(`${API_URL}/transactions`);
      
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

  // ... (Baaki poora formatting aur helper code wahi rahega jo tune diya hai)
  // ... (Bas API_URL wala change sabse zaroori tha)

  const formatINR = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure?')) return;
    try {
      const response = await fetch(`${API_URL}/reset`, { method: 'DELETE' });
      if (response.ok) window.location.reload();
    } catch (err) { alert('❌ Error connecting to backend!'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this?')) return;
    try {
      const response = await fetch(`${API_URL}/transactions/${id}`, { method: 'DELETE' });
      if (response.ok) fetchTransactions();
    } catch (err) { alert('❌ Error!'); }
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
    } catch (err) { alert('❌ Backend Error!'); }
  };

  // --- MOCK DATA GENERATOR ---
  const generateMockData = () => ({
    summary: { totalBalance: 0, monthlyIncome: 0, totalExpenses: 0, balanceTrend: [0,0,0,0], incomeTrend: [0,0,0,0], expensesTrend: [0,0,0,0] },
    categorySpending: [], monthlyTrends: [], recentTransactions: []
  });

  const data = transactions.summary ? transactions : generateMockData();
  const displayData = data.recentTransactions.length > 0 ? data : generateMockData();

  const filteredTransactions = (displayData.recentTransactions || []).filter(t => 
    t.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white text-2xl font-bold">Loading Financial Data...</div>;

  return (
    <div className={`min-h-screen relative overflow-hidden ${isDark ? 'bg-slate-900' : 'bg-slate-50'}`}>
      {/* 🎨 TERA DESIGN EK DUM PERFECT HAI ISLIYE MAINE UI MEI KOI CHANGE NAHI KIYA */}
      {/* ... (Tera poora JSX code yahan aayega) ... */}
      
      {/* Sirf ek reminder: jahan error alert hai, wahan backend status dikh raha hai */}
      {error && (
        <div className="fixed bottom-4 right-4 p-4 bg-rose-500 text-white rounded-xl shadow-2xl animate-bounce">
          ⚠️ Connection Issue: Using Local Cache
        </div>
      )}

      {/* TERA POORA RETURN CODE YAHAN PASTE KAR DE */}
      <div className="p-10 text-white text-center">
         <h1>Expenses Dashboard - Vercel Edition</h1>
         <p>Status: {error ? "Demo Mode" : "Connected to MongoDB"}</p>
         {/* ... Tera poora GUI ... */}
      </div>
    </div>
  );
}

export default App;