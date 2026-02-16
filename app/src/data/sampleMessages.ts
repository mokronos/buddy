export interface Message {
  id: string;
  type: 'ai' | 'human' | 'tool' | 'tool-call';
  content: string;
  timestamp?: string;
  toolName?: string;
  toolStatus?: 'success' | 'error' | 'running';
  toolCallId?: string;
  toolCallArgs?: unknown;
  toolResultData?: unknown;
  toolCallParams?: string;
  toolResult?: string;
}

export const sampleMessages: Message[] = [
  {
    id: '1',
    type: 'human',
    content: 'Add a few random tasks to my todo list for today.',
    timestamp: '09:10 AM'
  },
  {
    id: '2',
    type: 'tool-call',
    toolName: 'todoadd',
    toolStatus: 'success',
    toolCallId: 'call_todoadd_1',
    toolCallArgs: {
      todos: [
        { id: 'todo-1', content: 'Buy groceries', status: 'pending', priority: 'high' },
        { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'medium' },
        { id: 'todo-3', content: 'Go for a 30 minute run', status: 'in_progress', priority: 'low' }
      ]
    },
    toolResultData: [
      { id: 'todo-1', content: 'Buy groceries', status: 'pending', priority: 'high' },
      { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'medium' },
      { id: 'todo-3', content: 'Go for a 30 minute run', status: 'in_progress', priority: 'low' }
    ],
    content: 'Added 3 todos.',
    timestamp: '09:10 AM'
  },
  {
    id: '3',
    type: 'ai',
    content: 'Done. I added 3 items to your list and marked your run as already in progress.',
    timestamp: '09:10 AM'
  },
  {
    id: '4',
    type: 'human',
    content: 'Mark groceries as completed and raise the dentist one to high priority.',
    timestamp: '09:12 AM'
  },
  {
    id: '5',
    type: 'tool-call',
    toolName: 'todoupdate',
    toolStatus: 'success',
    toolCallId: 'call_todoupdate_1',
    toolCallArgs: {
      id: 'todo-1',
      patch: { status: 'completed' }
    },
    toolResultData: {
      before: { id: 'todo-1', content: 'Buy groceries', status: 'pending', priority: 'high' },
      after: { id: 'todo-1', content: 'Buy groceries', status: 'completed', priority: 'high' },
      todos: [
        { id: 'todo-1', content: 'Buy groceries', status: 'completed', priority: 'high' },
        { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'medium' },
        { id: 'todo-3', content: 'Go for a 30 minute run', status: 'in_progress', priority: 'low' }
      ]
    },
    content: 'Updated todo-1.',
    timestamp: '09:12 AM'
  },
  {
    id: '6',
    type: 'tool-call',
    toolName: 'todoupdate',
    toolStatus: 'success',
    toolCallId: 'call_todoupdate_2',
    toolCallArgs: {
      id: 'todo-2',
      patch: { priority: 'high' }
    },
    toolResultData: {
      before: { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'medium' },
      after: { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'high' },
      todos: [
        { id: 'todo-1', content: 'Buy groceries', status: 'completed', priority: 'high' },
        { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'high' },
        { id: 'todo-3', content: 'Go for a 30 minute run', status: 'in_progress', priority: 'low' }
      ]
    },
    content: 'Updated todo-2.',
    timestamp: '09:12 AM'
  },
  {
    id: '7',
    type: 'ai',
    content: 'Both updates are done. Want me to show the latest todo list?',
    timestamp: '09:12 AM'
  },
  {
    id: '8',
    type: 'human',
    content: 'Yes, and remove the running task.',
    timestamp: '09:13 AM'
  },
  {
    id: '9',
    type: 'tool-call',
    toolName: 'tododelete',
    toolStatus: 'success',
    toolCallId: 'call_tododelete_1',
    toolCallArgs: {
      ids: ['todo-3']
    },
    toolResultData: [
      { id: 'todo-1', content: 'Buy groceries', status: 'completed', priority: 'high' },
      { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'high' }
    ],
    content: 'Deleted todo-3.',
    timestamp: '09:13 AM'
  },
  {
    id: '10',
    type: 'tool-call',
    toolName: 'todoread',
    toolStatus: 'success',
    toolCallId: 'call_todoread_1',
    toolCallArgs: {},
    toolResultData: [
      { id: 'todo-1', content: 'Buy groceries', status: 'completed', priority: 'high' },
      { id: 'todo-2', content: 'Book dentist appointment', status: 'pending', priority: 'high' }
    ],
    content: 'Read current todo list.',
    timestamp: '09:13 AM'
  },
  {
    id: '11',
    type: 'ai',
    content: 'Here is your current list: groceries is completed, and the dentist appointment is pending with high priority.',
    timestamp: '09:13 AM'
  }
];
