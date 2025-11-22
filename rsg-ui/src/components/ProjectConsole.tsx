import React, { useState, useRef, useEffect } from 'react';
import { sendProjectChat, ChatResponse } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  tokens?: { input: number; output: number; total: number };
  timestamp: Date;
}

interface ProjectConsoleProps {
  projectId: string;
}

const ProjectConsole: React.FC<ProjectConsoleProps> = ({ projectId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await sendProjectChat(projectId, input.trim());

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        model: response.model,
        tokens: response.tokens,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to get response. Please check your API key settings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatModel = (model: string) => {
    if (model.includes('sonnet')) return 'Sonnet 4.5';
    if (model.includes('haiku')) return 'Haiku 4.5';
    return model;
  };

  return (
    <div className="project-console">
      <div className="console-header">
        <h4>Orchestrator Console</h4>
        <span className="console-hint">Ask about this project or get help</span>
      </div>

      <div className="console-messages">
        {messages.length === 0 && (
          <div className="console-empty">
            <p>Ask the orchestrator about this project:</p>
            <ul>
              <li>"What should I do next?"</li>
              <li>"How do I add a new feature?"</li>
              <li>"What is the current status?"</li>
            </ul>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`console-message ${msg.role}`}>
            <div className="message-header">
              <span className="message-role">
                {msg.role === 'user' ? 'You' : 'Orchestrator'}
              </span>
              {msg.model && (
                <span className="message-model">{formatModel(msg.model)}</span>
              )}
            </div>
            <div className="message-content">{msg.content}</div>
            {msg.tokens && (
              <div className="message-tokens">
                {msg.tokens.total} tokens
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="console-message assistant loading">
            <div className="message-header">
              <span className="message-role">Orchestrator</span>
            </div>
            <div className="message-content">Thinking...</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="console-error">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="console-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Enter to send)"
          disabled={loading}
          rows={2}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ProjectConsole;
