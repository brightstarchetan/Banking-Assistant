import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from .nessie_service import NessieBankService

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

SYSTEM_INSTRUCTION = """You are a helpful and professional banking assistant for 'Nessie Bank'.
- Your primary goal is to help users by calling the available functions based on their requests.
- When you need information like an account ID, ask the user for it clearly.
- CRITICAL: User account IDs are numbers, but they may speak them as words (e.g., "one two three four"). You MUST convert these words to digits.
- CRITICAL: The banking system requires account IDs to have the prefix 'acc-'. After converting words to digits, you must prepend 'acc-' to the ID before calling any function.
- Be concise and clear in your responses."""

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.nessie_service = NessieBankService()
        self.chat = None
        self.start_chat()

    def start_chat(self):
        """Initialize a new chat session"""
        self.chat = self.model.start_chat(history=[])
        # Send system instruction
        self.chat.send_message(SYSTEM_INSTRUCTION)

    def run_conversation(self, user_input: str, curr_user_name: str, curr_user_id: str, curr_account_id: str) -> str:
        """Process user input and return the response"""
        try:
            # Send user message and get response
            transactions = self.nessie_service.get_recent_transactions(curr_account_id, 10)
            print(f"Recent Transactions for Account {curr_account_id}: {transactions}")
            system_prompt = """
            System prompt: Please analyse the following recent transactions for the user and predict
            to their spending habits, categorizing expenses and identifying any unusual activity. 
            Give them advice on managing their finances based on these transactions. Please respond in 4 sentences.
            """
            
            print("Message sent to Gemini")
            print(system_prompt + " User Input: " + user_input + f" (User: {curr_user_name}, UserID: {curr_user_id}, AccountID: {curr_account_id}), Recent Transactions: {transactions}")
            response = self.chat.send_message(system_prompt + " User Input: " + user_input + f" (User: {curr_user_name}, UserID: {curr_user_id}, AccountID: {curr_account_id}), Recent Transactions: {transactions}")
            

            # Check if we need to call any banking functions
            # This is a simplified version - in practice, you'd need to implement
            # function calling based on the response content
            
            # For now, we'll use basic keyword matching
            response_text = response.text.lower()
            
            
            
            # if 'balance' in response_text:
            #     # Extract account ID from response
            #     # This is a simplified example - you'd need more robust parsing
            #     account_id = self._extract_account_id(response_text)
            #     if account_id:
            #         balance_info = self.nessie_service.get_account_balance(account_id)
            #         return self._format_balance_response(balance_info)
                    
            # elif 'transfer' in response_text:
            #     # Handle transfer logic
            #     # This is a simplified example
            #     from_account, to_account, amount = self._extract_transfer_details(response_text)
            #     if all([from_account, to_account, amount]):
            #         transfer_result = self.nessie_service.transfer_funds(
            #             from_account, to_account, float(amount)
            #         )
            #         return self._format_transfer_response(transfer_result)
            
            return response_text

        except Exception as e:
            print(f"Error in conversation: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Could you please try again?"

    def _extract_account_id(self, text: str) -> Optional[str]:
        """Extract account ID from text - simplified example"""
        # This would need more sophisticated parsing in practice
        import re
        match = re.search(r'acc-(\d+)', text)
        return match.group(0) if match else None

    def _extract_transfer_details(self, text: str) -> tuple[Optional[str], Optional[str], Optional[float]]:
        """Extract transfer details from text - simplified example"""
        # This would need more sophisticated parsing in practice
        # Returns (from_account, to_account, amount)
        return None, None, None

    def _format_balance_response(self, balance_info: Dict[str, Any]) -> str:
        """Format balance information into a response"""
        if balance_info.get('success'):
            return f"Your account balance is ${balance_info['balance']:.2f}"
        return "I'm sorry, I couldn't retrieve your balance at this time."

    def _format_transfer_response(self, transfer_result: Dict[str, Any]) -> str:
        """Format transfer result into a response"""
        if transfer_result.get('success'):
            return "The transfer was completed successfully."
        return f"I'm sorry, the transfer couldn't be completed: {transfer_result.get('error', 'Unknown error')}"

gemini_service = GeminiService()
