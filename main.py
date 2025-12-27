import argparse
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import system_prompt
from call_function import available_functions, call_function

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment. Did you create your .env file?")

    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        )
    )

    if response.usage_metadata is None:
        raise RuntimeError("Usage Metadata not available")
    if args.verbose:
        print(f"User prompt: {args.user_prompt}")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

    if response.function_calls:
        function_results = []

        for function_call in response.function_calls:
            # Call our helper that actually runs the tool
            function_call_result = call_function(function_call, verbose=args.verbose)

            # 1. Ensure parts list is not empty
            parts = function_call_result.parts
            if not parts:
                raise RuntimeError("Function call result has no parts")

            # 2. Ensure function_response exists
            func_response = parts[0].function_response
            if func_response is None:
                raise RuntimeError("Function call part has no function_response")

            # 3. Ensure the response field is not None
            response_dict = func_response.response
            if response_dict is None:
                raise RuntimeError("FunctionResponse has no response payload")

            # 4. Save this part for later use
            function_results.append(parts[0])

            # 5. If verbose, print the result
            if args.verbose:
                print(f"-> {response_dict}")
    else:
        print(f"I'M JUST A ROBOT {response.text}")

if __name__ == "__main__":
    main()