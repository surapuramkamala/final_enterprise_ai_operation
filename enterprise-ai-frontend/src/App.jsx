
import { useEffect, useState } from "react";
import {
  Bot, ShieldCheck, FileText, Send, LogOut,
  RefreshCw, Sparkles, AlertCircle
} from "lucide-react";

const API_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function apiRequest(path, { method = "GET", token, body } = {}) {
  const headers = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    ...(body !== undefined
      ? { body: JSON.stringify(body) }
      : {})
  });

  const text = await response.text();
  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!response.ok) {
    throw new Error(
      `${response.status}: ${
        data.detail || data.message || "Request failed"
      }`
    );
  }

  return data;
}

export default function App() {
  const [token, setToken] = useState(
    () => sessionStorage.getItem("ai_token") || ""
  );

  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("Checking");

  useEffect(() => {
    apiRequest("/health")
      .then(() => setApiStatus("Connected"))
      .catch(() => setApiStatus("Unavailable"));
  }, []);

  function saveToken(value) {
    if (value) {
      sessionStorage.setItem("ai_token", value);
    } else {
      sessionStorage.removeItem("ai_token");
    }
    setToken(value);
  }

  async function handleAuth(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setLoading(true);

    try {
      const path = mode === "login" ? "/login" : "/register";

      const body = mode === "login"
        ? { email, password }
        : { username, email, password };

      const data = await apiRequest(path, {
        method: "POST",
        body
      });

      const jwt = data.access_token || data.token;

      if (!jwt) {
        throw new Error(
          "No token returned. Check the backend login response."
        );
      }

      saveToken(jwt);
      setPassword("");
      setMessages([]);
      setNotice("You are signed in successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function askQuestion(event) {
    event.preventDefault();

    const prompt = question.trim();
    if (!prompt || loading) return;

    setError("");
    setNotice("");
    setQuestion("");
    setMessages(previous => [
      ...previous,
      { role: "user", text: prompt }
    ]);
    setLoading(true);

    try {
      const data = await apiRequest("/ask", {
        method: "POST",
        token,
        body: { question: prompt }
      });

      setMessages(previous => [
        ...previous,
        {
          role: "assistant",
          text: data.answer || data.response || data.message ||
            "The API returned no answer field.",
          citations: data.citations || data.sources || [],
          traceId: data.trace_id,
          latency: data.latency_ms
        }
      ]);
    } catch (err) {
      setError(err.message);

      if (err.message.startsWith("401:")) {
        saveToken("");
      }
    } finally {
      setLoading(false);
    }
  }

  async function reindexDocuments() {
    setError("");
    setNotice("");
    setLoading(true);

    try {
      const data = await apiRequest("/admin/reindex", {
        method: "POST",
        token,
        body: {}
      });

      setNotice(data.message || data.status || "Reindex request completed.");
    } catch (err) {
      setError(`Reindex failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    saveToken("");
    setMessages([]);
    setQuestion("");
    setNotice("");
    setError("");
  }

  if (!token) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <div className="brand-icon"><Bot size={30} /></div>

          <p className="eyebrow">ENTERPRISE AI PLATFORM</p>
          <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
          <p className="muted">
            Secure access to your document knowledge assistant.
          </p>

          <div className="tabs">
            <button
              className={mode === "login" ? "active" : ""}
              onClick={() => {
                setMode("login");
                setError("");
              }}
            >
              Sign in
            </button>

            <button
              className={mode === "register" ? "active" : ""}
              onClick={() => {
                setMode("register");
                setError("");
              }}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth}>
            {mode === "register" && (
              <label>
                Username
                <input
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </label>
            )}

            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="you@company.com"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete={
                  mode === "login"
                    ? "current-password"
                    : "new-password"
                }
                minLength={8}
                required
              />
            </label>

            {error && (
              <div className="error">
                <AlertCircle size={17} />
                {error}
              </div>
            )}

            <button className="primary" disabled={loading}>
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>

          {notice && <p className="success">{notice}</p>}

          <p className="api-status">
            API status: <strong>{apiStatus}</strong>
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon"><Bot size={25} /></span>
          <div>
            <strong>Enterprise AI</strong>
            <small>Knowledge Operations</small>
          </div>
        </div>

        <div className="header-actions">
          <span className="status">
            <span className="dot" />
            {apiStatus}
          </span>
          <button className="secondary" onClick={logout}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-icon"><Sparkles size={27} /></div>
        <p className="eyebrow">AI KNOWLEDGE ASSISTANT</p>
        <h1>Ask your documents</h1>
        <p className="muted">
          Search indexed policies, contracts, access procedures,
          and incident documentation.
        </p>
      </section>

      {error && (
        <div className="error banner">
          <AlertCircle size={17} /> {error}
        </div>
      )}

      {notice && <div className="success banner">{notice}</div>}

      <section className="chat-card">
        {messages.length === 0 ? (
          <div className="empty">
            <FileText size={34} />
            <h2>How can I help you?</h2>
            <p>Try asking a question about your indexed documents.</p>

            <div className="examples">
              {[
                "What should I do before testing a security vulnerability?",
                "How quickly must a security incident be reported?",
                "What approval is required for production access?"
              ].map(item => (
                <button
                  key={item}
                  onClick={() => setQuestion(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <article className={`message ${message.role}`} key={index}>
                <strong>
                  {message.role === "user" ? "You" : "AI Assistant"}
                </strong>
                <p>{message.text}</p>

                {message.citations?.length > 0 && (
                  <div className="citations">
                    <strong>Sources</strong>
                    {message.citations.map((source, i) => {
                      const label = typeof source === "string"
                        ? source
                        : source.source || source.filename ||
                          source.file || `Source ${i + 1}`;

                      return (
                        <span key={`${label}-${i}`}>
                          <FileText size={14} /> {label}
                          {typeof source === "object" && source.page
                            ? ` · page ${source.page}`
                            : ""}
                        </span>
                      );
                    })}
                  </div>
                )}

                {message.traceId && (
                  <small>Trace ID: {message.traceId}</small>
                )}
                {message.latency !== undefined && (
                  <small>Latency: {message.latency} ms</small>
                )}
              </article>
            ))}
          </div>
        )}

        <form className="composer" onSubmit={askQuestion}>
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            rows={3}
            required
          />
          <button className="primary send" disabled={loading}>
            {loading ? "Processing..." : "Ask AI"}
            <Send size={16} />
          </button>
        </form>
      </section>

      <footer className="footer">
        <span><ShieldCheck size={15} /> Authenticated session</span>
        <button
          className="secondary"
          onClick={reindexDocuments}
          disabled={loading}
        >
          <RefreshCw size={15} /> Reindex documents
        </button>
      </footer>
    </main>
  );
}
