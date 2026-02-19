# Big Idea

## Independent A2A Agents

- Each agent is a separate process or docker container
- Can easily create new agents via a dashboard
- PydanticAI with A2A Executor

## Communication between Agents

- Keep as human as possible
- Each agent has a communication tool
    - can send an async task to another agent (which it is allowed to)
    - can check status of task
- Agents could communicate in chats as well, e.g. discord channels
    - each agent has discord tool and is a separate bot

## Dashboard

- See all active agents
- See which agent can communicate with which other agents
- Change communication permissions (via central db)
- Chat with any agent
- Be able to define triggers, which agents should react to
    - Email (can have their own email address)
    - Discord (can have their own discord account/bot)
    - Time based e.g. cron job
