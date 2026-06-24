import { useState, useEffect, useRef } from "react";
import { signup, login, streamAnswer } from "./api";
import { marked } from "marked";

function App() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [authUsername, setAuthUsername] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");

  // Bot & Chat State
  const [repoUrl, setRepoUrl] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [openrouterApiKey, setOpenrouterApiKey] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // Status & UI Banners
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = localStorage.getItem("username");
    if (token && storedUser) {
      setIsAuthenticated(true);
      setUsername(storedUser);
    }
  }, []);

  // Sync user-specific states when username changes
  useEffect(() => {
    if (username) {
      setRepoUrl(localStorage.getItem(`${username}_repo_url`) || "");
      setGeminiApiKey(localStorage.getItem(`${username}_gemini_api_key`) || "");
      setOpenrouterApiKey(localStorage.getItem(`${username}_openrouter_api_key`) || "");
    } else {
      setRepoUrl("");
      setGeminiApiKey("");
      setOpenrouterApiKey("");
    }
  }, [username]);

  // Save repoUrl to localStorage when changed (scoped by user)
  useEffect(() => {
    if (username && repoUrl !== null) {
      localStorage.setItem(`${username}_repo_url`, repoUrl);
    }
  }, [repoUrl, username]);

  useEffect(() => {
    if (username && geminiApiKey !== null) {
      localStorage.setItem(`${username}_gemini_api_key`, geminiApiKey);
    }
  }, [geminiApiKey, username]);

  useEffect(() => {
    if (username && openrouterApiKey !== null) {
      localStorage.setItem(`${username}_openrouter_api_key`, openrouterApiKey);
    }
  }, [openrouterApiKey, username]);

  // Auto-scroll chat to bottom when messages list updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  // Authenticate submission
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    if (isRegistering) {
      // Username validation: starts with letter, alphanumeric/underscore only, 3-30 chars
      const usernameRegex = /^[a-zA-Z][a-zA-Z0-9_]{2,29}$/;
      if (!usernameRegex.test(authUsername)) {
        setErrorMessage("Username must start with a letter and contain only alphanumeric characters or underscores (3-30 characters).");
        setIsLoading(false);
        return;
      }

      // Email validation: standard email format
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(authEmail)) {
        setErrorMessage("Please enter a valid Gmail ID / Email address.");
        setIsLoading(false);
        return;
      }

      // Password strict conditions
      if (authPassword.length < 8) {
        setErrorMessage("Password must be at least 8 characters long.");
        setIsLoading(false);
        return;
      }
      if (!/[A-Z]/.test(authPassword)) {
        setErrorMessage("Password must contain at least one uppercase letter.");
        setIsLoading(false);
        return;
      }
      if (!/[a-z]/.test(authPassword)) {
        setErrorMessage("Password must contain at least one lowercase letter.");
        setIsLoading(false);
        return;
      }
      if (!/\d/.test(authPassword)) {
        setErrorMessage("Password must contain at least one number.");
        setIsLoading(false);
        return;
      }
      if (!/[@$!%*?&#]/.test(authPassword)) {
        setErrorMessage("Password must contain at least one special character (@$!%*?&#).");
        setIsLoading(false);
        return;
      }
    }

    try {
      if (isRegistering) {
        await signup(authUsername, authEmail, authPassword);
        setSuccessMessage("Account created successfully! You can now log in.");
        setIsRegistering(false);
        setAuthPassword("");
        setAuthEmail("");
      } else {
        const response = await login(authUsername, authPassword);
        localStorage.setItem("token", response.access_token);
        localStorage.setItem("username", response.username);
        setUsername(response.username);
        setIsAuthenticated(true);
        setAuthUsername("");
        setAuthPassword("");
      }
    } catch (err) {
      setErrorMessage(err.message || "Authentication failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setIsAuthenticated(false);
    setUsername("");
    setRepoUrl("");
    setGeminiApiKey("");
    setOpenrouterApiKey("");
    setMessages([]);
    setErrorMessage("");
    setSuccessMessage("");
  };

  // Submit question
  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    if (!repoUrl.trim()) {
      alert("Please configure a repository URL in the sidebar first.");
      return;
    }

    const userMessage = question;
    setQuestion("");
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);
    setIsStreaming(true);

    let streamBuffer = "";
    let hasBotMessage = false;

    try {
      await streamAnswer(
        repoUrl,
        userMessage,
        (chunk) => {
          streamBuffer += chunk;
          if (!hasBotMessage) {
            hasBotMessage = true;
            setMessages((prev) => [...prev, { sender: "bot", text: streamBuffer }]);
          } else {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { sender: "bot", text: streamBuffer };
              return updated;
            });
          }
        },
        geminiApiKey,
        openrouterApiKey
      );
    } catch (err) {
      if (err.message === "unauthorized") {
        alert("Session expired. Please log in again.");
        handleLogout();
      } else {
        setMessages((prev) => {
          const updated = [...prev];
          if (!hasBotMessage) {
            return [...updated, { sender: "bot", text: `⚠️ Error retrieving response: ${err.message}` }];
          } else {
            updated[updated.length - 1] = { 
              sender: "bot", 
              text: `⚠️ Error retrieving response: ${err.message}` 
            };
            return updated;
          }
        });
      }
    } finally {
      setIsStreaming(false);
    }
  };

  // Render Authentication View
  if (!isAuthenticated) {
    return (
      <div className="auth-container">
        <div className="auth-card glass-panel">
          <div className="auth-header">
            <h1>GitHub QA Bot</h1>
            <p>{isRegistering ? "Create your account to get started" : "Sign in to access the QA dashboard"}</p>
          </div>

          {errorMessage && <div className="banner banner-error">{errorMessage}</div>}
          {successMessage && <div className="banner banner-success">{successMessage}</div>}

          <form onSubmit={handleAuthSubmit}>
            <div className="auth-form-group">
              <label htmlFor="username">{isRegistering ? "Username" : "Username or Gmail ID"}</label>
              <input
                type="text"
                id="username"
                placeholder={isRegistering ? "Enter username" : "Enter username or email"}
                value={authUsername}
                onChange={(e) => setAuthUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            {isRegistering && (
              <div className="auth-form-group">
                <label htmlFor="email">Gmail ID / Email</label>
                <input
                  type="email"
                  id="email"
                  placeholder="Enter Gmail ID or email"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            )}
            <div className="auth-form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                placeholder="Enter password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            {isRegistering && (
              <div className="auth-requirements">
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>Requirements:</div>
                <ul style={{ margin: 0, paddingLeft: "16px", listStyleType: "disc" }}>
                  <li>Username: 3-30 chars, starts with a letter, letters/numbers/underscores only.</li>
                  <li>Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character (@$!%*?&#).</li>
                </ul>
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "10px" }} disabled={isLoading}>
              {isLoading ? "Processing..." : isRegistering ? "Sign Up" : "Log In"}
            </button>
          </form>

          <p className="auth-footer-text">
            {isRegistering ? "Already have an account? " : "New to the platform? "}
            <span
              className="auth-toggle-link"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setErrorMessage("");
                setSuccessMessage("");
                setAuthUsername("");
                setAuthEmail("");
                setAuthPassword("");
              }}
            >
              {isRegistering ? "Log In" : "Sign Up"}
            </span>
          </p>
        </div>
      </div>
    );
  }

  // Render Main Chat Interface Dashboard
  return (
    <div className="main-layout">
      {/* Left Sidebar */}
      <div className="sidebar glass-panel">
        <div className="logo-section">
          <div className="empty-state-icon" style={{ width: "36px", height: "36px", margin: 0, borderRadius: "8px" }}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" width="20" height="20">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A9 9 0 0 1 12 3v0a9 9 0 0 1 9 9v.75m-.75-3.04a7.5 7.5 0 1 0-13.5 0M2.25 12.75a1.218 1.218 0 0 0 .225-.225m19.5 0a1.218 1.218 0 0 1-.225-.225M2.25 12.75h19.5" />
            </svg>
          </div>
          <h2>GitHub QA Bot</h2>
        </div>

        <div className="config-section">
          <div>
            <label htmlFor="repo-url">Repository Target URL</label>
            <input
              type="text"
              id="repo-url"
              placeholder="e.g., https://github.com/langchain-ai/langchain"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isStreaming}
            />
          </div>
          <div style={{ marginTop: "14px" }}>
            <label htmlFor="gemini-key">Gemini API Key (Optional)</label>
            <input
              type="password"
              id="gemini-key"
              placeholder="AIzaSy..."
              value={geminiApiKey}
              onChange={(e) => setGeminiApiKey(e.target.value)}
              disabled={isStreaming}
            />
          </div>
          <div style={{ marginTop: "14px" }}>
            <label htmlFor="openrouter-key">OpenRouter API Key (Optional)</label>
            <input
              type="password"
              id="openrouter-key"
              placeholder="sk-or-..."
              value={openrouterApiKey}
              onChange={(e) => setOpenrouterApiKey(e.target.value)}
              disabled={isStreaming}
            />
          </div>
        </div>

        <div className="user-section">
          <div className="user-info">
            <span className="username">@{username}</span>
            <span className="user-status">Connected</span>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Log Out">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" width="18" height="18">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-area glass-panel">
        <div className="chat-header">
          <div className="chat-header-info">
            <div className="chat-header-title">Repository Chat Assistant</div>
            <div className="chat-header-repo">{repoUrl || "No repository configured"}</div>
          </div>
        </div>

        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" width="32" height="32">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
                </svg>
              </div>
              <h3>Explore Your Codebase</h3>
              <p>Configure a GitHub repository in the left panel, and ask specific questions about the structure, classes, modules, or flows of your code.</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender === "user" ? "message-user" : "message-bot"}`}>
                <span className="message-sender">{msg.sender === "user" ? `@${username}` : "Assistant"}</span>
                {msg.sender === "user" ? (
                  <div className="message-bubble-content">
                    {msg.text.split("\n").map((line, lIdx) => (
                      <p key={lIdx} style={{ minHeight: "1.2em", marginBottom: "4px" }}>{line}</p>
                    ))}
                  </div>
                ) : (
                  <div 
                    className="message-bubble-content markdown-body"
                    dangerouslySetInnerHTML={{ 
                      __html: marked.parse(msg.text, { gfm: true, breaks: true }) 
                    }}
                  />
                )}
              </div>
            ))
          )}

          {isStreaming && (messages.length === 0 || messages[messages.length - 1]?.sender !== "bot") && (
            <div className="message message-bot">
              <span className="message-sender">Assistant</span>
              <div className="message-bubble-content" style={{ padding: "8px 12px" }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-box-container">
          <form className="chat-input-form" onSubmit={handleAsk}>
            <textarea
              placeholder={repoUrl ? "Ask something about this repository..." : "Configure a repository first"}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isStreaming || !repoUrl}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk(e);
                }
              }}
            />
            <button type="submit" className="btn btn-primary" disabled={isStreaming || !question.trim() || !repoUrl}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M1.946 9.315c-.522-.174-.527-.455.01-.634L21.044 2.06c.502-.167.925.215.753.717L15.347 21.05c-.18.528-.46.522-.634-.01l-3.328-9.983L1.946 9.315z" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;