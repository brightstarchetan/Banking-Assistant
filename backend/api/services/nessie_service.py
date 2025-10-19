import os
from typing import Dict, Any
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NessieBankService:
    def __init__(self):
        self.api_key = os.getenv('NESSIE_API_KEY')
        self.base_url = 'http://api.nessieisreal.com'

    def _fetch_nessie(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """Helper function for making authenticated API calls"""
        url = f"{self.base_url}{endpoint}?key={self.api_key}"
        
        try:
            if method == 'GET':
                response = requests.get(url)
            elif method == 'POST':
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if not response.ok:
                error_data = response.json()
                error_message = error_data.get('message', f"API request failed with status {response.status_code}")
                print(f"[Nessie] Error for endpoint {endpoint}: {error_message}")
                return {'success': False, 'error': error_message, 'status': response.status_code}

            # Handle 204 No Content
            if response.status_code == 204:
                return {'success': True, 'data': {}}

            return {'success': True, 'data': response.json()}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get the balance for a specific account"""
        print(f"[Nessie] Getting balance for account: {account_id}")
        result = self._fetch_nessie(f"/accounts/{account_id}")

        if result['success']:
            account = result['data']
            return {
                'success': True,
                'accountId': account_id,
                'balance': account['balance'],
                'nickname': account.get('nickname', 'Account'),
                'currency': 'USD'
            }
        else:
            error_msg = 'Account not found.' if result.get('status') == 404 else result.get('error')
            return {'success': False, 'error': error_msg}

    def get_recent_transactions(self, account_id: str, count: int = 5) -> Dict[str, Any]:
        """Get recent transactions for an account"""
        print(f"[Nessie] Getting {count} recent transactions for account: {account_id}")
        # result = requests.get(f"{self.base_url}/accounts/{account_id}/purchases?key={self.api_key}")
        result = requests.get("http://api.nessieisreal.com/accounts/68f42d2a9683f20dd51a02cd/purchases?key=304c4f4ba37b99aca211e38cdbcc8b2a")
        #result = self._fetch_nessie(f"/accounts/{account_id}/purchases")
        result = result.json()
        # print(f"Result: {result}")
        if result:
            print("Result is a success")
            # all_purchases = result['data']
            transactions = []
            
            for p in result:
                transactions.append({
                    'id': p['_id'],
                    'date': p['purchase_date'],
                    'description': p.get('description', f"Merchant {p['merchant_id']}"),
                    'amount': -p['amount'],  # Negative for debits
                    'type': 'debit'
                })
            
            return {'success': True, 'accountId': account_id, 'transactions': transactions}
        else:
            print("Result is a failure")
            error_msg = 'Account not found.' if result.get('status') == 404 else result.get('error')
            return {'success': False, 'error': error_msg}

    def transfer_funds(self, from_account_id: str, to_account_id: str, amount: float) -> Dict[str, Any]:
        """Transfer funds between accounts"""
        print(f"[Nessie] Transferring {amount} from {from_account_id} to {to_account_id}")
        
        transfer_data = {
            'medium': 'balance',
            'payee_id': to_account_id,
            'amount': amount,
            'transaction_date': datetime.now().strftime('%Y-%m-%d'),
            'description': f"Transfer from {from_account_id} to {to_account_id}"
        }

        result = self._fetch_nessie(
            f"/accounts/{from_account_id}/transfers",
            method='POST',
            data=transfer_data
        )

        if result['success']:
            response = result['data']
            return {
                'success': True,
                'message': 'Transfer successfully created.',
                'transactionId': response.get('objectCreated', {}).get('_id')
            }
        else:
            error_msg = ("Transfer failed. Please check account IDs and balance."
                        if "Validation" in str(result.get('error', ''))
                        else result.get('error'))
            return {'success': False, 'error': error_msg}

nessie_service = NessieBankService()
