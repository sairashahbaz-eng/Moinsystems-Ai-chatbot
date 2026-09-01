import { useEffect, useState } from "react";

import "./App.css";

import {
  captureLead,
  createSession,
  sendChatMessage,
  type ChatResponse,
} from "./api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

const SESSION_KEY = "moinsystems_chat_session";

function getTimestamp() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content:
        "Hi! I'm the MoinSystems AI assistant. How can I help you today?",
      timestamp: getTimestamp(),
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [showLeadForm, setShowLeadForm] = useState(false);
  const [leadLoading, setLeadLoading] = useState(false);
  const [leadError, setLeadError] = useState("");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [contactNumber, setContactNumber] = useState("");
  const [serviceInterest, setServiceInterest] = useState("");
  const [projectSummary, setProjectSummary] = useState("");

  useEffect(() => {
    const existingToken = sessionStorage.getItem(SESSION_KEY);

    if (existingToken) {
      setSessionToken(existingToken);
      return;
    }

    async function startSession() {
      try {
        setError("");

        const session = await createSession(window.location.href);

        if (!session || !session.session_token) {
          throw new Error("Server did not return a session token.");
        }

        sessionStorage.setItem(
          SESSION_KEY,
          session.session_token
        );

        setSessionToken(session.session_token);
      } catch (err) {
        console.error("Session creation failed:", err);

        setError(
          err instanceof Error
            ? err.message
            : "Unable to start the chat. Please refresh the page and try again."
        );
      }
    }

    startSession();
  }, []);

  const sendMessage = async () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || isLoading || !sessionToken) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmedMessage,
      timestamp: getTimestamp(),
    };

    const recentMessages = messages.slice(-6).map((item) => ({
      role: item.role,
      content: item.content,
    }));

    setMessages((current) => [...current, userMessage]);
    setMessage("");
    setError("");
    setShowLeadForm(false);
    setIsLoading(true);

    try {
      const response: ChatResponse = await sendChatMessage({
        session_token: sessionToken,
        question: trimmedMessage,
        recent_messages: recentMessages,
      });

      if (response.session_token) {
        sessionStorage.setItem(
          SESSION_KEY,
          response.session_token
        );

        setSessionToken(response.session_token);
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: response.answer,
          timestamp: getTimestamp(),
        },
      ]);

      if (
        response.lead_state &&
        ["ask_name", "ask_email", "ask_phone"].includes(
          response.lead_state.toLowerCase()
        )
      ) {
        setShowLeadForm(true);
      }
    } catch (err) {
      console.error("Chat request failed:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to send your message. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const submitLead = async () => {
    setLeadError("");

    if (!fullName.trim()) {
      setLeadError("Please enter your name.");
      return;
    }

    if (!email.trim()) {
      setLeadError("Please enter your email address.");
      return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email.trim())) {
      setLeadError("Please enter a valid email address.");
      return;
    }

    if (!contactNumber.trim()) {
      setLeadError("Please enter your contact number.");
      return;
    }

    const phonePattern = /^[0-9+\-\s()]{7,20}$/;

    if (!phonePattern.test(contactNumber.trim())) {
      setLeadError("Please enter a valid contact number.");
      return;
    }

    if (!sessionToken) {
      setLeadError(
        "Your session has expired. Please refresh the page."
      );
      return;
    }

    setLeadLoading(true);

    try {
      const response = await captureLead({
        session_token: sessionToken,
        full_name: fullName.trim(),
        email: email.trim(),
        contact_number: contactNumber.trim(),
        service_interest: serviceInterest.trim() || null,
        project_summary: projectSummary.trim() || null,
        source_page: window.location.href,
      });

      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          role: "assistant",
          content: response.message,
          timestamp: getTimestamp(),
        },
      ]);

      setShowLeadForm(false);
    } catch (err) {
      console.error("Lead capture failed:", err);

      setLeadError(
        err instanceof Error
          ? err.message
          : "Unable to submit your details. Please try again."
      );
    } finally {
      setLeadLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <main className="widget-container">
      {!isOpen && (
        <button
          className="chat-launcher"
          type="button"
          onClick={() => setIsOpen(true)}
          aria-label="Open MoinSystems AI chat"
        >
          <span aria-hidden="true">💬</span>
          <span>Chat with us</span>
        </button>
      )}

      {isOpen && (
        <section
          className="chat-panel"
          aria-label="MoinSystems AI chatbot"
        >
          <header className="chat-header">
            <div>
              <h1>MoinSystems AI</h1>
              <p>AI Assistant</p>
            </div>

            <div className="header-actions">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Minimize chat"
              >
                −
              </button>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
              >
                ×
              </button>
            </div>
          </header>

          <div
            className="message-list"
            aria-live="polite"
            aria-label="Chat messages"
          >
            {messages.map((item) => (
              <div
                key={item.id}
                className={`message-row ${item.role}`}
              >
                <div className="message-bubble">
                  <p>{item.content}</p>
                  <time>{item.timestamp}</time>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message-row assistant">
                <div className="message-bubble loading">
                  <span aria-hidden="true">●</span>
                  <span aria-hidden="true">●</span>
                  <span aria-hidden="true">●</span>

                  <span className="sr-only">
                    MoinSystems AI is typing
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div className="error-message" role="alert">
                {error}
              </div>
            )}

            {showLeadForm && (
              <div className="lead-form">
                <h2>Project Details</h2>

                <p>
                  Please provide your details so we can help with your
                  project.
                </p>

                <label htmlFor="full-name">
                  Name *
                </label>

                <input
                  id="full-name"
                  type="text"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  placeholder="Your name"
                  disabled={leadLoading}
                />

                <label htmlFor="email">
                  Email *
                </label>

                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  disabled={leadLoading}
                />

                <label htmlFor="contact-number">
                  Contact Number *
                </label>

                <input
                  id="contact-number"
                  type="tel"
                  value={contactNumber}
                  onChange={(event) =>
                    setContactNumber(event.target.value)
                  }
                  placeholder="+92..."
                  disabled={leadLoading}
                />

                <label htmlFor="service-interest">
                  Service Interest
                </label>

                <input
                  id="service-interest"
                  type="text"
                  value={serviceInterest}
                  onChange={(event) =>
                    setServiceInterest(event.target.value)
                  }
                  placeholder="e.g. AI chatbot, web app, SaaS"
                  disabled={leadLoading}
                />

                <label htmlFor="project-summary">
                  Project Summary
                </label>

                <textarea
                  id="project-summary"
                  value={projectSummary}
                  onChange={(event) =>
                    setProjectSummary(event.target.value)
                  }
                  placeholder="Briefly describe your project..."
                  rows={3}
                  disabled={leadLoading}
                />

                {leadError && (
                  <div
                    className="error-message"
                    role="alert"
                  >
                    {leadError}
                  </div>
                )}

                <button
                  type="button"
                  className="lead-submit"
                  onClick={submitLead}
                  disabled={leadLoading}
                >
                  {leadLoading
                    ? "Submitting..."
                    : "Submit Details"}
                </button>
              </div>
            )}
          </div>

          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <label
              htmlFor="chat-message"
              className="sr-only"
            >
              Message
            </label>

            <textarea
              id="chat-message"
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder={
                sessionToken
                  ? "Type your message..."
                  : "Starting chat..."
              }
              rows={1}
              disabled={isLoading || !sessionToken}
            />

            <button
              type="submit"
              disabled={
                !message.trim() ||
                isLoading ||
                !sessionToken
              }
              aria-label="Send message"
            >
              Send
            </button>
          </form>
        </section>
      )}
    </main>
  );
}

export default App;