import React from 'react';
import { Check, ChevronLeft, ChevronRight } from 'lucide-react';

const FUNDS = [
    { id: 'hdfc-flexi-cap', name: 'HDFC Flexi Cap', short: 'Flexi Cap', color: 'var(--fund-hdfc-flexi)' },
    { id: 'hdfc-mid-cap', name: 'HDFC Mid Cap', short: 'Mid Cap', color: 'var(--fund-hdfc-mid)' },
    { id: 'absl-quant', name: 'ABSL Quant', short: 'Quant', color: 'var(--fund-absl-quant)' },
    { id: 'absl-elss', name: 'ABSL ELSS', short: 'ELSS', color: 'var(--fund-absl-elss)' },
    { id: 'edelweiss-nifty-next-50', name: 'Edelweiss Nifty 50', short: 'Index', color: 'var(--fund-edelweiss)' },
];

export const FundSelector = ({ selectedFunds, onToggleFund, onSelectAll, onClearAll }) => {
    const scrollRef = React.useRef(null);

    const scroll = (direction) => {
        if (scrollRef.current) {
            const scrollAmount = 200;
            scrollRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    return (
        <div style={{
            borderBottom: '1px solid var(--border)',
            backgroundColor: '#FFFFFF',
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            flexShrink: 0
        }}>
            <span style={{
                fontSize: '11px',
                fontWeight: 800,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                whiteSpace: 'nowrap'
            }}>
                Funds
            </span>

            <div style={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 0, position: 'relative' }}>
                <button
                    onClick={() => scroll('left')}
                    style={{
                        padding: '4px',
                        backgroundColor: '#FFFFFF',
                        border: '1px solid var(--border)',
                        borderRadius: '50%',
                        cursor: 'pointer',
                        display: 'flex',
                        zIndex: 2,
                        marginRight: '8px'
                    }}
                >
                    <ChevronLeft size={14} />
                </button>

                <div
                    ref={scrollRef}
                    className="no-scrollbar"
                    style={{
                        display: 'flex',
                        gap: '10px',
                        overflowX: 'auto',
                        padding: '4px 2px',
                        flex: 1
                    }}
                >
                    {FUNDS.map((fund) => {
                        const isSelected = selectedFunds.includes(fund.id);
                        return (
                            <button
                                key={fund.id}
                                onClick={() => onToggleFund(fund.id)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '6px 14px',
                                    backgroundColor: isSelected ? 'rgba(0, 82, 204, 0.05)' : '#FFFFFF',
                                    border: `1.5px solid ${isSelected ? 'var(--brand-blue)' : 'var(--border-dark)'}`,
                                    borderRadius: '20px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    whiteSpace: 'nowrap'
                                }}
                            >
                                <span style={{
                                    fontSize: '13px',
                                    fontWeight: 700,
                                    color: isSelected ? 'var(--brand-blue)' : 'var(--text-primary)'
                                }}>
                                    {fund.name}
                                </span>
                                <span style={{
                                    fontSize: '10px',
                                    fontWeight: 600,
                                    backgroundColor: fund.color,
                                    color: '#FFFFFF',
                                    padding: '2px 8px',
                                    borderRadius: '10px',
                                    opacity: isSelected ? 1 : 0.7
                                }}>
                                    {fund.short}
                                </span>
                                {isSelected && <Check size={14} color="var(--brand-blue)" strokeWidth={3} />}
                            </button>
                        );
                    })}
                </div>

                <button
                    onClick={() => scroll('right')}
                    style={{
                        padding: '4px',
                        backgroundColor: '#FFFFFF',
                        border: '1px solid var(--border)',
                        borderRadius: '50%',
                        cursor: 'pointer',
                        display: 'flex',
                        zIndex: 2,
                        marginLeft: '8px'
                    }}
                >
                    <ChevronRight size={14} />
                </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
                <button
                    onClick={onSelectAll}
                    style={{
                        padding: '6px 12px',
                        backgroundColor: selectedFunds.length === FUNDS.length ? 'var(--brand-blue)' : 'transparent',
                        border: '1px solid var(--border-dark)',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: 700,
                        color: selectedFunds.length === FUNDS.length ? '#FFFFFF' : 'var(--brand-blue)',
                        cursor: 'pointer'
                    }}
                >
                    All
                </button>
                <button
                    onClick={onClearAll}
                    style={{
                        padding: '6px 12px',
                        backgroundColor: 'transparent',
                        border: '1px solid var(--border-dark)',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: 700,
                        color: 'var(--text-secondary)',
                        cursor: 'pointer'
                    }}
                >
                    Clear
                </button>
            </div>
        </div>
    );
};
