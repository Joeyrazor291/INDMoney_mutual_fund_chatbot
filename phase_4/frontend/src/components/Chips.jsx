import React from 'react';

const CHIPS = [
    "Expense ratio",
    "Minimum SIP",
    "Exit load",
    "Lock-in period",
    "Capital gains download",
    "Riskometer"
];

export const Chips = ({ onChipClick }) => {
    return (
        <div className="animate-fade-in" style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginTop: '16px',
            marginBottom: '16px',
            padding: '0 4px'
        }}>
            <div style={{ width: '100%', marginBottom: '4px' }}>
                <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    paddingLeft: '4px'
                }}>
                    Suggested Questions
                </span>
            </div>
            {CHIPS.map((chip) => (
                <button
                    key={chip}
                    onClick={() => onChipClick(chip)}
                    style={{
                        padding: '8px 16px',
                        backgroundColor: '#FFFFFF',
                        border: '1px solid var(--border-dark)',
                        borderRadius: '12px',
                        fontSize: '12.5px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        e.currentTarget.style.borderColor = 'var(--brand-blue)';
                        e.currentTarget.style.color = 'var(--brand-blue)';
                        e.currentTarget.style.backgroundColor = 'rgba(0, 82, 204, 0.05)';
                    }}
                    onMouseOut={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border-dark)';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                        e.currentTarget.style.backgroundColor = '#FFFFFF';
                    }}
                >
                    {chip}
                </button>
            ))}
        </div>
    );
};
