import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Message } from './components/Message';
import { Chips } from './components/Chips';
import { Input } from './components/Input';
import { FundSelector } from './components/FundSelector';

const INITIAL_MESSAGE = {
  id: "welcome",
  role: "bot",
  isInitial: true,
  content: "Hello! I'm the **INDmoney MF Assistant**. Select the funds you want to explore above, then ask me anything — expense ratios, SIP amounts, exit loads, lock-in periods, benchmarks, or capital gains statements.",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

const FUND_MAP = {
  'hdfc-flexi-cap': 'HDFC Flexi Cap',
  'hdfc-mid-cap': 'HDFC Mid Cap',
  'absl-quant': 'ABSL Quant',
  'absl-elss': 'ABSL ELSS',
  'edelweiss-nifty-next-50': 'Edelweiss Nifty Next 50'
};

function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [selectedFunds, setSelectedFunds] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleToggleFund = (id) => {
    // If it's already the only one selected, we toggle it off (clear).
    // Otherwise, we select ONLY this fund.
    setSelectedFunds(prev =>
      prev.length === 1 && prev[0] === id ? [] : [id]
    );
  };

  const handleSelectAll = () => {
    setSelectedFunds(Object.keys(FUND_MAP));
  };

  const handleClearAll = () => {
    setSelectedFunds([]);
  };

  const handleSend = async (query) => {
    if (!query.trim() || loading) return;

    // Enrich query with selected fund context
    let enrichedQuery = query;
    if (selectedFunds.length > 0) {
      const fundContext = selectedFunds.map(id => FUND_MAP[id]).join(", ");
      enrichedQuery = `${query} (Focus funds: ${fundContext})`;
    }

    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: query, // Keep original query for UI display
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await fetch("https://indmoney-backend-production.up.railway.app/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: enrichedQuery }),
      });

      if (response.ok) {
        const data = await response.json();
        const botMsg = {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: data.answer,
          citation_url: data.citation_url,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, botMsg]);
      } else {
        throw new Error("Failed to fetch");
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: "I'm having trouble connecting to the knowledge base. Please ensure the backend is running.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
      setInput(""); // Clear input after sending
    }
  };

  const handleReset = () => {
    setMessages([INITIAL_MESSAGE]);
    setSelectedFunds([]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: 'var(--bg-main)' }}>
      <Header
        messageCount={messages.length - 1}
        onReset={handleReset}
      />

      <FundSelector
        selectedFunds={selectedFunds}
        onToggleFund={handleToggleFund}
        onSelectAll={handleSelectAll}
        onClearAll={handleClearAll}
      />

      {/* Main Chat Area */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '0 16px' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px', padding: '24px 0 100px 0' }}>

          {messages.map((msg) => (
            <React.Fragment key={msg.id}>
              <Message message={msg} />

              {/* Placement of chips after welcome message IF no user messages exist yet */}
              {msg.isInitial && messages.length === 1 && (
                <div style={{ padding: '0 8px' }}>
                  <Chips onChipClick={(text) => setInput(text)} />
                </div>
              )}
            </React.Fragment>
          ))}

          {loading && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '0 16px', width: '60%' }}>
              <div style={{ height: '14px', width: '120px', backgroundColor: 'var(--border)', borderRadius: '4px' }} />
              <div style={{ height: '80px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '20px', borderTopLeftRadius: '0' }} />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <div style={{ width: '100%', borderTop: '1px solid var(--border)', backgroundColor: '#FFFFFF' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <Input
            value={input}
            onChange={setInput}
            onSend={() => handleSend(input)}
            disabled={loading}
          />

          <p style={{ textAlign: 'center', padding: '12px 0', fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', opacity: 0.7 }}>
            Facts only • No investment advice • Sourced from INDmoney.com • Always verify before investing
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
