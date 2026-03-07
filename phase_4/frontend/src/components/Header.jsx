import React from 'react';
import { RotateCcw } from 'lucide-react';

export const Header = ({ messageCount, onReset }) => {
    return (
        <header style={{
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            backgroundColor: 'var(--brand-navy)',
            color: '#FFFFFF',
            flexShrink: 0,
            zIndex: 10
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{
                    width: '40px',
                    height: '40px',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <polygon points="12,2 14.9,9.3 22.5,9.3 16.6,14.1 18.8,21.5 12,17 5.2,21.5 7.4,14.1 1.5,9.3 9.1,9.3" fill="#0052CC" />
                    </svg>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h1 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.02em' }}>INDmoney</h1>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            backgroundColor: 'rgba(0, 179, 134, 0.15)',
                            padding: '3px 8px',
                            borderRadius: '12px'
                        }}>
                            <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#00B386' }} />
                            <span style={{ fontSize: '10px', fontWeight: 700, color: '#00B386' }}>Live</span>
                        </div>
                    </div>
                    <p style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.6)', fontWeight: 500 }}>
                        Mutual Fund Assistant
                    </p>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.5)' }}>
                    {messageCount} messages
                </span>

                <button
                    onClick={onReset}
                    className="new-chat-btn"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 18px',
                        backgroundColor: 'rgba(255, 255, 255, 0.08)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '10px',
                        fontSize: '13px',
                        fontWeight: 700,
                        color: '#FFFFFF',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                >
                    <RotateCcw size={14} />
                    New chat
                </button>
            </div>
        </header>
    );
};
