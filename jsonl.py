import jsonlines
import json


def parse_conversation_file(file_path):
    conversations = []
    current_messages = []
    current_system_message = ""

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        if line.startswith("---"):  # New conversation marker
            if current_messages:
                conversations.append(
                    {
                        "messages": [
                            {"role": "system", "content": current_system_message}
                        ]
                        + current_messages
                    }
                )
                current_messages = []
            continue

        if line.startswith("system:"):
            current_system_message = line.replace("system:", "").strip()
            continue

        if line.startswith("user:"):
            content = line.replace("user:", "").strip()
            current_messages.append({"role": "user", "content": content})
        elif line.startswith("ai:"):
            content = line.replace("ai:", "").strip()
            current_messages.append({"role": "assistant", "content": content})
        elif line.startswith("tool_calls:"):
            # Parse tool calls line
            content = line.replace("tool_calls:", "").strip()
            function_name = content.split("(")[0]
            try:
                args_str = content[content.index("(") + 1 : content.index(")")]
            except ValueError:
                print("Malformed tool_calls")

            # Parse arguments
            args_dict = {}
            if args_str:
                args = args_str.split(",")
                for arg in args:
                    if ":" in arg:
                        key, value = arg.split(":", 1)
                        args_dict[key.strip()] = value.strip().strip('"')

            # Create tool call message
            tool_call = {
                "id": "call_id",
                "type": "function",
                "function": {"name": function_name, "arguments": json.dumps(args_dict)},
            }
            current_messages.append({"role": "assistant", "tool_calls": [tool_call]})
        elif line.startswith("tool:"):
            # Parse tool response
            content = line.replace("tool:", "").strip()
            current_messages.append(
                {"role": "tool", "tool_call_id": "call_id", "content": content}
            )

    # Add the last conversation
    if current_messages:
        conversations.append(
            {
                "messages": [{"role": "system", "content": current_system_message}]
                + current_messages
            }
        )

    return conversations


def convert_to_jsonl(input_file, output_file):
    conversations = parse_conversation_file(input_file)
    with jsonlines.open(output_file, "w") as writer:
        writer.write_all(conversations)
    print(f"Wrote {len(conversations)} messages.")


# Usage
convert_to_jsonl("conversations.priv.txt", "conversations.jsonl")
