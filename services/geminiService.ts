import { GoogleGenAI, GenerateContentResponse, Chat } from "@google/genai";
import { nessieFunctionDeclarations } from "../constants";
import { nessieBankApi } from "./nessieService";

// The API key must be obtained exclusively from the environment variable `process.env.API_KEY`.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const model = "gemini-2.5-flash";

const systemInstruction = `You are a helpful and professional banking assistant for 'Nessie Bank'.
- Your primary goal is to help users by calling the available functions based on their requests.
- When you need information like an account ID, ask the user for it clearly.
- CRITICAL: User account IDs are numbers, but they may speak them as words (e.g., "one two three four"). You MUST convert these words to digits.
- CRITICAL: The banking system requires account IDs to have the prefix 'acc-'. After converting words to digits, you must prepend 'acc-' to the ID before calling any function. For example, if a user says their ID is "one two three four", you must call the function with accountId: "acc-1234".
- Be concise and clear in your responses.`;


export const geminiService = {
  startChatSession: (): Chat => {
     return ai.chats.create({
      model: model,
      config: {
        systemInstruction: systemInstruction,
        tools: [{ functionDeclarations: nessieFunctionDeclarations }],
      },
    });
  },

  runConversation: async (chat: Chat, userInput: string): Promise<string> => {
    // First, send the user's message
    // FIX: `chat.sendMessage` expects an object with a `message` property. The user input string is passed as the value.
    let response: GenerateContentResponse = await chat.sendMessage({ message: userInput });

    // Check if the model responded with a function call
    if (response.functionCalls && response.functionCalls.length > 0) {
      const functionCall = response.functionCalls[0];
      const functionName = functionCall.name as keyof typeof nessieBankApi;
      
      console.log(`[Gemini] Requested function call: ${functionName}`);
      console.log(`[Gemini] Arguments:`, functionCall.args);

      if (nessieBankApi[functionName]) {
        const args = functionCall.args;
        let functionResult: Record<string, unknown>;

        // FIX: Call API functions with named arguments to avoid issues with argument order from Object.values(). This also resolves the type error.
        switch (functionName) {
          case 'getAccountBalance':
            functionResult = await nessieBankApi.getAccountBalance(args.accountId as string);
            break;
          case 'getRecentTransactions':
            functionResult = await nessieBankApi.getRecentTransactions(args.accountId as string, args.count as number | undefined);
            break;
          case 'transferFunds':
            functionResult = await nessieBankApi.transferFunds(args.fromAccountId as string, args.toAccountId as string, args.amount as number);
            break;
        }
        
        console.log(`[Nessie] Function result:`, functionResult);

        // Send the function's result back to the model
        // FIX: `chat.sendMessage` expects an object with a `message` property. The function response is passed as a `Part` object within an array.
        response = await chat.sendMessage({
          message: [
            {
              functionResponse: {
                name: functionCall.name,
                response: functionResult,
              },
            },
          ],
        });

        // The model will now respond in natural language based on the function result.
        return response.text;
      } else {
        return `I'm sorry, I don't know how to do that. The function ${functionName} is not available.`;
      }
    }

    // If no function call, return the direct text response
    return response.text;
  },
};