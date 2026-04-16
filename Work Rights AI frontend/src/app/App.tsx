import { useState, useRef, useEffect } from "react";
import { Send, FileText, Clock, DollarSign, Scale, Shield, Briefcase, AlertCircle, Bot } from "lucide-react";
import { ChatMessage } from "./components/ChatMessage";
import { QuickActionCard } from "./components/QuickActionCard";

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: string;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm your Work Rights AI Assistant. I'm here to help you understand your workplace rights and answer any employment-related questions you may have. How can I assist you today?",
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickActions = [
    {
      icon: Clock,
      title: "Working Hours",
      description: "Learn about overtime, breaks, and maximum working hours"
    },
    {
      icon: DollarSign,
      title: "Wages & Pay",
      description: "Understand minimum wage, pay slips, and salary deductions"
    },
    {
      icon: FileText,
      title: "Contracts",
      description: "Get help with employment contracts and terms"
    },
    {
      icon: Shield,
      title: "Discrimination",
      description: "Information about workplace discrimination and harassment"
    },
    {
      icon: Briefcase,
      title: "Termination",
      description: "Understand dismissal, redundancy, and notice periods"
    },
    {
      icon: AlertCircle,
      title: "Health & Safety",
      description: "Workplace safety rights and reporting concerns"
    }
  ];

  const sendChatRequest = async (userMessage: string): Promise<string> => {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: userMessage,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Chat backend request failed");
    }

    const data: { answer: string } = await response.json();
    return data.answer;
  };

  const getFallbackAIResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes("hours") || lowerMessage.includes("overtime")) {
      return "Regarding working hours: In most jurisdictions, standard working hours are typically 40 hours per week. Overtime pay (usually 1.5x regular rate) applies when you work beyond standard hours. You're entitled to breaks - typically 30 minutes for shifts over 6 hours. The maximum working week is often capped at 48 hours (averaged over 17 weeks), though you can opt out in writing. Would you like more specific information about your situation?";
    } else if (lowerMessage.includes("wage") || lowerMessage.includes("pay") || lowerMessage.includes("salary")) {
      return "Regarding wages and pay: You have the right to receive at least minimum wage for your work. Your employer must provide itemized pay slips showing gross pay, deductions, and net pay. Unauthorized deductions from your wages are generally illegal. You should be paid regularly (weekly, bi-weekly, or monthly as agreed). If you believe you're being underpaid, you can file a complaint with your local labor authority. Would you like information about specific pay-related concerns?";
    } else if (lowerMessage.includes("contract") || lowerMessage.includes("agreement")) {
      return "Regarding employment contracts: You're entitled to a written statement of employment within 2 months of starting work. This should include job title, duties, pay, hours, holiday entitlement, and notice periods. Always read contracts carefully before signing. Key terms include probation periods, termination clauses, and any restrictive covenants. You can negotiate contract terms before accepting. If you need help understanding your contract, consider consulting with an employment lawyer or union representative.";
    } else if (lowerMessage.includes("discriminat") || lowerMessage.includes("harass")) {
      return "Regarding discrimination and harassment: You're protected from discrimination based on age, disability, gender, race, religion, sexual orientation, and other protected characteristics. Harassment and bullying are illegal. If you experience discrimination, document incidents with dates, times, and witnesses. Report to HR or management first. If unresolved, you can file a complaint with the Equal Employment Opportunity Commission or equivalent body. You're also protected from retaliation for reporting discrimination.";
    } else if (lowerMessage.includes("fire") || lowerMessage.includes("terminat") || lowerMessage.includes("dismiss") || lowerMessage.includes("redundan")) {
      return "Regarding termination and dismissal: Employers must provide proper notice (or pay in lieu) when terminating employment - typically 1-12 weeks depending on length of service. You can be dismissed for misconduct, capability, or redundancy. Unfair dismissal claims can be made if you've worked for 2+ years. Redundancy should follow fair selection criteria and you're entitled to redundancy pay. Constructive dismissal occurs when working conditions become intolerable. Always request written reasons for dismissal.";
    } else if (lowerMessage.includes("safety") || lowerMessage.includes("health") || lowerMessage.includes("injury")) {
      return "Regarding health and safety: Your employer has a legal duty to ensure your workplace is safe. This includes proper equipment, training, risk assessments, and protective gear. You have the right to refuse unsafe work without punishment. Report all accidents and injuries immediately. You may be entitled to sick pay and compensation for workplace injuries. Safety representatives should be available to address concerns. For serious violations, contact your local occupational safety authority.";
    } else if (lowerMessage.includes("leave") || lowerMessage.includes("holiday") || lowerMessage.includes("vacation")) {
      return "Regarding leave and holidays: You're typically entitled to paid annual leave (often 20-28 days per year including public holidays). You also have rights to sick leave, parental leave, and bereavement leave. Your employer should have clear procedures for requesting time off. Unused holiday often cannot be carried over unless specified in your contract. You should be paid your normal rate during annual leave. Parental leave may be partially paid depending on your jurisdiction.";
    } else {
      return "I understand you have a question about workplace rights. I can help with topics including working hours, wages, contracts, discrimination, termination, health & safety, and leave entitlements. Could you provide more details about your specific situation? You can also click one of the quick action cards below to explore common topics.";
    }
  };

  const handleSend = async () => {
    const trimmedInput = inputValue.trim();
    if (trimmedInput === "") return;

    const userMessage: Message = {
      id: Date.now(),
      text: trimmedInput,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setErrorMessage(null);
    setIsTyping(true);

    try {
      const aiText = await sendChatRequest(trimmedInput);
      const aiResponse: Message = {
        id: Date.now() + 1,
        text: aiText,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      const fallbackText = getFallbackAIResponse(trimmedInput);
      const aiResponse: Message = {
        id: Date.now() + 1,
        text: fallbackText,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiResponse]);
      setErrorMessage("The chatbot backend is unavailable. Showing local fallback response.");
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickAction = (title: string) => {
    const prompts: { [key: string]: string } = {
      "Working Hours": "What are my rights regarding working hours and overtime?",
      "Wages & Pay": "Can you explain my rights about wages and payment?",
      "Contracts": "What should I know about employment contracts?",
      "Discrimination": "What are my rights regarding workplace discrimination?",
      "Termination": "What are my rights if I'm being terminated?",
      "Health & Safety": "What are my workplace health and safety rights?"
    };
    
    setInputValue(prompts[title] || title);
  };

  return (
    <div className="size-full flex flex-col bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Scale className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Work Rights AI</h1>
              <p className="text-xs text-gray-600">Your Employment Rights Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-sm text-gray-600">Online</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        <div className="flex-1 flex flex-col max-w-7xl mx-auto w-full">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="space-y-6 max-w-4xl mx-auto">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message.text}
                  isUser={message.isUser}
                  timestamp={message.timestamp}
                />
              ))}
              {isTyping && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Quick Actions - Only show when chat is empty or just has welcome message */}
          {messages.length <= 1 && (
            <div className="px-6 pb-4">
              <div className="max-w-4xl mx-auto">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {quickActions.map((action) => (
                    <QuickActionCard
                      key={action.title}
                      icon={action.icon}
                      title={action.title}
                      description={action.description}
                      onClick={() => handleQuickAction(action.title)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="flex-shrink-0 bg-white border-t border-gray-200 px-6 py-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-3 items-end">
                <div className="flex-1 relative">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Ask me about your work rights..."
                    rows={1}
                    className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    style={{ minHeight: '48px', maxHeight: '120px' }}
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={inputValue.trim() === "" || isTyping}
                  className="flex-shrink-0 w-12 h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-colors"
                >
                  <Send className="w-5 h-5 text-white" />
                </button>
              </div>
              {errorMessage && (
                <p className="text-xs text-red-600 mt-3 text-center">
                  {errorMessage}
                </p>
              )}
              <p className="text-xs text-gray-500 mt-2 text-center">
                This AI provides general information only. For legal advice, consult a qualified employment lawyer.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
