
import { FunctionDeclaration, Type } from '@google/genai';

export const ELEVENLABS_VOICE_ID = '21m00Tcm4TlvDq8ikWAM'; // A common voice (Rachel)

export const nessieFunctionDeclarations: FunctionDeclaration[] = [
  {
    name: 'getAccountBalance',
    description: 'Get the balance for a specific bank account.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        accountId: {
          type: Type.STRING,
          description: 'The ID of the account to check.',
        },
      },
      required: ['accountId'],
    },
  },
  {
    name: 'getRecentTransactions',
    description: 'Get a list of recent transactions for a specific account.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        accountId: {
          type: Type.STRING,
          description: 'The ID of the account.',
        },
        count: {
          type: Type.INTEGER,
          description: 'The number of recent transactions to retrieve. Defaults to 5.',
        },
      },
      required: ['accountId'],
    },
  },
  {
    name: 'transferFunds',
    description: 'Transfer funds between two bank accounts.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        fromAccountId: {
          type: Type.STRING,
          description: 'The ID of the account to transfer funds from.',
        },
        toAccountId: {
          type: Type.STRING,
          description: 'The ID of the account to transfer funds to.',
        },
        amount: {
          type: Type.NUMBER,
          description: 'The amount of money to transfer.',
        },
      },
      required: ['fromAccountId', 'toAccountId', 'amount'],
    },
  },
];

export const Icons = {
  Mic: (props: React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m12 7.5v-1.5a6 6 0 0 0-6-6.75v-1.5a6.75 6.75 0 0 1 6.75 6.75v1.5m-6.75-6.75a6.75 6.75 0 0 0-6.75 6.75v1.5m6.75-6.75v-1.5m0 1.5v-1.5m0 0a2.25 2.25 0 0 0-2.25 2.25v1.5a2.25 2.25 0 0 0 2.25 2.25m0-3.75a2.25 2.25 0 0 1 2.25 2.25v1.5a2.25 2.25 0 0 1-2.25 2.25m0-3.75V3.75m0 0A2.25 2.25 0 0 0 9.75 6v1.5a2.25 2.25 0 0 0 2.25 2.25m0-3.75A2.25 2.25 0 0 1 14.25 6v1.5a2.25 2.25 0 0 1-2.25 2.25" />
    </svg>
  ),
  Stop: (props: React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 7.5A2.25 2.25 0 0 1 7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9Z" />
    </svg>
  ),
  Spinner: (props: React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  ),
};
