from openai import OpenAI

# pega a chave api do env da openai
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key = "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",
)

# define o modelo da ia e "personaliza" ela
def pergunta(input):
  return client.chat.completions.create(
  model="sao10k/l3.1-euryale-70b",
  messages=[
    {
      "role": "user",
      "content": input,
      },
    ],
  )

# função para colocar o prompt
def conversa(tema, linhas):
  # define a persona da ia, seria como um "fine-tuning" básico
  rule = "Responda e insira uma pergunta no final. Responda apenas em português e com caracteres do utf-8"
  resposta = pergunta(f"{rule}. Inicie uma conversa sobre {tema}.")

  print(resposta.choices[0].message.content)

  for i in range(linhas):
    resposta = pergunta(f"{rule}. {resposta}")
    print(f'{i}, {resposta.choices[0].message.content}')
    print()

conversa('experimentação', 10)