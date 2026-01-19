export interface Message {
  id: string;
  type: 'ai' | 'human' | 'tool';
  content: string;
  timestamp?: string;
  toolName?: string;
  toolStatus?: 'success' | 'error' | 'running';
}

export const sampleMessages: Message[] = [
  {
    id: '1',
    type: 'human',
    content: 'Hello! Can you help me understand how flexbox works in CSS?',
    timestamp: '10:30 AM'
  },
  {
    id: '2',
    type: 'ai',
    content: 'Of course! Flexbox is a CSS layout module that makes it easy to create flexible and responsive layouts. Let me explain the key concepts:\n\n1. **Display: flex** - Turns an element into a flex container\n2. **flex-direction** - Controls the direction (row, column, etc.)\n3. **justify-content** - Aligns items along the main axis\n4. **align-items** - Aligns items along the cross axis\n\nWould you like me to show you a practical example?',
    timestamp: '10:31 AM'
  },
  {
    id: '3',
    type: 'tool',
    toolName: 'Code Search',
    content: 'Searching for flexbox examples in the codebase...',
    toolStatus: 'running',
    timestamp: '10:31 AM'
  },
  {
    id: '4',
    type: 'tool',
    toolName: 'Code Search',
    content: 'Found 15 flexbox examples across 8 files. Key patterns include:\n- .flex for container\n- .items-center for vertical centering\n- .justify-between for space distribution\n- .flex-col for column layouts',
    toolStatus: 'success',
    timestamp: '10:32 AM'
  },
  {
    id: '5',
    type: 'human',
    content: 'That\'s helpful! Can you show me how to create a sidebar layout with flexbox?',
    timestamp: '10:33 AM'
  },
  {
    id: '6',
    type: 'ai',
    content: 'Absolutely! Here\'s how you can create a sidebar layout using flexbox:\n\n```css\n.container {\n  display: flex;\n  height: 100vh;\n}\n\n.sidebar {\n  width: 250px;\n  background: #f5f5f5;\n}\n\n.main-content {\n  flex: 1;\n  padding: 20px;\n}\n```\n\nThe key is using `flex: 1` on the main content area to make it take up the remaining space after the fixed-width sidebar.',
    timestamp: '10:34 AM'
  },
  {
    id: '7',
    type: 'tool',
    toolName: 'File Editor',
    content: 'Creating example sidebar layout component...',
    toolStatus: 'running',
    timestamp: '10:34 AM'
  },
  {
    id: '8',
    type: 'tool',
    toolName: 'File Editor',
    content: 'Successfully created SidebarLayout.tsx with flexbox implementation.',
    toolStatus: 'success',
    timestamp: '10:35 AM'
  }
];