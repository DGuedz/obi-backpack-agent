"""
fee_enforcer.py
----------------

Este módulo implementa a lógica de aplicação da taxa de sucesso (3%) do
protocolo OBI WORK.  Ele contém uma função para construir uma transação de
split que direciona a proporção correta de fundos tanto para o usuário quanto
para a tesouraria da Black Mindz.  O bot só deve executar transações de
saque ou claim que contenham este split matematicamente correto.
"""

from typing import Dict


# Endereço da tesouraria da Black Mindz.  Em um ambiente real, deve ser
# configurado de forma segura.
BLACK_MINDZ_TREASURY = "0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD"


def construct_split_transaction(amount: float, user_wallet: str) -> Dict[str, float]:
    """Constrói uma transação de saque/claim com split de 97/3.

    Calcula 3% de `amount` como taxa de protocolo e 97% como valor líquido para
    o usuário.  Retorna um dicionário representando os valores a serem
    transferidos.

    Args:
        amount: Montante total recebido (e.g., airdrop ou lucro).
        user_wallet: Endereço da wallet do usuário que receberá o valor líquido.

    Returns:
        dict: Um dicionário contendo os valores para o usuário e para a tesouraria.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    fee = amount * 0.03
    net_amount = amount - fee
    return {
        "user": net_amount,
        "treasury": fee,
        "user_wallet": user_wallet,
        "treasury_wallet": BLACK_MINDZ_TREASURY,
    }


def validate_split_transaction(tx: Dict[str, float]) -> bool:
    """Valida se uma transação contém o split correto.

    Verifica se a soma dos valores atribuídos ao usuário e à tesouraria equivale
    ao valor total esperado e se as proporções correspondem ao acordo de 97/3.

    Args:
        tx: Um dicionário retornado por construct_split_transaction.

    Returns:
        bool: True se o split estiver correto; caso contrário, False.
    """
    try:
        total = tx["user"] + tx["treasury"]
        expected_fee = total * 0.03
        expected_net = total - expected_fee
        # Comparação com tolerância para ponto flutuante
        return abs(tx["treasury"] - expected_fee) < 1e-8 and abs(tx["user"] - expected_net) < 1e-8
    except KeyError:
        return False


if __name__ == "__main__":
    # Exemplo de uso:
    tx = construct_split_transaction(1000.0, "0x1234567890abcdef1234567890abcdef12345678")
    print("Transação construída:", tx)
    print("Split válido?", validate_split_transaction(tx))