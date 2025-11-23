import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { projectChat } from '../api/client';
import { ChatMessage } from '../api/types';

interface ProjectConsoleProps {
  projectId: string;
  onOpenArtifact?: (artifactId: string) => void;
}

interface ConsoleMessage extends ChatMessage {
  type?: 'user' | 'command' | 'assistant' | 'error' | 'help' | 'artifact-preview';
  artifactPreview?: {
    name: string;
    content: string;
    contentType: string;
  };
}

const ProjectConsole: React.FC<ProjectConsoleProps> = ({ projectId, onOpenArtifact }) => {
  const [messages, setMessages] = useState<ConsoleMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Command chips for quick access
  const commandChips = [
    '/help',
    '/app-plan',
    '/app-scaffold',
    '/new-feature "title"',
    '/list-features',
    '/plan-phase planning',
    '/run-phase development',
  ];

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle inserting a command chip into the input
  const handleInsertCommand = (command: string) => {
    setInputValue(command);
    textareaRef.current?.focus();
  };

  // Parse artifact references from text and make them clickable
  const parseArtifactRefs = (text: string): React.ReactNode[] => {
    // Match artifact IDs like "ART-xxx" or UUID patterns
    const artifactPattern = /(ART-[a-zA-Z0-9]+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/g;
    const parts = text.split(artifactPattern);

    return parts.map((part, index) => {
      if (artifactPattern.test(part)) {
        return (
          <span
            key={index}
            className="artifact-ref"
            onClick={() => onOpenArtifact?.(part)}
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // Handle sending a message
  const handleSend = async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || isLoading) return;

    const isCommand = trimmedInput.startsWith('/');

    // Add user message
    const userMessage: ConsoleMessage = {
      role: 'user',
      content: trimmedInput,
      type: isCommand ? 'command' : 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await projectChat(projectId, trimmedInput);

      // Check if this is a help response
      const isHelpResponse = trimmedInput === '/help';

      // Check if response contains artifact preview data
      let artifactPreview = undefined;
      if (response.reply.includes('"content":') && response.reply.includes('"content_type":')) {
        try {
          const parsed = JSON.parse(response.reply);
          if (parsed.content && parsed.content_type) {
            artifactPreview = {
              name: parsed.name || 'Preview',
              content: parsed.content,
              contentType: parsed.content_type,
            };
          }
        } catch {
          // Not JSON, use as regular reply
        }
      }

      const assistantMessage: ConsoleMessage = {
        role: 'assistant',
        content: response.reply,
        model: response.model,
        tokens: response.tokens,
        agent: response.agent,
        type: isHelpResponse ? 'help' : artifactPreview ? 'artifact-preview' : 'assistant',
        artifactPreview,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ConsoleMessage = {
        role: 'assistant',
        content: 'Something went wrong running that command. Try again or check diagnostics.',
        type: 'error',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('Console error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle key press (Enter to send, Shift+Enter for newline)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    // Reset height to auto to get the correct scrollHeight
    e.target.style.height = 'auto';
    // Set height to scrollHeight (min 40px, max 120px)
    e.target.style.height = `${Math.min(Math.max(e.target.scrollHeight, 40), 120)}px`;
  };

  // Render message content based on type
  const renderMessageContent = (message: ConsoleMessage) => {
    // Help message - rich formatted output
    if (message.type === 'help') {
      return (
        <div className="console-help">
          <pre>{message.content}</pre>
        </div>
      );
    }

    // Artifact preview
    if (message.type === 'artifact-preview' && message.artifactPreview) {
      const { name, content, contentType } = message.artifactPreview;
      return (
        <div className="console-artifact-preview">
          <div className="preview-header">
            <span>previewing: {name}</span>
          </div>
          <div className="preview-content">
            {contentType === 'markdown' ? (
              <ReactMarkdown>{content}</ReactMarkdown>
            ) : contentType === 'json' ? (
              <pre><code>{JSON.stringify(JSON.parse(content), null, 2)}</code></pre>
            ) : (
              <pre>{content}</pre>
            )}
          </div>
        </div>
      );
    }

    // Error message
    if (message.type === 'error') {
      return (
        <div className="console-error">
          {message.content}
        </div>
      );
    }

    // Regular message - parse for artifact references
    return <>{parseArtifactRefs(message.content)}</>;
  };

  return (
    <div className="project-console">
      {/* Command Helper Panel */}
      <div className="console-command-bar">
        {commandChips.map((cmd) => (
          <button
            key={cmd}
            className="command-chip"
            onClick={() => handleInsertCommand(cmd)}
          >
            {cmd}
          </button>
        ))}
      </div>

      {/* Messages Area */}
      <div className="console-messages">
        {messages.length === 0 && (
          <div className="console-empty">
            Type <code>/help</code> to see available commands, or ask a question about your project.
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`console-message console-message-${message.type || message.role}`}
          >
            {/* Message Label */}
            <div className="console-message-label">
              {message.type === 'command' ? 'Command' :
               message.type === 'user' ? 'You' :
               message.type === 'error' ? 'Error' :
               message.agent || 'RSC'}
            </div>

            {/* Message Content */}
            <div className="console-message-content">
              {renderMessageContent(message)}
            </div>

            {/* LLM Metadata Footer */}
            {message.role === 'assistant' && message.model && message.type !== 'error' && (
              <div className="console-meta">
                {message.model}
                {message.tokens && ` • ${((message.tokens.input + message.tokens.output) / 1000).toFixed(1)}k tokens`}
                {message.agent && ` • ${message.agent}`}
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="console-message console-message-assistant">
            <div className="console-message-label">RSC</div>
            <div className="console-message-content console-loading">
              Thinking...
            </div>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="console-input-area">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask RSC... Type /help for commands"
          disabled={isLoading}
          rows={1}
        />
        <button
          className="button-primary console-send-btn"
          onClick={handleSend}
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ProjectConsole;
