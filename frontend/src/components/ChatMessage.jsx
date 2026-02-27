// src/components/ChatMessage.jsx

function formatMessage(text) {
    if (!text) return '';
    return text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Numbered list items
        .replace(/^(\d+)\.\s/gm, '<span class="list-num">$1.</span> ')
        // Bullet list items with dash
        .replace(/^-\s(.+)/gm, '<span class="list-bullet">•</span> $1')
        // Line breaks
        .replace(/\n/g, '<br/>');
}

function formatTimestamp(ts) {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function ChatMessage({ message }) {
    const isUser = message.role === 'user';
    return (
        <div className={`message ${message.role}`}>
            <div className="message-avatar">
                {isUser ? '👨‍🌾' : '🤖'}
            </div>
            <div className="message-body">
                <div 
                    className="message-text"
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} 
                />
                {message.audioUrl && (
                    <audio controls src={message.audioUrl} className="message-audio" />
                )}
                {message.timestamp && (
                    <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                )}
            </div>
        </div>
    );
}

export default ChatMessage;
