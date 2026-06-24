import { useState, useEffect, useRef } from "react";
import { signup, login, streamAnswer } from "./api";

function App() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");

  // Bot & Chat State
  const [repoUrl, setRepoUrl] = useState(localStorage.getItem("repo_url") || "");
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

  // Save repoUrl to localStorage when changed
  useEffect(() => {
    localStorage.setItem("repo_url", repoUrl);
  }, [repoUrl]);

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

    if (authUsername.length < 3) {
      setErrorMessage("Username must be at least 3 characters.");
      setIsLoading(false);
      return;
    }
    if (authPassword.length < 6) {
      setErrorMessage("Password must be at least 6 characters.");
      setIsLoading(false);
      return;
    }

    try {
      if (isRegistering) {
        await signup(authUsername, authPassword);
        setSuccessMessage("Account created successfully! You can now log in.");
        setIsRegistering(false);
        setAuthPassword("");
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
    
    // Add placeholder for bot response
    setMessages((prev) => [...prev, { sender: "bot", text: "" }]);

    try {
      await streamAnswer(
        repoUrl,
        userMessage,
        (chunk) => {
          streamBuffer += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { sender: "bot", text: streamBuffer };
            return updated;
          });
        }
      );
    } catch (err) {
      if (err.message === "unauthorized") {
        alert("Session expired. Please log in again.");
        handleLogout();
      } else {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { 
            sender: "bot", 
            text: `⚠️ Error retrieving response: ${err.message}` 
          };
          return updated;
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
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                placeholder="Enter username"
                value={authUsername}
                onChange={(e) => setAuthUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
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
                <div className="message-bubble-content">
                  {msg.text.split("\n").map((line, lIdx) => {
                    // Very simple formatter to highlight backticks or triple backticks in text bubbles
                    if (line.startsWith("```")) return null;
                    
                    // Simple regex replacement for bold markup
                    const boldFormatted = line.split("**").map((subText, sIdx) => {
                      return sIdx % 2 === 1 ? <strong key={sIdx}>{subText}</strong> : subText;
                    });
                    
                    return <p key={lIdx} style={{ minHeight: "1.2em", marginBottom: "4px" }}>{boldFormatted}</p>;
                  })}
                </div>
              </div>
            ))
          )}

          {isStreaming && (
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