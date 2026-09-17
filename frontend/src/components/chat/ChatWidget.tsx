import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { useSendChatMessage } from "../../hooks/useChat";
import { extractErrorMessage } from "../../lib/api";
import { Spinner } from "../ui/Spinner";

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
}

const QUICK_REPLIES = ["Check availability", "View menu", "Book a table"];

const FALLBACK_MESSAGE =
  "Sorry, I couldn't reach our assistant just now. Please call the cafe directly, or use the availability page to book manually.";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<DisplayMessage[]>([
    { role: "assistant", content: "Hi! I can help you check availability, book a table, or answer menu questions." },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sendMessage = useSendChatMessage();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sendMessage.isPending]);

  function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sendMessage.isPending) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");

    sendMessage.mutate(
      { message: trimmed, session_id: sessionId },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
        },
        onError: (error) => {
          setMessages((prev) => [...prev, { role: "assistant", content: extractErrorMessage(error, FALLBACK_MESSAGE) }]);
        },
      },
    );
  }

  return (
    <div className="fixed right-4 bottom-4 z-50 sm:right-6 sm:bottom-6">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            role="dialog"
            aria-label="CafeConnect assistant"
            className="mb-4 flex h-[28rem] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-lg border border-cream-200 bg-cream-50 shadow-strong"
          >
            <div className="flex items-center justify-between bg-primary-600 px-4 py-3">
              <p className="text-sm font-semibold text-cream-50">CafeConnect Assistant</p>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close chat"
                className="text-cream-50/80 hover:text-cream-50"
              >
                ✕
              </button>
            </div>

            <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                    message.role === "user"
                      ? "ml-auto bg-primary-600 text-cream-50"
                      : "bg-cream-200 text-cream-900"
                  }`}
                >
                  {message.content}
                </div>
              ))}
              {sendMessage.isPending && (
                <div className="flex items-center gap-2 text-xs text-cream-600">
                  <Spinner className="h-3.5 w-3.5" /> Typing…
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 border-t border-cream-200 px-4 py-2">
              {QUICK_REPLIES.map((reply) => (
                <button
                  key={reply}
                  onClick={() => handleSend(reply)}
                  className="rounded-full border border-cream-300 px-2.5 py-1 text-xs text-cream-700 hover:border-primary-400 hover:text-primary-600"
                >
                  {reply}
                </button>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend(input);
              }}
              className="flex gap-2 border-t border-cream-200 p-3"
            >
              <label htmlFor="chat-input" className="sr-only">
                Message
              </label>
              <input
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about a table or the menu…"
                className="flex-1 rounded-md border border-cream-300 bg-cream-50 px-3 py-2 text-sm outline-none focus:border-primary-400"
              />
              <button
                type="submit"
                disabled={sendMessage.isPending}
                className="rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-cream-50 hover:bg-primary-700 disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close chat assistant" : "Open chat assistant"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-600 text-cream-50 shadow-strong"
      >
        {open ? <ChevronDownIcon /> : <ChatIcon />}
      </motion.button>
    </div>
  );
}

function ChatIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path
        d="M4 5h16v11H8l-4 4V5z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
