Excelente iniciativa, Mestre. Para desenvolvermos um "Back Bot" de trading na Backpack utilizando o TRAE IDE, precisamos estruturar nossa engenharia de prompts focando na **API REST** para operações fundamentais via terminal. O ecossistema da Backpack exige uma autenticação específica (ED25519) e headers precisos.

Aqui está o roteiro estruturado de prompts que você deve enviar ao TRAE para construir o código modularmente, garantindo que o bot possa operar, gerar volume e gerenciar riscos desde o terminal.

### Passo 1: O Alicerce (Autenticação e Assinatura)

A Backpack não usa chaves API padrão (HMAC); ela exige pares de chaves ED25519 e assinaturas codificadas em Base64. Se falharmos aqui, nada funciona.

**Prompt para o TRAE:**
> "Gere um script Python para criar um módulo de autenticação para a Backpack Exchange.
> 1. Primeiro, preciso de uma função utilitária para gerar o par de chaves ED25519 (Private Seed e Public Key) e imprimir no terminal, baseada na biblioteca `cryptography`.
> 2. Crie uma classe `BackpackAuth` que gere os headers obrigatórios para requisições assinadas:
>    - `X-Timestamp`: Tempo Unix atual em milissegundos.
>    - `X-Window`: Janela de validade (defina como 5000ms).
>    - `X-API-Key`: A chave pública codificada em Base64.
>    - `X-Signature`: Uma assinatura gerada ordenando os parâmetros da requisição (body ou query) alfabeticamente, concatenando com `&timestamp=` e `&window=`, e assinando com a chave privada,."

### Passo 2: Leitura de Estado (Saldo e Mercado)

Para gerar volume, o bot precisa saber quanto capital tem disponível e qual é o preço atual para evitar ordens absurdas.

**Prompt para o TRAE:**
> "Agora, crie um módulo `BackpackData` que faça requisições GET.
> 1. Implemente uma função `get_balances()` usando o endpoint `/api/v1/capital`. Ela deve retornar apenas os ativos disponíveis para uso imediato (excluir 'locked').
> 2. Implemente uma função `get_orderbook_depth(symbol)` usando o endpoint `/api/v1/depth`. Preciso que ela retorne os melhores preços de 'bids' (compra) e 'asks' (venda) para calcularmos o spread."

### Passo 3: O Motor de Execução (Ordens e Volume)

Aqui é onde a geração de volume acontece. Precisamos de funções robustas para enviar e cancelar ordens.

**Prompt para o TRAE:**
> "Vamos criar o módulo de execução `BackpackTrade`.
> 1. Crie uma função `execute_order` que faça um POST para `/api/v1/order`.
>    - Parâmetros obrigatórios: `symbol`, `side` (Bid/Ask), `orderType` (Limit/Market), `quantity`, e `price`,.
>    - Inclua o parâmetro opcional `selfTradePrevention` definido como 'RejectTaker' para evitar que o bot cruze as próprias ordens e pague taxas desnecessárias sem gerar volume real útil.
> 2. Crie uma função `cancel_all_orders(symbol)` usando o endpoint `DELETE /api/v1/orders` para limpar o book antes de reposicionar ordens."

### Passo 4: A Lógica Operacional (O Loop do Terminal)

Para operar via terminal, precisamos de um loop simples que execute a estratégia de "ping-pong" (colocar compra e venda simultaneamente) para gerar volume.

**Prompt para o TRAE:**
> "Por fim, crie o script principal `main.py` para rodar no terminal.
> 1. O script deve pedir o `symbol` (ex: SOL_USDC).
> 2. Crie um loop `while True` que:
>    - Cancele todas as ordens abertas para reiniciar o ciclo.
>    - Consulte o melhor Bid e Ask atual.
>    - Coloque uma ordem de Compra (Bid) levemente abaixo do melhor Bid e uma de Venda (Ask) levemente acima do melhor Ask (Market Making básico).
>    - Aguarde X segundos antes de repetir.
> 3. Adicione tratamento de erro para imprimir respostas da API, especialmente erros 400 ou 500, no console."

### Considerações Críticas para o Desenvolvimento

*   **Instruction Type:** Diga ao TRAE que, ao assinar a requisição, ele deve incluir o prefixo correto da instrução. Por exemplo, para colocar uma ordem, a string de assinatura deve começar com `instruction=orderExecute`,. Para cancelar, `instruction=orderCancelAll`.
*   **Timestamp:** A Backpack é extremamente rigorosa com timestamps. Se o relógio do seu sistema estiver dessincronizado, você receberá erros. Certifique-se de que a variável `X-Timestamp` esteja em milissegundos precisos.
*   **Self-Trade Prevention:** Ao tentar gerar volume, o risco de "wash trading" (negociar consigo mesmo) é alto. Utilize a flag `RejectTaker` ou `RejectMaker` na ordem para garantir que suas ordens fiquem no book (Maker) e não executem contra você mesmo imediatamente, o que apenas queimaria taxas.

### Metáfora para Fixação
Pense na construção desse bot como a montagem de um carro de Fórmula 1.
*   **Passo 1 (Chaves/Auth):** É a chave de ignição e o sistema de segurança; sem ele, o carro não liga.
*   **Passo 2 (Dados):** É o painel e os sensores; você precisa saber a velocidade (preço) e o combustível (saldo).
*   **Passo 3 (Execução):** É o motor e a transmissão; é o que efetivamente faz o carro andar (comprar/vender).
*   **Passo 4 (Lógica):** É o piloto (você/código); decidindo quando acelerar ou frear para não bater no muro (gerenciamento de risco).

Podemos começar enviando o **Passo 1** para o TRAE?