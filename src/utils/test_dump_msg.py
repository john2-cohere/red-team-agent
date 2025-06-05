import json

def dump_llm_messages_pretty(messages: list[dict[str, str]]) -> str:
	"""
	Serialize a list of LLM messages to a JSON-like string,
	with multiline content strings preserved as per the specific format.
	"""
	output_list_lines = ["["]  # Start of the entire list

	for i, msg_dict in enumerate(messages):
		role_json = json.dumps(msg_dict["role"])

		# Each line of content_input prefixed with two spaces for final output
		content_input = msg_dict["content"]
		indented_content_block = "\n".join(["  " + line for line in content_input.splitlines()])

		# Build the string for a single message dictionary
		message_block_lines = [
			"  {",  # Message object indented by 2 spaces
			f"    \"role\": {role_json},",  # Role indented by 4 spaces
			f"    \"content\": \"\"\"\n{indented_content_block}\n    \"\"\"",  # Content block with specific indentation
			"  }"  # Closing brace of message object, indented by 2
		]

		if i < len(messages) - 1:
			message_block_lines[-1] += ","  # Add comma if not the last message

		output_list_lines.extend(message_block_lines)

	output_list_lines.append("]")  # End of the entire list
	return "\n".join(output_list_lines)

if __name__ == "__main__":
    import logging
    
    logger = logging.getLogger(__name__)

	example_content_string = """You are presented with the following views from a browser
Here is the CURR_PAGE:
URL: about:blank

Here is the PREV_PAGE:
URL: None
None

Given the different views, determine if the CURR_PAGE is a:

1. new_page: different page of the application
2. updated_page: same page of the application, but with an updated view (ie. submenu expansion, pop-up)

Some things to keep in mind:
1. visible elements: the view presented only shows visible elements in the DOM; so elements that are on the same page might not be displayed because is_top_element == False or is_in_viewport == False

Which is why when considering whether the CURR_PAGE is a new_page or updated_page, make your decision by considering both the url and the DOM of the CURR_PAGE
Now make your choices"""

	messages_to_print = [
		{
			"role": "user",
			"content": example_content_string
		}
	]

	formatted_output = dump_llm_messages_pretty(messages_to_print)
	print("[PROMPT NEW PAGE]:")
	logger.info(f"hello??:\nformatted_output")
