# Context Management

## Components

- System Message
    - General instructions
    - Tool definitions (via api)
    - Skill descriptions/names/paths
- User Message
- Agent Message
- Tool Message


## How to handle skills

### System Message


- Simple
- Cache is gone when updating skills during thread

### Skill search tool

- Just give agent a tool to seach (b25 or keyword)
- Tell agent to search for relevant skills every time in the beginning of a task




# General Approach
- Give agent general tools
    - search for skills/mcp_tools/memories
- More requests necessary
- Longer running updating threads
- caching works (up to compaction)
