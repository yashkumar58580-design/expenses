import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { Wallet, Plus, Search, Sun, Moon } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDark, setIsDark] = useState(true);

  // ✅ Data Fetch karne ka naya tarika
  const fetchTransactions = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .order('date', { ascending: false });
    
    if (error) console.log('Error:', error);
    else setTransactions(data || []);
    setLoading(false);
  };

  useEffect(() => { fetchTransactions(); }, []);

  // ✅ Data Add karne ka naya tarika
  const handleAdd = async (formData) => {
    const { error } = await supabase
      .from('transactions')
      .insert([formData]);
    
    if (error) alert(error.message);
    else fetchTransactions();
  };

  // ✅ Summary logic (Frontend par hi calculate kar rahe hain)
  const totalExpenses = transactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  
  const totalIncome = transactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);

  if (loading) return <div className="p-10 text-center text-white">Loading from Supabase...</div>;

  return (
    <div className={isDark ? "bg-slate-900 text-white min-h-screen" : "bg-white text-slate-900 min-h-screen"}>
      {/* Tera Design yahan aayega, bas transactions map kar dena */}
      <header className="p-6 border-b border-slate-800 flex justify-between">
         <h1 className="text-2xl font-bold flex gap-2"><Wallet/> Bhai Dashboard</h1>
         <button onClick={() => setIsDark(!isDark)}>{isDark ? <Sun/> : <Moon/>}</button>
      </header>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
         <div className="p-6 bg-slate-800 rounded-2xl">
            <p className="text-rose-400">Total Kharcha</p>
            <h2 className="text-3xl font-bold">₹{totalExpenses.toLocaleString()}</h2>
         </div>
         <div className="p-6 bg-slate-800 rounded-2xl">
            <p className="text-emerald-400">Total Kamai</p>
            <h2 className="text-3xl font-bold">₹{totalIncome.toLocaleString()}</h2>
         </div>
      </div>
    </div>
  );
}

export default App;