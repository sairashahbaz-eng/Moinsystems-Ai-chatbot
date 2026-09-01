
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import App from "../App";
import * as api from "../api";

vi.mock("../api", () => ({
  createSession: vi.fn(),
  sendChatMessage: vi.fn(),
  captureLead: vi.fn(),
}));

describe("MoinSystems AI Chat Widget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();

    vi.mocked(api.createSession).mockResolvedValue({
      session_id: 1,
      session_token: "test-session-token",
      status: "active",
    });

    vi.mocked(api.sendChatMessage).mockResolvedValue({
      answer: "Test assistant response",
      grounded: true,
      session_token: "test-session-token",
      intent: "general",
      lead_state: "none",
    });

    vi.mocked(api.captureLead).mockResolvedValue({
      session_token: "test-session-token",
      state: "submitted",
      message: "Your details have been submitted successfully.",
    });
  });

  async function openChatAndWaitForSession() {
    render(<App />);

    fireEvent.click(
      screen.getByRole("button", {
        name: /open moinsystems ai chat/i,
      }),
    );

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/type your message/i),
      ).toBeInTheDocument();
    });
  }

  async function openChatAndTriggerLeadForm() {
    vi.mocked(api.sendChatMessage).mockResolvedValueOnce({
      answer: "Please provide your details.",
      grounded: true,
      session_token: "test-session-token",
      intent: "commercial",
      lead_state: "ask_name",
    });

    await openChatAndWaitForSession();

    const input = screen.getByPlaceholderText(/type your message/i);

    fireEvent.change(input, {
      target: { value: "I need a project quote" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /send message/i,
      }),
    );

    await screen.findByRole("heading", {
      name: /project details/i,
    });
  }

  it("renders the chat launcher", () => {
    render(<App />);

    expect(
      screen.getByRole("button", {
        name: /open moinsystems ai chat/i,
      }),
    ).toBeInTheDocument();
  });

  it("opens the chat panel after session is ready", async () => {
    await openChatAndWaitForSession();

    expect(
      screen.getByRole("heading", {
        name: /moinsystems ai/i,
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByPlaceholderText(/type your message/i),
    ).toBeInTheDocument();
  });

  it("sends a message and renders the assistant response", async () => {
    await openChatAndWaitForSession();

    const input = screen.getByPlaceholderText(/type your message/i);

    fireEvent.change(input, {
      target: { value: "Hello" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /send message/i,
      }),
    );

    expect(await screen.findByText("Hello")).toBeInTheDocument();

    expect(
      await screen.findByText("Test assistant response"),
    ).toBeInTheDocument();

    expect(api.sendChatMessage).toHaveBeenCalledTimes(1);
  });

  it("shows lead form when backend requests lead capture", async () => {
    await openChatAndTriggerLeadForm();

    expect(
      screen.getByRole("heading", {
        name: /project details/i,
      }),
    ).toBeInTheDocument();

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(
      screen.getByLabelText(/contact number/i),
    ).toBeInTheDocument();
  });

  it("shows invalid email validation", async () => {
    await openChatAndTriggerLeadForm();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Test User" },
    });

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "invalid-email" },
    });

    fireEvent.change(screen.getByLabelText(/contact number/i), {
      target: { value: "+923001234567" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /submit details/i,
      }),
    );

    expect(
      await screen.findByText(
        /please enter a valid email address/i,
      ),
    ).toBeInTheDocument();

    expect(api.captureLead).not.toHaveBeenCalled();
  });

  it("shows invalid contact number validation", async () => {
    await openChatAndTriggerLeadForm();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Test User" },
    });

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });

    fireEvent.change(screen.getByLabelText(/contact number/i), {
      target: { value: "abc123" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /submit details/i,
      }),
    );

    expect(
      await screen.findByText(
        /please enter a valid contact number/i,
      ),
    ).toBeInTheDocument();

    expect(api.captureLead).not.toHaveBeenCalled();
  });

  it("submits valid lead details successfully", async () => {
    await openChatAndTriggerLeadForm();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Test User" },
    });

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });

    fireEvent.change(screen.getByLabelText(/contact number/i), {
      target: { value: "+923001234567" },
    });

    fireEvent.change(screen.getByLabelText(/project summary/i), {
      target: { value: "I need an AI chatbot." },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /submit details/i,
      }),
    );

    await waitFor(() => {
      expect(api.captureLead).toHaveBeenCalledWith(
        expect.objectContaining({
          session_token: "test-session-token",
          full_name: "Test User",
          email: "test@example.com",
          contact_number: "+923001234567",
          project_summary: "I need an AI chatbot.",
        }),
      );
    });

    expect(
      await screen.findByText(
        "Your details have been submitted successfully.",
      ),
    ).toBeInTheDocument();
  });

  it("supports Enter to send a message", async () => {
    await openChatAndWaitForSession();

    const input = screen.getByPlaceholderText(/type your message/i);

    fireEvent.change(input, {
      target: { value: "Hello via Enter" },
    });

    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(
      await screen.findByText("Hello via Enter"),
    ).toBeInTheDocument();

    expect(api.sendChatMessage).toHaveBeenCalledTimes(1);
  });

  it("keeps Shift+Enter for a new line", async () => {
    await openChatAndWaitForSession();

    const input = screen.getByPlaceholderText(/type your message/i);

    fireEvent.change(input, {
      target: { value: "Line one" },
    });

    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      shiftKey: true,
    });

    expect(input).toHaveValue("Line one");
    expect(api.sendChatMessage).not.toHaveBeenCalled();
  });
});
