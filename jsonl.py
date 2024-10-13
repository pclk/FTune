import jsonlines
import json


def parse_conversation_file(file_path, include_tool):
    conversations = []
    current_messages = []
    current_system_message = ""
    in_system_prompt = False

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        if line.startswith("<system>"):
            in_system_prompt = True
            current_system_message = ""
            continue
        elif line.startswith("</system>"):
            in_system_prompt = False
            continue

        if in_system_prompt:
            current_system_message += line + " "
        elif line.startswith("---"):  # New conversation marker
            if current_messages:
                conversations.append(
                    {
                        "messages": [
                            {
                                "role": "system",
                                "content": current_system_message.strip(),
                            }
                        ]
                        + current_messages
                    }
                )
                current_messages = []
        elif line.startswith("user:"):
            content = line.replace("user:", "").strip()
            current_messages.append({"role": "user", "content": content})
        elif line.startswith("ai:"):
            content = line.replace("ai:", "").strip()
            current_messages.append({"role": "assistant", "content": content})
        elif line.startswith("tool_calls:") and include_tool:
            # Parse tool calls line (unchanged)
            content = line.replace("tool_calls:", "").strip()
            function_name = content.split("(")[0]
            try:
                args_str = content[content.index("(") + 1 : content.index(")")]
            except ValueError:
                print("Malformed tool_calls")
                exit()
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
        elif line.startswith("tool:") and include_tool:
            # Parse tool response (unchanged)
            content = line.replace("tool:", "").strip()
            current_messages.append(
                {"role": "tool", "tool_call_id": "call_id", "content": content}
            )

    # Add the last conversation
    if current_messages:
        conversations.append(
            {
                "messages": [
                    {"role": "system", "content": current_system_message.strip()}
                ]
                + current_messages
            }
        )

    return conversations


def convert_to_jsonl(input_file, output_file, include_tool):
    conversations = parse_conversation_file(input_file, include_tool)
    with jsonlines.open(output_file, "w") as writer:
        writer.write_all(conversations)
    print(f"Wrote {len(conversations)} messages.")


# Usage
convert_to_jsonl("sales_tool.priv.txt", "conversations.jsonl", False)
