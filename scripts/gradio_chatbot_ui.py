import uuid

import gradio as gr
import requests

SESSION_ID = uuid.uuid4()
API_ENDPOINT = "http://localhost:8000/kitsune-chatbot/chat"

predefined_questions = [
    "How many draft policies are there?",
    "How many total policies are there?",
    "Can you help me with my children's homework?",
]


def chat_with_bot(message, chat_history):
    if not message.strip():
        return "", chat_history  # ignore empty messages
    try:
        response = requests.post(
            API_ENDPOINT, json={"session_id": str(SESSION_ID), "question": message}
        )
        response.raise_for_status()
        answer = response.json().get("answer", "")
    except Exception as e:
        answer = f"Error: {str(e)}"
    chat_history = chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return "", chat_history


def set_message(question):
    return question


with gr.Blocks(title="Kitsune Chatbot") as demo:
    gr.Markdown("# Kitsune Chatbot")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=500, elem_id="chatbot", label="Chat History", type="messages"
            )
            msg = gr.Textbox(
                placeholder="Type your question here...", label="Your Message"
            )
            send_btn = gr.Button("Send")

        with gr.Column(scale=1):
            gr.Markdown("### Example Questions")
            for question in predefined_questions:
                btn = gr.Button(question)
                # When button is clicked, set the textbox value to the question
                btn.click(
                    fn=lambda q=question: q, outputs=msg  # Returns the question text
                )

    send_btn.click(chat_with_bot, inputs=[msg, chatbot], outputs=[msg, chatbot])
    msg.submit(chat_with_bot, inputs=[msg, chatbot], outputs=[msg, chatbot])

if __name__ == "__main__":
    demo.launch()
