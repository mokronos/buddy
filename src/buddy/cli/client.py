"""
CLI client that connects to the A2A server.

This is the main CLI frontend that acts as an A2A client,
connecting to the A2A server to interact with the agent.
"""


class CLIClient:
    """CLI client for interacting with the Buddy agent via A2A protocol."""

    def __init__(self):
        """Initialize the CLI client."""
        self.running = False

    async def run(self):
        """Run the CLI client main loop."""
        self.running = True
        print("Buddy CLI starting...")
        print("Type 'exit' to quit")

        while self.running:
            try:
                # Get user input
                user_input = input("\n> ")

                if user_input.lower() in ["exit", "quit", "q"]:
                    self.running = False
                    break

                # TODO: Send request to A2A server
                # TODO: Handle streaming responses
                # For now, just echo
                print(f"Echo: {user_input}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                self.running = False
                break
            except Exception as e:
                print(f"Error: {e}")

        print("Buddy CLI stopped.")

    async def stop(self):
        """Stop the CLI client."""
        self.running = False
