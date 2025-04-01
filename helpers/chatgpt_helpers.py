def get_chat_gpt_response(client, prompt):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o-mini",
        response_format={ "type": "json_object" }
    )

    return chat_completion.choices[0].message.content
