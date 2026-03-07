import React, { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

export const Input = ({ value, onChange, onSend, disabled }) => {
    const textareaRef = useRef(null);

    const handleSubmit = (e) => {
        e?.preventDefault();
        if (value.trim() && !disabled) {
            onSend();
        }
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [value]);

    return (
        <div style={{
            width: '100%',
            display: 'flex',
            alignItems: 'flex-end',
            gap: '12px',
            padding: '16px',
            backgroundColor: '#FFFFFF',
            borderTop: '1px solid var(--border)'
        }}>
            <form
                onSubmit={handleSubmit}
                style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'flex-end',
                    gap: '8px',
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-dark)',
                    borderRadius: '12px',
                    padding: '8px 16px',
                    transition: 'all 0.2s'
                }}
                onFocusCapture={(e) => e.currentTarget.style.borderColor = 'var(--brand-blue)'}
                onBlurCapture={(e) => e.currentTarget.style.borderColor = 'var(--border-dark)'}
            >
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit();
                        }
                    }}
                    placeholder="Ask about expense ratios, SIP amounts..."
                    style={{
                        flex: 1,
                        backgroundColor: 'transparent',
                        border: 'none',
                        padding: '8px 0',
                        fontSize: '14px',
                        fontWeight: 500,
                        lineHeight: '1.6',
                        color: 'var(--text-primary)',
                        outline: 'none',
                        resize: 'none',
                        height: '36px',
                        maxHeight: '120px'
                    }}
                    disabled={disabled}
                    rows={1}
                />
            </form>

            <button
                type="submit"
                disabled={!value.trim() || disabled}
                onClick={handleSubmit}
                style={{
                    height: '44px',
                    padding: '0 24px',
                    backgroundColor: value.trim() && !disabled ? 'var(--brand-navy)' : 'var(--bg-secondary)',
                    color: value.trim() && !disabled ? '#FFFFFF' : 'var(--text-muted)',
                    border: 'none',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: 700,
                    cursor: value.trim() && !disabled ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s',
                    boxShadow: value.trim() && !disabled ? 'var(--shadow-sm)' : 'none'
                }}
            >
                Send
                <Send size={16} />
            </button>
        </div>
    );
};
