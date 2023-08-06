import os
import json
import openai

openai.api_key = os.environ['OPENAI_API_KEY']
GPT = 'gpt-3.5-turbo'
question = "what is terraform used for?"
context = [
    {"role": "system", "content": ""},
    {"role": "user", "content": question}
]


def save_history(prompt, response):
    print("prompt:", prompt)
    print("response:", response)
    #
    # print("message_log:", message_log)
    content = prompt + [(dict(response))]
    print("content:", content)
    content_log = [": ".join(m.values()) for m in content]
    print("content_log:", content_log)

    with open(f"history/history.txt", 'a') as f:
        print("file opened")
        for msg in content_log:
            f.write(f"{msg}\n")
        f.write("\n")

    json_data = []
    print("path check:", os.path.exists("history/history.json"))
    if os.path.exists("history/history.json"):
        with open("history/history.json", 'r') as fp:
            json_data = json.load(fp)

    print("json_data:", json_data + [content])

    with open(f"history/history.json", 'w+') as f:
        json.dump(json_data + [content], f, indent=1)
        # f.write(os.linesep)

    # with open(f"history/history.csv", 'w') as f:
    #     fieldnames = ['role', 'content']
    #     writer = csv.DictWriter(f, fieldnames=fieldnames)
    #     writer.writeheader()
    #     for d in session_context[1:]:
    #         writer.writerow(d)


completion = openai.ChatCompletion.create(
    model=GPT,
    messages=context,
    temperature=0.1
)

# print(completion.choices[0].message)
save_history(context, completion.choices[0].message)
