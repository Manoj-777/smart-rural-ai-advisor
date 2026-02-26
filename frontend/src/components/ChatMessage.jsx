// src/components/ChatMessage.jsx

function ChatMessage({ message }) {
    return (
        <div className={`message ${message.role}`}>
            <div dangerouslySetInnerHTML={{ 
                __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                       .replace(/\n/g, '<br/>') 
            }} />
            {message.audioUrl && (
                <audio controls src={message.audioUrl} style={{ marginTop: '8px', width: '100%' }} />
            )}
        </div>
    );
}

export default ChatMessage;
