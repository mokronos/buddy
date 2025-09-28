import json

import requests


def handle_event(evt: dict) -> None:
    etype = evt.get("type")

    if etype == "RUN_STARTED":
        print(f"[RUN STARTED] thread={evt.get('threadId')} run={evt.get('runId')}")

    elif etype == "RUN_FINISHED":
        print(f"[RUN FINISHED] thread={evt.get('threadId')} run={evt.get('runId')} result={evt.get('result')}")

    elif etype == "RUN_ERROR":
        print(f"[RUN ERROR] code={evt.get('code')} msg={evt.get('message')}")

    elif etype == "STEP_STARTED":
        print(f"[STEP STARTED] {evt.get('stepName')}")

    elif etype == "STEP_FINISHED":
        print(f"[STEP FINISHED] {evt.get('stepName')}")

    elif etype == "TEXT_MESSAGE_START":
        print(f"[MSG START] id={evt.get('messageId')} role={evt.get('role')}")

    elif etype == "TEXT_MESSAGE_CONTENT":
        print(f"{evt.get('delta')}", end="")

    elif etype == "TEXT_MESSAGE_END":
        print(f"[MSG END] id={evt.get('messageId')}")

    elif etype == "TEXT_MESSAGE_CHUNK":
        print(f"{evt.get('delta')}", end="")

    elif etype == "TOOL_CALL_START":
        print(f"[TOOL CALL] name={evt.get('toolCallName')}")

    elif etype == "TOOL_CALL_ARGS":
        print(f"args={evt.get('delta')}")

    elif etype == "TOOL_CALL_END":
        # print(f"[TOOL CALL END] id={evt.get('toolCallId')}")
        pass

    elif etype == "TOOL_CALL_RESULT":
        print(f"[TOOL RESULT] {evt.get('content', '')[:200]}")

    elif etype == "STATE_SNAPSHOT":
        print(f"[STATE SNAPSHOT] {evt.get('snapshot')}")

    elif etype == "STATE_DELTA":
        print(f"[STATE DELTA] {evt.get('delta')}")

    elif etype == "MESSAGES_SNAPSHOT":
        print(f"[MESSAGES SNAPSHOT] {len(evt.get('messages', []))} messages")

    elif etype == "RAW":
        print(f"[RAW] source={evt.get('source')} event={evt.get('event')}")

    elif etype == "CUSTOM":
        print(f"[CUSTOM] name={evt.get('name')} value={evt.get('value')}")

    elif etype == "ACTIVITY_SNAPSHOT":
        print(
            f"[ACTIVITY SNAPSHOT] msg={evt.get('messageId')} type={evt.get('activityType')} content={evt.get('content')}"
        )

    elif etype == "ACTIVITY_DELTA":
        print(f"[ACTIVITY DELTA] msg={evt.get('messageId')} type={evt.get('activityType')} patch={evt.get('patch')}")

    elif etype == "REASONING_START":
        print(f"[REASONING START] msg={evt.get('messageId')}")

    elif etype == "REASONING_MESSAGE_START":
        print(f"[REASONING MSG START] msg={evt.get('messageId')} role={evt.get('role')}")

    elif etype == "REASONING_MESSAGE_CONTENT":
        print(f"[REASONING MSG CONTENT] msg={evt.get('messageId')} delta={evt.get('delta')}")

    elif etype == "REASONING_MESSAGE_END":
        print(f"[REASONING MSG END] msg={evt.get('messageId')}")

    elif etype == "REASONING_MESSAGE_CHUNK":
        print(f"[REASONING MSG CHUNK] msg={evt.get('messageId')} delta={evt.get('delta')}")

    elif etype == "REASONING_END":
        print(f"[REASONING END] msg={evt.get('messageId')}")

    elif etype == "META_EVENT":
        print(f"[META] type={evt.get('metaType')} payload={evt.get('payload')}")

    else:
        print(f"[UNKNOWN EVENT] {evt}")


def main(prompt: str):
    url = "http://127.0.0.1:8000/"

    payload = {
        "threadId": "thread-1",
        "runId": "run-1",
        "state": {},
        "tools": [],
        "context": [],
        "forwardedProps": {},
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "id": "message-1",
            }
        ],
    }

    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }

    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        for chunk in response.iter_lines(decode_unicode=True):
            if chunk == "":
                continue

            evt_data = chunk.split(":", 1)[1]

            evt_data_json = json.loads(evt_data)

            handle_event(evt_data_json)


if __name__ == "__main__":
    main(
        "Are there news about kai cenat and skating? Give me a detailed answer. Go through multiple sources, and reevaluate your search strategy after retrieving some results. Don't only search, but also retrieve the full pages, to get more context"
    )
    # main("What was my last question and your last answer?")
