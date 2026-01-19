import { createSignal } from "solid-js"

const Input = () => {
    const [inputValue, setInputValue] = createSignal("")

    return (
        <box height={4} border>
            <text>Name: {inputValue()}</text>
            <input focused onInput={(value) => setInputValue(value)} />
        </box>
    )
}

export default Input
