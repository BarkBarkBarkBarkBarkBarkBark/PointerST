import streamlit as st
import openai  # Import the openai module

# Import the weaviate_process function
from weaviate_integration import weaviate_process

# Set the OpenAI API key
openai_api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openai_api_key  # Set the API key

st.title("BOINKBOT")

# Sidebar for system prompt editing
st.sidebar.header("Customize the Chatbot's Personality")

default_prompt = (
    "You are a helpful bot whose job it is to identify the sort of resource that the user might need."
)
system_prompt = st.sidebar.text_area("System Prompt:", value=default_prompt, height=300)

# Initialize session state for chat history
if "messages" not in st.session_state or st.sidebar.button("Reset Conversation"):
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
else:
    # Update the system prompt if it has changed
    st.session_state.messages[0]["content"] = system_prompt

# Display existing chat messages
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input using st.chat_input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Use your existing code to process the input
    try:
        # Call the weaviate_process function
        results = weaviate_process(user_input)

        if isinstance(results, list):
            import pandas as pd
            df = pd.DataFrame(results)

            # Generate a generative touch using OpenAI
            # Prepare the prompt for OpenAI
            introduction_prompt = (
                f"{system_prompt}\n\n"
                f"User query: {user_input}\n"
                f"Based on the above query, provide a brief greeting, do not elaborate or suggest anything."
            )

            # Call OpenAI API to generate the introduction
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": introduction_prompt}
                ],
                max_tokens=50,
                temperature=0.2,
            )
            introduction = response.choices[0].message.content.strip()

            assistant_message = introduction + "\n\n"

            # Convert DataFrame to Markdown
            assistant_message += df.to_markdown(index=False)
        else:
            assistant_message = results  # It's an error message

        # When displaying the message
        with st.chat_message("assistant"):
            st.markdown(assistant_message)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        assistant_message = (
            "I'm sorry, but I couldn't retrieve information to answer your question."
        )

        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

        # Display assistant message
        with st.chat_message("assistant"):
            st.markdown(assistant_message)

    # Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

# Sidebar instructions
st.sidebar.markdown("---")
st.sidebar.markdown("### Instructions:")
st.sidebar.markdown(
    """
1. **Edit the System Prompt** to customize the bot's personality.
2. **Type your message** in the chat input box below.
3. **Reset Conversation** to start over.
"""
)
