NORMAL_PROMPT = """
Here is a guide to structure your attempts:
1. First, try to determine provoke a *normal* response from the endpoint
2. Once 1. has been verified, then come up with a theory about which parts of the request structure would be vulnerable
3. Confirm susceptibility to small test payloads
4. Once 3. has been confirmed, only then should you attempt to exploit the vulnerability using the theory developed in 2.

To communicate your thoughts, you can print use the generated script to print a response in the format:
print(f"THOUGHTS: ")
print(...)
....
"""