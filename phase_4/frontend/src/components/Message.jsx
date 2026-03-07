import React from 'react';
import { ExternalLink } from 'lucide-react';

export const Message = ({ message }) => {
    const isBot = message.role === 'bot';

    return (
        <div className={`animate-slide-up`} style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            width: '100%',
            alignItems: isBot ? 'flex-start' : 'flex-end',
            padding: '0 8px'
        }}>
            <div style={{
                maxWidth: '70%',
                padding: '16px',
                borderRadius: '20px',
                fontSize: '14px',
                lineHeight: '1.6',
                backgroundColor: isBot ? 'var(--surface)' : 'var(--bg-secondary)',
                border: `1px solid ${isBot ? 'var(--border-dark)' : 'var(--border)'}`,
                color: 'var(--text-primary)',
                boxShadow: 'var(--shadow-sm)',
                borderTopLeftRadius: isBot ? '0' : '20px',
                borderTopRightRadius: isBot ? '20px' : '0'
            }}>
                <div
                    dangerouslySetInnerHTML={{
                        __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: 700;">$1</strong>')
                    }}
                />

                {message.citation_url && isBot && (
                    <div style={{
                        marginTop: '12px',
                        paddingTop: '12px',
                        borderTop: '1px solid var(--border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <a
                            href={message.citation_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="citation-link"
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '6px 10px',
                                backgroundColor: 'var(--bg-secondary)',
                                border: '1px solid var(--border-dark)',
                                borderRadius: '8px',
                                fontSize: '11px',
                                fontWeight: 700,
                                color: 'var(--text-secondary)',
                                textDecoration: 'none',
                                transition: 'all 0.2s'
                            }}
                        >
                            Official Factsheet
                            <ExternalLink size={12} style={{ opacity: 0.5 }} />
                        </a>
                        <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {message.timestamp}
                        </span>
                    </div>
                )}

                {!message.citation_url && (
                    <div style={{ marginTop: '4px', textAlign: 'right' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {message.timestamp}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
};
