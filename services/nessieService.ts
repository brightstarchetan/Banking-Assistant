// This service has been updated to use the real Capital One Nessie API.

const NESSIE_API_KEY = '304c4f4ba37b99aca211e38cdbcc8b2a';
const BASE_URL = 'http://api.nessieisreal.com';

// A helper function for making authenticated API calls
const fetchNessie = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${BASE_URL}${endpoint}?key=${NESSIE_API_KEY}`;
    const response = await fetch(url, options);
    if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.message || `API request failed with status ${response.status}`;
        console.error(`[Nessie] Error for endpoint ${endpoint}:`, errorMessage);
        return { success: false, error: errorMessage, status: response.status };
    }
    // Handle 204 No Content for successful deletions or updates
    if (response.status === 204) {
        return { success: true, data: {} };
    }
    return { success: true, data: await response.json() };
};


const getAccountBalance = async (accountId: string): Promise<Record<string, unknown>> => {
  console.log(`[Nessie] Getting balance for account: ${accountId}`);
  const result = await fetchNessie(`/accounts/${accountId}`);

  if (result.success) {
    const account = result.data as { balance: number; nickname: string };
    return {
      success: true,
      accountId,
      balance: account.balance,
      nickname: account.nickname,
      currency: 'USD',
    };
  } else {
    return { success: false, error: result.status === 404 ? 'Account not found.' : result.error };
  }
};

const getRecentTransactions = async (accountId: string, count: number = 5): Promise<Record<string, unknown>> => {
  console.log(`[Nessie] Getting ${count} recent transactions for account: ${accountId}`);
  // The Nessie API uses "purchases" for transactions
  const result = await fetchNessie(`/accounts/${accountId}/purchases`);

  if (result.success) {
    const allPurchases = result.data as any[];
    // The API doesn't support a count parameter, so we slice the result
    const transactions = allPurchases.slice(0, count).map(p => ({
        id: p._id,
        date: p.purchase_date,
        description: p.description || `Merchant ${p.merchant_id}`,
        amount: -p.amount, // Nessie amounts are positive, so we make them negative for debits
        type: 'debit',
    }));
    return { success: true, accountId, transactions };
  } else {
     return { success: false, error: result.status === 404 ? 'Account not found.' : result.error };
  }
};

const transferFunds = async (fromAccountId: string, toAccountId: string, amount: number): Promise<Record<string, unknown>> => {
  console.log(`[Nessie] Transferring ${amount} from ${fromAccountId} to ${toAccountId}`);
  
  const transferRequest = {
    medium: 'balance',
    payee_id: toAccountId,
    amount: amount,
    transaction_date: new Date().toISOString().split('T')[0],
    description: `Transfer from ${fromAccountId} to ${toAccountId}`
  };

  const result = await fetchNessie(`/accounts/${fromAccountId}/transfers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(transferRequest)
  });

  if (result.success) {
    const response = result.data as { objectCreated?: { _id: string } };
    return {
      success: true,
      message: 'Transfer successfully created.',
      transactionId: response.objectCreated?._id,
    };
  } else {
     // Nessie API doesn't give a specific "insufficient funds" error, so we generalize
     if (result.error?.toString().includes("Validation")) {
        return { success: false, error: "Transfer failed. Please check account IDs and balance." };
     }
     return { success: false, error: result.error };
  }
};

export const nessieBankApi = {
  getAccountBalance,
  getRecentTransactions,
  transferFunds,
};
