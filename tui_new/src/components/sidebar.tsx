import { useTerminalDimensions, type JSX } from "@opentui/solid"

function Sidebar() {
    const dimensions = useTerminalDimensions()

    return (
        <box flexGrow={1} height={dimensions().height * 0.9} width={dimensions().width * 0.2} border>
        </box>
    )
}

export default Sidebar
