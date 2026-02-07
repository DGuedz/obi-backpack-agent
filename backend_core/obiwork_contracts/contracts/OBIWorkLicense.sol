// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title OBI Work License (The Gatekeeper)
 * @dev Emite licenças de acesso ao bot OBI Work como NFTs.
 * Aceita pagamento em USDC.
 */
contract OBIWorkLicense is ERC721URIStorage, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    using SafeERC20 for IERC20;
    Counters.Counter private _tokenIds;

    IERC20 public usdcToken;
    
    // Mapping de Tier ID para Preço em USDC (com 6 casas decimais)
    mapping(uint256 => uint256) public tierPrices;
    
    // Mapping de Endereço para Tier Ativo (0 = Sem Acesso)
    mapping(address => uint256) public userTier;
    mapping(address => uint256) public userToken;
    
    // Mapping de TokenID para Tier
    mapping(uint256 => uint256) public tokenTier;

    event LicensePurchased(address indexed buyer, uint256 indexed tier, uint256 tokenId, uint256 price);
    event TierPriceUpdated(uint256 indexed tier, uint256 newPrice);

    bool public transfersEnabled;

    constructor(address _usdcTokenAddress) ERC721("OBI Work License", "OBILIC") {
        usdcToken = IERC20(_usdcTokenAddress);
        transfersEnabled = true;
        
        // Configuração Inicial de Preços (Exemplo)
        // Clone #02: $200 USDC
        tierPrices[2] = 200 * 10**6; 
        // Clone #05: $500 USDC
        tierPrices[5] = 500 * 10**6;
    }

    /**
     * @dev Compra uma licença (Clone) pagando em USDC.
     * Requer aprovação prévia do contrato para gastar USDC do usuário.
     */
    function buyLicense(uint256 tierId) external nonReentrant {
        uint256 price = tierPrices[tierId];
        require(price > 0, "Tier invalido ou nao disponivel");
        require(userToken[msg.sender] == 0, "Usuario ja possui uma licenca ativa");

        // Verifica saldo e allowance
        require(usdcToken.balanceOf(msg.sender) >= price, "Saldo USDC insuficiente");
        require(usdcToken.allowance(msg.sender, address(this)) >= price, "Aprovacao USDC insuficiente");

        // Transfere USDC do usuário para este contrato (ou tesouraria)
        // Por segurança, transferimos para o contrato e o owner pode sacar depois, 
        // ou transferimos direto para o owner. Vamos manter no contrato para simplificar saque em batch.
        usdcToken.safeTransferFrom(msg.sender, address(this), price);

        // Minera o NFT
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenTier[newItemId] = tierId;
        _safeMint(msg.sender, newItemId);
        
        // Define metadata baseada no Tier (pode ser IPFS depois)
        string memory uri = _generateTokenURI(tierId);
        _setTokenURI(newItemId, uri);

        // Registra Tier
        userTier[msg.sender] = tierId;

        emit LicensePurchased(msg.sender, tierId, newItemId, price);
    }

    /**
     * @dev Verifica o nível de acesso de um usuário.
     * Retorna o Tier ID (0 se não tiver acesso).
     * Útil para o Backend Python validar.
     */
    function verifyAccess(address user) external view returns (uint256) {
        // Verifica se o usuário ainda é dono do NFT (se for transferível)
        // Se userTier for apenas registro de compra, ok. 
        // Mas se o NFT for transferido, o novo dono deve ter acesso e o antigo não?
        // Implementação Soulbound simplificada: O mapping userTier é a verdade.
        // Se quiser transferibilidade real, teríamos que iterar ou usar Enumerable.
        // Para este MVP, vamos confiar no userTier gravado na compra.
        uint256 tokenId = userToken[user];
        if (tokenId == 0) {
            return 0;
        }
        if (!_exists(tokenId)) {
            return 0;
        }
        if (ownerOf(tokenId) != user) {
            return 0;
        }
        return tokenTier[tokenId];
    }

    /**
     * @dev Saque de fundos pelo dono.
     */
    function withdrawUSDC() external onlyOwner {
        uint256 balance = usdcToken.balanceOf(address(this));
        require(balance > 0, "Sem fundos para sacar");
        usdcToken.safeTransfer(owner(), balance);
    }

    function setTierPrice(uint256 tierId, uint256 price) external onlyOwner {
        tierPrices[tierId] = price;
        emit TierPriceUpdated(tierId, price);
    }

    function setTransfersEnabled(bool enabled) external onlyOwner {
        transfersEnabled = enabled;
    }

    // Helper interno para URI (Mock)
    function _generateTokenURI(uint256 tierId) internal pure returns (string memory) {
        if (tierId == 2) return "ipfs://QmClone02Metadata";
        if (tierId == 5) return "ipfs://QmClone05Metadata";
        return "ipfs://QmDefault";
    }
    
    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        if (from != address(0) && to != address(0)) {
            require(transfersEnabled, "Transferencias desativadas");
            require(userToken[to] == 0, "Destino ja possui licenca");
        }
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function _afterTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        if (from != address(0)) {
            userToken[from] = 0;
            userTier[from] = 0;
        }
        if (to != address(0)) {
            userToken[to] = tokenId;
            userTier[to] = tokenTier[tokenId];
        }
        super._afterTokenTransfer(from, to, tokenId, batchSize);
    }
}
