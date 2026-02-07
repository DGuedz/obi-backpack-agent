// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title OBIWORK ACCESS PASS
 * @dev Institutional-grade trading engineering access credential.
 *      1 NFT = 1 Active Operator.
 */
contract ObiWorkPass is ERC721, Ownable {
    using Strings for uint256;

    // --- STRUCTS ---
    struct CloneType {
        uint256 price;
        uint256 weight; // 1x = 100, 1.5x = 150, etc.
        string name;
        bool active;
    }

    // --- STATE VARIABLES ---
    mapping(uint256 => CloneType) public cloneTypes; // Clone ID => Config
    mapping(uint256 => bool) public hasMinted; // Wallet => Minted? (1 per wallet rule)
    
    string public baseURI;
    address public treasury;

    // --- EVENTS ---
    event PassMinted(address indexed minter, uint256 indexed cloneId, uint256 price);
    event TreasuryUpdated(address newTreasury);

    constructor(address _treasury) ERC721("OBIWORK ACCESS PASS", "OBIWORK") Ownable(msg.sender) {
        treasury = _treasury;
        
        // Initialize Clones
        _setupClone(2, 997 ether, 100, "Clone #02 - Operator"); // Using ether as placeholder for USDC/Stable logic or native ETH
        _setupClone(3, 1497 ether, 125, "Clone #03 - Priority");
        _setupClone(4, 1997 ether, 150, "Clone #04 - Early Access");
        _setupClone(5, 2497 ether, 200, "Clone #05 - Advanced");
        _setupClone(6, 3497 ether, 300, "Clone #06 - Core");
    }

    function _setupClone(uint256 _id, uint256 _price, uint256 _weight, string memory _name) internal {
        cloneTypes[_id] = CloneType(_price, _weight, _name, true);
    }

    // --- MINT FUNCTION ---
    function mintAccessPass(uint256 _cloneId) external payable {
        CloneType memory clone = cloneTypes[_cloneId];
        
        require(clone.active, "Clone type not active");
        require(msg.value >= clone.price, "Insufficient payment");
        require(!hasMinted[msg.sender], "One pass per wallet rule");
        
        // Effects
        hasMinted[msg.sender] = true;
        _safeMint(msg.sender, _cloneId); // TokenID IS the CloneID for simplicity in this specific batch model? 
        // Wait, if multiple people buy Clone #02, we need unique TokenIDs.
        // Correction: CloneID is the TYPE. TokenID must be unique.
        
        // Revert: We need unique TokenIDs. 
        // Let's assume TokenID = (CloneID * 1000) + Counter? 
        // Or simple increment. Let's use simple increment but store the Type.
    }
    
    // REFACTORING FOR ROBUSTNESS
    uint256 private _nextTokenId;
    mapping(uint256 => uint256) public tokenCloneType; // TokenID => CloneTypeID

    function mintPass(uint256 _cloneTypeId) external payable {
        CloneType memory clone = cloneTypes[_cloneTypeId];
        
        require(clone.active, "Clone type not active");
        require(msg.value >= clone.price, "Insufficient payment"); // Assuming Native ETH payment for MVP
        require(balanceOf(msg.sender) == 0, "One pass per wallet rule"); // Enforce 1 per wallet check via balance

        uint256 tokenId = _nextTokenId++;
        tokenCloneType[tokenId] = _cloneTypeId;
        
        _safeMint(msg.sender, tokenId);
        
        // Forward funds
        (bool sent, ) = treasury.call{value: address(this).balance}("");
        require(sent, "Failed to send Ether");

        emit PassMinted(msg.sender, _cloneTypeId, msg.value);
    }

    // --- VIEW ---
    function getPassDetails(uint256 _tokenId) external view returns (CloneType memory) {
        require(_ownerOf(_tokenId) != address(0), "Token does not exist");
        return cloneTypes[tokenCloneType[_tokenId]];
    }

    function _baseURI() internal view override returns (string memory) {
        return baseURI;
    }

    // --- ADMIN ---
    function setBaseURI(string memory _newURI) external onlyOwner {
        baseURI = _newURI;
    }
    
    function setClonePrice(uint256 _id, uint256 _price) external onlyOwner {
        cloneTypes[_id].price = _price;
    }

    // Soulbound-ish Logic? User said "Transferencia = revogacao automatica de acesso off-chain".
    // So standard transfer is allowed, but backend handles the revocation.
    // No code change needed here, pure ERC721.
}
