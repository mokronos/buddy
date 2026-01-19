import { useTerminalDimensions } from "@opentui/solid"
import { type JSX } from "solid-js"

function Container(props: {children: JSX.Element}) {
    const dimensions = useTerminalDimensions()

    return (
        <box flexGrow={1} height={dimensions().height} width={dimensions().width} border>
            {props.children}
        </box>
    )
}

export default Container
