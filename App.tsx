import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { ChatMessage } from './types';
import ChatBubble from './components/ChatBubble';
import RecordButton from './components/RecordButton';
import { geminiService } from './services/geminiService';
import { elevenLabsService } from './services/elevenLabsService';
import { Chat } from '@google/genai';

const App: React.FC = () => {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    { role: 'bot', content: "Hello! I'm your AI banking assistant. How can I help you today? Please tap the microphone to speak." },
  ]);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const chatSessionRef = useRef<Chat | null>(null);

  useEffect(() => {
    // Initialize the stateful chat session once when the component mounts
    if (!chatSessionRef.current) {
        chatSessionRef.current = geminiService.startChatSession();
    }
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const addMessage = (message: ChatMessage) => {
    setChatHistory(prev => [...prev, message]);
  };

  const playAudio = useCallback(async (audioBlob: Blob) => {
    if (!audioContextRef.current) {
      // FIX: Cast window to any to allow for webkitAudioContext for older browser compatibility.
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const audioContext = audioContextRef.current;
    
    // Resume context on user gesture if needed
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
  }, []);

  const handleAudioBlob = useCallback(async (audioBlob: Blob) => {
    setIsLoading(true);
    setStatusMessage('Transcribing your speech...');
    addMessage({ role: 'status', content: 'Processing your request...' });
    
    try {
      // 1. Speech to Text
      const userText = await elevenLabsService.speechToText(audioBlob);
      setChatHistory(prev => prev.slice(0, -1)); // Remove status message
      addMessage({ role: 'user', content: userText });
      setStatusMessage('Thinking...');

      if (!chatSessionRef.current) {
          throw new Error("Chat session not initialized.");
      }

      // 2. Call Gemini with function calling (using the persistent session)
      const botText = await geminiService.runConversation(chatSessionRef.current, userText);
      addMessage({ role: 'bot', content: botText });
      setStatusMessage('Generating speech...');

      // 3. Text to Speech
      const botAudioBlob = await elevenLabsService.textToSpeech(botText);
      setStatusMessage('Speaking...');
      
      // 4. Play audio response
      await playAudio(botAudioBlob);

    } catch (error) {
      console.error("An error occurred in the conversation flow:", error);
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
      setChatHistory(prev => prev.slice(0, -1)); // Remove status message
      addMessage({ role: 'bot', content: `I'm sorry, I encountered an error: ${errorMessage}` });
    } finally {
      setIsLoading(false);
      setStatusMessage('');
    }
  }, [playAudio]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        handleAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop()); // Stop microphone access
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatusMessage('Recording... Tap stop when you are done.');
    } catch (error) {
      console.error("Error accessing microphone:", error);
      setStatusMessage('Microphone access denied. Please enable it in your browser settings.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto font-sans">
        <header className="bg-white p-4 border-b border-gray-200 shadow-sm sticky top-0 z-10">
            <h1 className="text-2xl font-bold text-center text-gray-800">AI Banking Assistant</h1>
        </header>
        <main ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 bg-gray-50">
            {chatHistory.map((msg, index) => (
                <ChatBubble key={index} message={msg} />
            ))}
        </main>
        <footer className="bg-white p-4 border-t border-gray-200">
            <div className="flex flex-col items-center justify-center gap-4">
                { (isLoading || isRecording || statusMessage) &&
                    <p className="text-sm text-gray-600 h-5">{statusMessage}</p>
                }
                <RecordButton 
                    isRecording={isRecording}
                    isLoading={isLoading}
                    onStart={startRecording}
                    onStop={stopRecording}
                />
            </div>
        </footer>
    </div>
  );
};

export default App;