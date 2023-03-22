# Automated Code Review using the ChatGPT language model

## Import statements
import argparse
import openai
import os
import requests
from github import Github

## Adding command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--openai_api_key', help='Your OpenAI API Key')
parser.add_argument('--github_token', help='Your Github Token')
parser.add_argument('--github_pr_id', help='Your Github PR ID')
parser.add_argument('--openai_engine', default="text-davinci-002", help='GPT-3 model to use. Options: text-davinci-002, text-babbage-001, text-curie-001, text-ada-001')
parser.add_argument('--openai_temperature', default=0.5, help='Sampling temperature to use. Higher values means the model will take more risks. Recommended: 0.5')
parser.add_argument('--openai_max_tokens', default=2048, help='The maximum number of tokens to generate in the completion.')
parser.add_argument('--mode', default="files", help='PR interpretation form. Options: files, patch')
args = parser.parse_args()

## Authenticating with the OpenAI API
openai.api_key = args.openai_api_key

## Authenticating with the Github API
g = Github(args.github_token)


def review():
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    pull_request = repo.get_pull(int(args.github_pr_id))

    content = get_content_patch()

    if len(content) == 0:
        pull_request.create_issue_comment(f"Patch file does not contain any changes")
        return

    response = openai.ChatCompletion.create(
        model=args.openai_engine,
        messages=[{"role": "user", "content": "Bellow is the code patch, please help me do a brief code review," \
            "if any bug risk and improvement suggestion are welcome, diff:\n" + content}],
        # prompt=(f"Bellow is the code patch, please help me do a brief code review," \
        #     "if any bug risk and improvement suggestion are welcome, diff:\n```{diff_text}```"),
        temperature=float(args.openai_temperature),
        max_tokens=int(args.openai_max_tokens)
    )
    print(response)

    for choice in response['choices']:
        print(choice['message']['content'])
        pull_request.create_issue_comment(f"{choice['message']['content']}")



def get_content_patch():
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/pulls/{args.github_pr_id}"
    print(url)

    headers = {
        'Authorization': f"token {args.github_token}",
        'Accept': 'application/vnd.github.v3.diff'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        raise Exception(response.text)

    return response.text

if (args.mode == "review"):
    review()
