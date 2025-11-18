                elif Agent.is_call_tools_node(node):
                    # A handle-response node => The model returned some data, potentially calls a tool
                    async with node.stream(agent_run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                console.print(Markdown(
                                    f"[Tool] {event.part.tool_name!r} called with args={event.part.args}"
                                ))
                            elif isinstance(event, FunctionToolResultEvent):
                                console.print(Markdown(
                                    f"[Tool] {event.result.tool_name!r} returned => {event.result.content}"
                                ))
