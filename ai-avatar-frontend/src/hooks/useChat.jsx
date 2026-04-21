import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = typeof window !== "undefined" ? `http://${window.location.hostname}:3001` : "http://localhost:3001";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);

  const chat = async (message) => {
    setLoading(true);
    try {
      const data = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });
      const resJson = await data.json();
      if (resJson.error) {
        console.error("Backend Error:", resJson.error);
        alert(`Backend Error: ${resJson.error}`);
      } else if (resJson.messages) {
        setMessages((messages) => [...messages, ...resJson.messages]);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to communicate with the avatar backend.");
    } finally {
      setLoading(false);
    }
  };
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
