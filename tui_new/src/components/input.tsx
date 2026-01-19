import { createSignal } from "solid-js"

const Input = () => {
    const [inputValue, setInputValue] = createSignal("")

    const onInput = (value: string) => {
        setInputValue(value)
    }

    return (
        <box height={4} bottom={0} position="absolute" border>
            <text>Namskjf: {inputValue()}</text>
            <input focused onInput={onInput} />
        </box>
    )
}

export default Input
